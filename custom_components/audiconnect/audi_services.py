from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timedelta, UTC
from typing import Any

from aiohttp import ClientResponseError

from .audi_api import AudiAPI
from .audi_auth import AudiAuthError, AudiAuthMixin, AudiTokenRefreshError
from .api_probe import run_read_only_probes
from .capability_jobs import (
    BASE_SELECTIVE_JOBS,
    capability_snapshot,
    observed_readable_jobs,
    select_jobs,
)
from .audi_models import TripDataResponse, VehicleDataResponse, VehiclesResponse
from .audi_payloads import (
    JSON_CONTENT_VARIANTS,
    build_climatisation_settings_update,
    build_climatisation_timer,
    build_climatisation_timers_update,
    build_climatisation_start_body,
    build_profile_change,
    build_profile_update,
)
from .const import DEFAULT_API_LEVEL
from .util import get_attr

__all__ = [
    "AudiAuthError",
    "AudiService",
    "AudiTokenRefreshError",
    "build_climatisation_settings_update",
    "build_climatisation_start_body",
    "build_profile_change",
    "build_profile_update",
]

MAX_RESPONSE_ATTEMPTS = 10
REQUEST_STATUS_SLEEP = 10

# The home-region lookup can return a ha-5a.prd.<region>.vwg.vwautocloud.net base
# URI. That host does not present a usable certificate chain, so every call routed
# there dies with CERTIFICATE_VERIFY_FAILED. Anything containing this is discarded
# in favour of the static default.
UNUSABLE_HOME_REGION_HOST = "vwautocloud"

# Charging start/stop confirmation. Kept short because each poll spends one
# call from the metered daily allowance and blocks the service call.
CHARGING_CONFIRM_ATTEMPTS = 3
CHARGING_CONFIRM_SLEEP = 5

# Climatisation needs a longer window than charging. Measured on a live vehicle
# 2026-09-13: a start the car never acted on sat at in_progress through +10s and
# +20s and only reached "timeout" at about +60s, so the 15s charging budget would
# expire before the failure was visible and report it as merely unconfirmed.
CLIMATISATION_CONFIRM_ATTEMPTS = 8
CLIMATISATION_CONFIRM_SLEEP = 10


SUCCEEDED = "succeeded"
FAILED = "failed"
REQUEST_SUCCESSFUL = "request_successful"
REQUEST_FAILED = "request_failed"

_LOGGER = logging.getLogger(__name__)


def _utc_offset_of(stamp: Any) -> timedelta | None:
    """The UTC offset of a timestamp the car reported.

    ``json_loads`` already turns ISO strings into ``datetime`` objects, so the
    value arrives as either; neither may be guessed when it is naive.
    """
    try:
        if isinstance(stamp, datetime):
            return stamp.utcoffset()
        return datetime.fromisoformat(stamp).utcoffset()
    except (TypeError, ValueError):
        return None


class AudiService(AudiAuthMixin):
    def __init__(
        self, api: AudiAPI, country: str, spin: str | None, api_level: int
    ) -> None:
        self._api = api
        self._country = country
        self._language: str | None = None
        self._type = "Audi"
        self._spin = spin
        self._homeRegion: dict[str, str] = {}
        self._homeRegionSetter = {}
        self.mbbOAuthBaseURL = None
        self.mbboauthToken = None
        self.xclientId = None
        self._tokenEndpoint = ""
        self._authorizationEndpoint = ""
        self._bearer_token_json = None
        self._uses_auth0 = False
        # Scoped to the live session: next polling cycles omit explicitly
        # unsupported CARIAD jobs, without any additional Audi requests.
        self._cariad_capabilities: dict[str, tuple[frozenset[str], frozenset[str]]] = {}
        # Fixed job labels only, never data values. Scoped to this Audi session.
        self._cariad_observed_jobs: dict[str, frozenset[str]] = {}
        self._client_id = ""
        self._authorizationServerBaseURLLive = ""
        self._api_level = api_level

        if self._api_level is None:
            self._api_level = DEFAULT_API_LEVEL

        if self._country is None:
            self._country = "DE"

    async def refresh_vehicle_data(self, vin: str):
        request_id = await self.request_current_vehicle_data(vin.upper())
        await self.check_bff_request_succeeded(vin, request_id)

    async def request_current_vehicle_data(self, vin: str):
        self._api.use_token(self._bearer_token_json)
        data = await self._api.post(
            self._get_cariad_url_for_vin(vin, "vehiclewakeup"),
            data=None,
            use_json=False,
        )

        request_id = data.get("data", {}).get("requestID")
        if request_id is None:
            raise Exception("Vehicle wakeup response did not contain requestID")

        return request_id

    async def get_preheater(self, vin: str):
        self._api.use_token(self.vwToken)
        return await self._api.get(
            f"{await self._get_home_region(vin.upper())}/fs-car/bs/rs/v1/{self._type}/{self._country}/vehicles/{vin.upper()}/status"
        )

    async def probe_known_read_only_paths(
        self, vin: str, *, extended: bool = False
    ) -> dict[str, Any]:
        """Use current CARIAD credentials for opt-in diagnostic GET probes.

        Does not create/refresh an auth session or send an action.
        """
        token = self._bearer_token_json
        access_token = token.get("access_token") if isinstance(token, dict) else None
        if not isinstance(access_token, str) or not access_token:
            raise ValueError("Active CARIAD access token unavailable")
        self._api.use_token(token)
        return await run_read_only_probes(
            self._api,
            access_token,
            lambda suffix: self._get_cariad_url_for_vin(vin, suffix),
            extended=extended,
        )

    async def get_stored_vehicle_data(self, vin: str):
        """Poll CARIAD with explicit aliases and previously observed valid jobs.

        A 207 or a partial payload may contain useful jobs alongside errors.
        Preserve the evidence and mark incomplete reports for conservative
        state merging; do not add retries or extra network calls.
        """
        key = vin.upper()
        known = self._cariad_capabilities.get(key)
        observed = self._cariad_observed_jobs.get(key, frozenset())
        jobs = (
            select_jobs(*known, observed=observed)
            if known is not None
            else select_jobs()
        )
        self._api.use_token(self._bearer_token_json)
        data = await self._api.get(
            self._get_cariad_url_for_vin(
                vin, "selectivestatus?jobs={jobs}", jobs=",".join(jobs)
            )
        )
        snapshot = capability_snapshot(data)
        if snapshot is not None:
            self._cariad_capabilities[key] = snapshot
        learned = observed_readable_jobs(data, jobs)
        if learned:
            self._cariad_observed_jobs[key] = observed | learned
        response = VehicleDataResponse(data)
        # Pruned requests and missing job keys are never complete snapshots.
        # A successful HTTP status (including 207) does not change this.
        response.partial_response = (
            len(jobs) != len(BASE_SELECTIVE_JOBS)
            or not isinstance(data, dict)
            or any(job not in data for job in jobs)
        )
        _LOGGER.debug(
            "Vehicle selective-status received (%d jobs; capabilities %s; "
            "partial=%s; payload redacted)",
            len(jobs),
            "known" if snapshot is not None else "unknown",
            response.partial_response,
        )
        return response

    async def probe_vehicle_endpoint(self, vin: str, path_and_query: str):
        """GET any read-only path below the vehicle's CARIAD URL (discovery).

        Trip data lives beside the vehicle URL, not below it
        (/vehicle/v1/trips/{vin}/...), so "trips/..." selects that root.
        """
        self._api.use_token(self._bearer_token_json)
        if path_and_query.startswith("trips/"):
            url = self._get_cariad_url(
                "/vehicle/v1/trips/{vin}/" + path_and_query[len("trips/") :],
                vin=vin.upper(),
            )
        elif path_and_query.startswith("bs/"):
            url = self._bs_url(vin, path_and_query)
        elif path_and_query.startswith("bff/"):
            # Any read-only path of the BFF itself, VIN filled in where {vin} is.
            url = self._get_cariad_url(
                "/" + path_and_query[len("bff/") :].replace("{vin}", vin.upper())
            )
        else:
            url = self._get_cariad_url_for_vin(vin, path_and_query)
        return await self._api.get(url)

    def _bs_url(self, vin: str, path: str) -> str:
        """URL of a "bs/<service>/<version>/<rest>" route of the myAudi app.

        The app reaches several backend services (climatisation, batterycharge,
        departuretimer, ...) as bs/<service>/<version>/<brand>/<country>/
        vehicles/<vin>/<rest>, beside the vehicle/v1 URL this integration uses.
        The caller gives only service, version and rest; brand, country and VIN
        are filled in here.
        """
        parts = path.split("/", 3)
        if len(parts) != 4 or not all(parts[1:]):
            raise ValueError("bs path must be bs/<service>/<version>/<route>")
        _, service, version, rest = parts
        base = self._get_cariad_url(
            "/bs/{service}/{version}", service=service, version=version
        )
        return f"{base}/audi/{self._country.upper()}/vehicles/{vin.upper()}/{rest}"

    async def get_charger(self, vin: str):
        self._api.use_token(self.vwToken)
        return await self._api.get(
            f"{await self._get_home_region(vin.upper())}/fs-car/bs/batterycharge/v1/{self._type}/{self._country}/vehicles/{vin.upper()}/charger"
        )

    async def get_climater(self, vin: str):
        self._api.use_token(self.vwToken)
        return await self._api.get(
            f"{await self._get_home_region(vin.upper())}/fs-car/bs/climatisation/v1/{self._type}/{self._country}/vehicles/{vin.upper()}/climater"
        )

    async def get_stored_position(self, vin: str):
        self._api.use_token(self._bearer_token_json)
        return await self._api.get(self._get_cariad_url_for_vin(vin, "parkingposition"))

    async def get_operations_list(self, vin: str):
        self._api.use_token(self.vwToken)
        return await self._api.get(
            "https://mal-1a.prd.ece.vwg-connect.com/api/rolesrights/operationlist/v3/vehicles/"
            + vin.upper()
        )

    async def get_timer(self, vin: str):
        self._api.use_token(self.vwToken)
        return await self._api.get(
            f"{await self._get_home_region(vin.upper())}/fs-car/bs/departuretimer/v1/{self._type}/{self._country}/vehicles/{vin.upper()}/timer"
        )

    async def get_vehicles(self):
        self._api.use_token(self.vwToken)
        return await self._api.get(
            f"https://msg.volkswagen.de/fs-car/usermanagement/users/v1/{self._type}/{self._country}/vehicles"
        )

    # The app's own read-only GraphQL questions about a vehicle (myAudi 5.9.0).
    # Fixed texts, never built from input. The per-vehicle ones take the id the
    # vehicle list calls csid.
    GRAPHQL_LIST = (
        "query vehicleList { userVehicles { vin mappingVin csid devicePlatform "
        "mbbConnect userRole { role } vehicle { classification { driveTrain } "
        "fleet } nickname } }"
    )
    GRAPHQL_PROBES = {
        "list": GRAPHQL_LIST,
        "details": (
            "query vehicleDetails($vehicleCoreId: String!) { userVehicle("
            "vehicleCoreId: $vehicleCoreId) { vehicle { core { modelYear "
            "modelCoding } media { shortName longName } classification { "
            "driveTrain } fleet } devicePlatform mbbConnect vin mappingVin "
            "nickname } }"
        ),
        "render_pictures": (
            "query renderPictures($vehicleCoreId: String!) { vehicle("
            "vehicleCoreId: $vehicleCoreId) { renderPictures { mediaType url } } }"
        ),
        "configuration": (
            "query configuration($vehicleCoreId: String!) { vehicle("
            "vehicleCoreId: $vehicleCoreId) { techSpecs { key name value unit "
            "groupId groupName } equipments { code name categoryName standard } "
            "media { interiorColor exteriorColor } } }"
        ),
    }

    async def _graphql(self, query: str, variables: dict | None = None):
        headers = {
            "Accept": "application/json",
            "Accept-Charset": "utf-8",
            "X-App-Name": "myAudi",
            "X-App-Version": AudiAPI.HDR_XAPP_VERSION,
            "Accept-Language": f"{self._language}-{self._country.upper()}",
            "X-User-Country": self._country.upper(),
            "User-Agent": AudiAPI.HDR_USER_AGENT,
            "Authorization": "Bearer " + self.audiToken["access_token"],
            "Content-Type": "application/json; charset=utf-8",
        }
        payload: dict = {"query": query}
        if variables:
            payload["variables"] = variables
        _, text = await self._api.request(
            "POST",
            "https://app-api.my.aoa.audi.com/vgql/v1/graphql"
            if self._country.upper() == "US"
            else "https://app-api.live-my.audi.com/vgql/v1/graphql",
            json.dumps(payload),
            headers=headers,
            allow_redirects=False,
            rsp_wtxt=True,
        )
        return json.loads(text)

    async def probe_graphql(self, preset: str, vin: str | None = None):
        """Run one of the app's fixed read-only GraphQL questions.

        "list" is the vehicle list. The others are asked about one vehicle, whose
        id (csid) is read from that list first. The whole answer comes back,
        errors included: the point is to see why the model name is missing,
        which the normal vehicle list throws away.
        """
        if preset not in self.GRAPHQL_PROBES:
            raise ValueError(f"Unknown GraphQL probe {preset!r}")
        if preset == "list":
            return await self._graphql(self.GRAPHQL_LIST)
        listing = await self._graphql(self.GRAPHQL_LIST)
        vehicles = (listing.get("data") or {}).get("userVehicles") or []
        wanted = str(vin).lower()
        match = next(
            (
                v
                for v in vehicles
                if isinstance(v, dict) and str(v.get("vin", "")).lower() == wanted
            ),
            None,
        )
        core_id = match.get("csid") if match else None
        if not core_id:
            return {
                "error": "The vehicle list gave no csid for this vehicle",
                "list": listing,
            }
        return await self._graphql(
            self.GRAPHQL_PROBES[preset], {"vehicleCoreId": str(core_id)}
        )

    async def get_vehicle_information(self):
        headers = {
            "Accept": "application/json",
            "Accept-Charset": "utf-8",
            "X-App-Name": "myAudi",
            "X-App-Version": AudiAPI.HDR_XAPP_VERSION,
            "Accept-Language": f"{self._language}-{self._country.upper()}",
            "X-User-Country": self._country.upper(),
            "User-Agent": AudiAPI.HDR_USER_AGENT,
            "Authorization": "Bearer " + self.audiToken["access_token"],
            "Content-Type": "application/json; charset=utf-8",
        }
        req_data = {
            "query": "query vehicleList {\n userVehicles {\n vin\n mappingVin\n vehicle { core { modelYear\n }\n media { shortName\n longName }\n }\n csid\n commissionNumber\n type\n devicePlatform\n mbbConnect\n userRole {\n role\n }\n vehicle {\n classification {\n driveTrain\n }\n }\n nickname\n }\n}"
        }
        req_rsp, rep_rsptxt = await self._api.request(
            "POST",
            "https://app-api.my.aoa.audi.com/vgql/v1/graphql"
            if self._country.upper() == "US"
            else "https://app-api.live-my.audi.com/vgql/v1/graphql",  # Starting in 2023, US users need to point at the aoa (Audi of America) URL.
            json.dumps(req_data),
            headers=headers,
            allow_redirects=False,
            rsp_wtxt=True,
        )
        vins = json.loads(rep_rsptxt)
        if "data" not in vins or vins["data"] is None:
            if "errors" in vins:
                raise Exception(f"API returned errors: {vins['errors']}")
            raise Exception("No data in API response")

        if vins["data"].get("userVehicles") is None:
            if "errors" in vins:
                raise Exception(f"API returned errors: {vins['errors']}")
            raise Exception(
                "No vehicle data in API response - possible authentication issue"
            )

        # GraphQL may return usable vehicle data with enrichment errors.
        if "errors" in vins:
            _LOGGER.debug(
                "Vehicle discovery returned non-fatal enrichment errors: %s",
                [error.get("message") for error in vins["errors"]],
            )

        response = VehiclesResponse()
        response.parse(vins["data"])
        return response

    async def get_vehicle_data(self, vin: str):
        self._api.use_token(self.vwToken)
        return await self._api.get(
            f"{await self._get_home_region(vin.upper())}/fs-car/vehicleMgmt/vehicledata/v2/{self._type}/{self._country}/vehicles/{vin.upper()}/"
        )

    async def get_capabilities(self, vin: str) -> dict[str, Any]:
        """What the car can do, with each capability's parameters.

        The capability list inside selectivestatus carries no parameters. This
        separate call does: limits such as the lowest charge target the car
        accepts. Returns the capabilities keyed by id.
        """
        self._api.use_token(self._bearer_token_json)
        response = await self._api.get(
            self._get_cariad_url_for_vin(vin, "capabilities")
        )
        found = response.get("capabilities") if isinstance(response, dict) else None
        return found if isinstance(found, dict) else {}

    async def get_last_trip(self, vin: str, kind: str) -> dict[str, Any]:
        """The car's last trip of one kind ("shortterm" or "longterm").

        Served from /vehicle/v1/trips/{vin}/{kind}/last, with the figures one
        level down under "data". A 404 means the car has no such trips.
        """
        if kind not in ("shortterm", "longterm"):
            raise ValueError(f"Unknown trip kind: {kind}")
        self._api.use_token(self._bearer_token_json)
        response = await self._api.get(
            self._get_cariad_url(
                "/vehicle/v1/trips/{vin}/{kind}/last", vin=vin.upper(), kind=kind
            )
        )
        data = response.get("data") if isinstance(response, dict) else None
        return data if isinstance(data, dict) else {}

    async def get_tripdata(self, vin: str, kind: str):
        self._api.use_token(self.vwToken)

        # read tripdata
        headers = {
            "Accept": "application/json",
            "Accept-Charset": "utf-8",
            "X-App-Name": "myAudi",
            "X-App-Version": AudiAPI.HDR_XAPP_VERSION,
            "X-Client-ID": self.xclientId,
            "User-Agent": AudiAPI.HDR_USER_AGENT,
            "Authorization": "Bearer " + self.vwToken["access_token"],
        }
        td_reqdata = {
            "type": "list",
            "from": "1970-01-01T00:00:00Z",
            # "from":(datetime.now(timezone.utc) - timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "to": (datetime.now(UTC) + timedelta(minutes=90)).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            ),
        }
        data = await self._api.request(
            "GET",
            f"{await self._get_home_region_setter(vin.upper())}/api/bs/tripstatistics/v1/vehicles/{vin.upper()}/tripdata/{kind}",
            None,
            params=td_reqdata,
            headers=headers,
        )
        td_sorted = sorted(
            data["tripDataList"]["tripData"],
            key=lambda k: k["overallMileage"],
            reverse=True,
        )
        # _LOGGER.debug("get_tripdata: td_sorted: %s", td_sorted)
        td_current = td_sorted[0]
        # FIX, TR/2023-03-25: Assign just in case td_sorted contains only one item
        td_reset_trip = td_sorted[0]

        for trip in td_sorted:
            if (td_current["startMileage"] - trip["startMileage"]) > 2:
                td_reset_trip = trip
                break
            else:
                td_current["tripID"] = trip["tripID"]
                td_current["startMileage"] = trip["startMileage"]
        _LOGGER.debug("TRIP DATA: td_current: %s", td_current)
        _LOGGER.debug("TRIP DATA: td_reset_trip: %s", td_reset_trip)

        return TripDataResponse(td_current), TripDataResponse(td_reset_trip)

    async def _fill_home_region(self, vin: str):
        # the home-region endpoint returns
        # https://ha-5a.prd.eu.vwg.vwautocloud.net which is no valid endpoint
        # (at least not in DE region). set it statically.
        if self._country.upper() != "US" and self._api_level == 1:
            self._homeRegion[vin] = "https://mal-3a.prd.eu.dp.vwg-connect.com"
            self._homeRegionSetter[vin] = "https://mal-3a.prd.eu.dp.vwg-connect.com"
            return
        self._homeRegion[vin] = "https://msg.volkswagen.de"
        self._homeRegionSetter[vin] = "https://mal-1a.prd.ece.vwg-connect.com"

        try:
            self._api.use_token(self.vwToken)
            res = await self._api.get(
                f"https://mal-1a.prd.ece.vwg-connect.com/api/cs/vds/v1/vehicles/{vin}/homeRegion"
            )
            if (
                res is not None
                and res.get("homeRegion") is not None
                and res["homeRegion"].get("baseUri") is not None
                and res["homeRegion"]["baseUri"].get("content") is not None
            ):
                uri = res["homeRegion"]["baseUri"]["content"]
                if UNUSABLE_HOME_REGION_HOST in uri:
                    # The endpoint hands back ha-5a.prd.<region>.vwg.vwautocloud.net,
                    # which does not serve a usable certificate chain and fails with
                    # CERTIFICATE_VERIFY_FAILED. The static default above already
                    # works, so keep it. The guard at the top of this method covers
                    # the same host for non-US accounts on API level 1; this covers
                    # every other combination, which is how US accounts (#829) and
                    # API level 0 accounts in Europe still reached it.
                    _LOGGER.debug(
                        "HOME REGION: ignoring unusable base URI %s, keeping %s",
                        uri,
                        self._homeRegion[vin],
                    )
                elif uri != "https://mal-1a.prd.ece.vwg-connect.com/api":
                    self._homeRegionSetter[vin] = uri.split("/api")[0]
                    self._homeRegion[vin] = self._homeRegionSetter[vin].replace(
                        "mal-", "fal-"
                    )
        except Exception:
            pass

    async def _get_home_region(self, vin: str):
        if self._homeRegion.get(vin) is not None:
            return self._homeRegion[vin]

        await self._fill_home_region(vin)

        return self._homeRegion[vin]

    async def _get_home_region_setter(self, vin: str):
        if self._homeRegionSetter.get(vin) is not None:
            return self._homeRegionSetter[vin]

        await self._fill_home_region(vin)

        return self._homeRegionSetter[vin]

    async def _get_security_token(self, vin: str, action: str):
        # Challenge
        headers = {
            "User-Agent": "okhttp/3.7.0",
            "X-App-Version": "3.14.0",
            "X-App-Name": "myAudi",
            "Accept": "application/json",
            "Authorization": "Bearer " + self.vwToken.get("access_token"),
        }

        body = await self._api.request(
            "GET",
            f"{await self._get_home_region_setter(vin.upper())}/api/rolesrights/authorization/v2/vehicles/"
            + vin.upper()
            + "/services/"
            + action
            + "/security-pin-auth-requested",
            headers=headers,
            data=None,
        )
        secToken = body["securityPinAuthInfo"]["securityToken"]
        challenge = body["securityPinAuthInfo"]["securityPinTransmission"]["challenge"]

        # Response
        securityPinHash = self._generate_security_pin_hash(challenge)
        data = {
            "securityPinAuthentication": {
                "securityPin": {
                    "challenge": challenge,
                    "securityPinHash": securityPinHash,
                },
                "securityToken": secToken,
            }
        }

        headers = {
            "User-Agent": "okhttp/3.7.0",
            "Content-Type": "application/json",
            "X-App-Version": "3.14.0",
            "X-App-Name": "myAudi",
            "Accept": "application/json",
            "Authorization": "Bearer " + self.vwToken.get("access_token"),
        }

        body = await self._api.request(
            "POST",
            f"{await self._get_home_region_setter(vin.upper())}/api/rolesrights/authorization/v2/security-pin-auth-completed",
            headers=headers,
            data=json.dumps(data),
        )
        return body["securityToken"]

    def _get_vehicle_action_header(
        self, content_type: str, security_token: str | None, host: str | None = None
    ) -> dict[str, str]:
        if not host:
            host = (
                "mal-3a.prd.eu.dp.vwg-connect.com"
                if self._country in {"DE", "US"}
                else "msg.volkswagen.de"
            )

        headers = {
            "User-Agent": AudiAPI.HDR_USER_AGENT,
            "Host": host,
            "X-App-Version": AudiAPI.HDR_XAPP_VERSION,
            "X-App-Name": "myAudi",
            "Authorization": "Bearer " + self.vwToken.get("access_token"),
            "Accept-charset": "UTF-8",
            "Content-Type": content_type,
            "Accept": "application/json, application/vnd.vwg.mbb.ChargerAction_v1_0_0+xml,application/vnd.volkswagenag.com-error-v1+xml,application/vnd.vwg.mbb.genericError_v1_0_2+xml, application/vnd.vwg.mbb.RemoteStandheizung_v2_0_0+xml, application/vnd.vwg.mbb.genericError_v1_0_2+xml,application/vnd.vwg.mbb.RemoteLockUnlock_v1_0_0+xml,*/*",
        }

        if security_token:
            headers["x-securityToken"] = security_token

        return headers

    def _build_url(
        self, base_url: str, path_and_query: str, **path_and_query_kwargs: Any
    ) -> str:
        action_path = path_and_query.format(**path_and_query_kwargs)

        return base_url.rstrip("/") + "/" + action_path.lstrip("/")

    def _get_cariad_url(self, path_and_query: str, **path_and_query_kwargs: Any) -> str:
        base_url = "https://{region}.bff.cariad.digital".format(
            region="emea" if self._country.upper() != "US" else "na"
        )

        return self._build_url(base_url, path_and_query, **path_and_query_kwargs)

    def _get_cariad_url_for_vin(
        self, vin: str, path_and_query: str, **path_and_query_kwargs: Any
    ) -> str:
        base_url = self._get_cariad_url("/vehicle/v1/vehicles/{vin}", vin=vin.upper())

        return self._build_url(base_url, path_and_query, **path_and_query_kwargs)

    async def set_vehicle_lock(self, vin: str, lock: bool):
        """Use the CARIAD access API with Auth0, legacy RLU only with legacy auth.

        Audi's 2026 Auth0 sessions no longer authorize the old
        rolesrights/rlu_v1 PIN challenge used by the pre-2026 integration.
        Do not retry a failed access command on another backend: unlocking is a
        security-sensitive mutation and blind retries can have side effects.
        """
        if self._uses_auth0:
            return await self._set_vehicle_lock_cariad(vin, lock)
        return await self._set_vehicle_lock_legacy(vin, lock)

    async def _set_vehicle_lock_cariad(self, vin: str, lock: bool) -> None:
        """Modern /access/lock and /access/unlock route (Audi connector reference).

        The Audi BFF expects the S-PIN as a JSON field, unlike legacy RLU
        challenge/response. Never log the payload, VIN, or authorization data.
        HTTP 200 means *accepted by gateway*, not proven physical door state.
        """
        if not self._spin:
            raise ValueError("An Audi S-PIN is required for remote door control")
        if not self._bearer_token_json or not self._bearer_token_json.get(
            "access_token"
        ):
            raise AudiAuthError("Audi Auth0 access token is unavailable")
        action = "lock" if lock else "unlock"
        headers = {
            "Authorization": "Bearer " + self._bearer_token_json["access_token"],
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        self._api.use_token(self._bearer_token_json)
        try:
            reply = await self._api.request(
                "POST",
                self._get_cariad_url_for_vin(vin, f"access/{action}"),
                headers=headers,
                data=json.dumps({"spin": self._spin}),
            )
        except ClientResponseError as err:
            # CARIAD may acknowledge a mutation with 204 No Content.
            # This is only a transport acknowledgement, not a door-state check.
            if err.status != 204:
                raise
            reply = None
        request_id = (
            get_attr(reply, "data.requestID") if isinstance(reply, dict) else None
        )
        if request_id:
            await self._confirm_vehicle_request(
                vin, action, request_id, noun="Door lock"
            )
        else:
            _LOGGER.debug(
                "Door %s request acknowledged without a confirmation id; "
                "verify lock status after the next vehicle refresh",
                action,
            )

    async def _set_vehicle_lock_legacy(self, vin: str, lock: bool) -> None:
        security_token = await self._get_security_token(
            vin, "rlu_v1/operations/" + ("LOCK" if lock else "UNLOCK")
        )
        # deprecated data removed on 24Mar2025
        # data = '<?xml version="1.0" encoding= "UTF-8" ?><rluAction xmlns="http://audi.de/connect/rlu"><action>{action}</action></rluAction>'.format(
        #     action="lock" if lock else "unlock"
        # )
        data = None

        headers = self._get_vehicle_action_header(
            "application/vnd.vwg.mbb.RemoteLockUnlock_v1_0_0+xml", security_token
        )
        res = await self._api.request(
            "POST",
            "{homeRegionSetter}/api/bs/rlu/v1/vehicles/{vin}/{action}".format(
                homeRegionSetter=await self._get_home_region_setter(vin.upper()),
                vin=vin.upper(),
                action="lock" if lock else "unlock",
            ),
            headers=headers,
            data=data,
        )

        checkUrl = "{homeRegionSetter}/api/bs/rlu/v1/vehicles/{vin}/requests/{requestId}/status".format(
            homeRegionSetter=await self._get_home_region_setter(vin.upper()),
            vin=vin.upper(),
            requestId=res["rluActionResponse"]["requestId"],
        )

        await self.check_request_succeeded(
            checkUrl,
            "lock vehicle" if lock else "unlock vehicle",
            REQUEST_SUCCESSFUL,
            REQUEST_FAILED,
            "requestStatusResponse.status",
        )

    async def set_battery_charger(self, vin: str, start: bool, timer: bool):
        """Start or stop charging.

        start=True, timer=True  -> select timer mode, so the car charges on its
                                   own schedule rather than immediately.
        start=True, timer=False -> start charging now.
        start=False             -> stop charging now.

        Until 2.3.1 all three only PUT charging/mode, which sets a *mode
        preference* and neither starts nor stops a charge, and the stop case
        raised outright (upstream #725). charging/start and charging/stop are the
        routes current firmware exposes for the action itself, cross-checked
        against two independent BFF clients.
        """
        if start and timer:
            await self.set_preferred_charge_mode(vin, "timer")
            return

        await self._send_charging_command(vin, "start" if start else "stop")

    async def set_preferred_charge_mode(self, vin: str, mode: str) -> None:
        """Set which mode the car charges in. A preference, not an action: it does
        not start or stop a charge in progress."""
        headers = {"Authorization": "Bearer " + self._bearer_token_json["access_token"]}

        await self._api.request(
            "PUT",
            self._get_cariad_url_for_vin(vin, "charging/mode"),
            headers=headers,
            data=json.dumps({"preferredChargeMode": mode}),
        )

    async def _post_charging_command(
        self, vin: str, suffix: str, body: dict[str, Any]
    ) -> Any:
        """POST one BFF charging command.

        Returns the parsed body, or None when the car answers 204. The shared
        request helper raises ClientResponseError for every status outside
        200/202/207, 204 included, so a no-content success arrives here as an
        exception and has to be turned back into one.
        """
        headers = {"Authorization": "Bearer " + self._bearer_token_json["access_token"]}
        try:
            return await self._api.request(
                "POST",
                self._get_cariad_url_for_vin(vin, suffix),
                headers=headers,
                data=json.dumps(body),
            )
        except ClientResponseError as err:
            if err.status == 204:
                return None
            raise

    async def _send_charging_command(self, vin: str, action: str) -> None:
        """Actually start or stop a charge.

        Separate charging/start and charging/stop are what current firmware
        exposes; the combined charging/start-stop route is kept as a 404 fallback
        for older cars. Both shapes are used by CarConnectivity-connector-volkswagen
        and vwgroup-connect-ha against the same CARIAD BFF.
        """
        try:
            res = await self._post_charging_command(vin, f"charging/{action}", {})
        except ClientResponseError as err:
            if err.status != 404:
                raise
            _LOGGER.debug(
                "charging/%s not provisioned for %s, trying the combined route",
                action,
                vin,
            )
            res = await self._post_charging_command(
                vin, "charging/start-stop", {"action": action}
            )

        request_id = get_attr(res, "data.requestID") if isinstance(res, dict) else None
        if request_id is None:
            _LOGGER.debug(
                "Charging %s accepted for %s with no request id to confirm against",
                action,
                vin,
            )
            return

        await self._confirm_charging_command(vin, action, request_id)

    async def _confirm_charging_command(
        self, vin: str, action: str, request_id: str
    ) -> None:
        """Confirm a charging command. Thin wrapper kept for its call sites."""
        await self._confirm_vehicle_request(
            vin,
            action,
            request_id,
            noun="Charging",
            attempts=CHARGING_CONFIRM_ATTEMPTS,
            sleep=CHARGING_CONFIRM_SLEEP,
        )

    async def _confirm_vehicle_request(
        self,
        vin: str,
        action: str,
        request_id: str,
        noun: str = "Charging",
        attempts: int = CHARGING_CONFIRM_ATTEMPTS,
        sleep: int = CHARGING_CONFIRM_SLEEP,
    ) -> None:
        """Poll pendingrequests until the car acts on the command.

        Deliberately shorter than check_bff_request_succeeded (10 polls, 10s
        apart): every poll is an API call against a metered daily allowance, and
        this runs inside a service call the user is waiting on. Running out of
        attempts is reported as unconfirmed rather than failed, so a command that
        did work is never announced as broken. An explicit rejection still
        raises.
        """
        headers = {
            "Accept": "application/json",
            "Authorization": "Bearer " + self._bearer_token_json["access_token"],
            "User-Agent": AudiAPI.HDR_USER_AGENT,
            "Content-Type": "application/json; charset=utf-8",
        }

        for _ in range(attempts):
            await asyncio.sleep(sleep)
            try:
                res = await self._api.request(
                    "GET",
                    self._get_cariad_url_for_vin(vin, "pendingrequests"),
                    headers=headers,
                    data=None,
                )
            except ClientResponseError as err:
                if err.status != 204:
                    raise
                res = None

            entries = get_attr(res, "data") or []
            if not isinstance(entries, list):
                entries = []
            for pending_request in entries:
                if not isinstance(pending_request, dict):
                    continue
                if pending_request.get("id") != request_id:
                    continue
                status = pending_request.get("status")
                if status == "in_progress":
                    break
                if status == "successful":
                    _LOGGER.debug("%s %s confirmed by CARIAD", noun, action)
                    return
                raise RuntimeError(
                    f"{noun} {action} rejected by the vehicle "
                    f"(confirmation state {str(status)[:32]})"
                )

        _LOGGER.warning(
            "%s %s was accepted but not confirmed within %ds. "
            "The command may still be carried out; verify vehicle state.",
            noun,
            action,
            attempts * sleep,
        )

        # checkUrl = "{homeRegion}/fs-car/bs/batterycharge/v1/{type}/{country}/vehicles/{vin}/charger/actions/{actionid}".format(
        #     homeRegion=await self._get_home_region(vin.upper()),
        #     type=self._type,
        #     country=self._country,
        #     vin=vin.upper(),
        #     actionid=res["action"]["actionId"],
        # )

        # await self.check_request_succeeded(
        #     checkUrl,
        #     "start charger" if start else "stop charger",
        #     SUCCEEDED,
        #     FAILED,
        #     "action.actionState",
        # )

    async def get_charging_profiles_raw(self, vin: str) -> dict:
        """Fetch just the chargingProfiles job, unparsed.

        The write is a read-modify-write and the BFF replaces the whole profile,
        so we need the profile exactly as the car reports it, not the scrubbed
        summary the sensor keeps.
        """
        self._api.use_token(self._bearer_token_json)
        return await self._api.get(
            self._get_cariad_url_for_vin(
                vin, "selectivestatus?jobs={jobs}", jobs="chargingProfiles"
            )
        )

    async def set_location_charge_target(
        self, vin: str, profile_id: int | None, target_soc: int
    ) -> None:
        """Set a location charging profile's target SoC.

        This is the value that actually governs where a charge stops at a
        location; the global charging/settings target does not (upstream #722).

        Endpoint, verb and body shape are from the myAudi app 4.30:
            PUT charging/profiles   body {"profile": {<whole profile>}}
        The PUT replaces the entire profile, so this reads the current one,
        changes only targetSOC_pct, and sends everything else back unchanged.
        Never invent or drop a field.

        profile_id None targets the profile the car is currently parked in.
        """
        await self._put_profile_change(
            vin, profile_id, f"target {target_soc}%", targetSOC_pct=target_soc
        )

    async def set_profile_charging_current(
        self, vin: str, profile_id: int | None, current: str
    ) -> None:
        """Set a location profile's charging current to "max" or "reduced"."""
        await self._put_profile_change(
            vin, profile_id, f"current {current}", maxChargingCurrent=current
        )

    async def _put_profile_change(
        self, vin: str, profile_id: int | None, label: str, **changes: Any
    ) -> None:
        raw = await self.get_charging_profiles_raw(vin)
        value = get_attr(raw, "chargingProfiles.chargingProfilesStatus.value")
        profile_id, put_body = build_profile_change(value, profile_id, **changes)

        headers = {
            "Authorization": "Bearer " + self._bearer_token_json["access_token"],
            "Content-Type": "application/json",
        }
        try:
            res = await self._api.request(
                "PUT",
                self._get_cariad_url_for_vin(vin, "charging/profiles"),
                headers=headers,
                data=json.dumps(put_body),
            )
        except ClientResponseError as err:
            if err.status == 204:
                res = None
            else:
                raise

        request_id = get_attr(res, "data.requestID") if isinstance(res, dict) else None
        if request_id is None:
            _LOGGER.debug(
                "Profile change for %s accepted with no request id to confirm",
                vin,
            )
            return
        await self._confirm_charging_command(
            vin, f"profile {profile_id} {label}", request_id
        )

    async def flash_lights(
        self, vin: str, latitude: float, longitude: float, duration_s: int = 10
    ) -> None:
        """Flash the vehicle's lights.

        Endpoint and body shape are from WeConnect-python, which drives the same
        Cariad BFF:

            POST {bff}/vehicle/v1/vehicles/{vin}/honkandflash
            {"duration_s": 10, "mode": "flash",
             "userPosition": {"latitude": .., "longitude": ..}}

        The position is required, which is why a GET against this path returns
        404 rather than 405: there is no GET route at all.

        The mode is hard-coded. The same endpoint sounds the horn when given
        "honkandflash", and there is deliberately no parameter through which a
        caller could reach that: a control that can wake a street by passing the
        wrong string is not worth the flexibility.
        """
        headers = {"Authorization": "Bearer " + self._bearer_token_json["access_token"]}
        data = {
            "duration_s": duration_s,
            "mode": "flash",
            "userPosition": {"latitude": latitude, "longitude": longitude},
        }
        await self._api.request(
            "POST",
            self._get_cariad_url_for_vin(vin, "honkandflash"),
            headers=headers,
            data=json.dumps(data),
        )

    async def honk_horn(
        self, vin: str, latitude: float, longitude: float, duration_s: int = 10
    ) -> None:
        """Sound the horn and flash the lights.

        The same endpoint as flash_lights, with the mode the myAudi app sends
        for the horn. It is a separate method with a literal mode, not an
        option of flash_lights, so the silent flash can never turn into a horn
        by passing a different string.
        """
        headers = {"Authorization": "Bearer " + self._bearer_token_json["access_token"]}
        data = {
            "duration_s": duration_s,
            "mode": "honkandflash",
            "userPosition": {"latitude": latitude, "longitude": longitude},
        }
        await self._api.request(
            "POST",
            self._get_cariad_url_for_vin(vin, "honkandflash"),
            headers=headers,
            data=json.dumps(data),
        )

    async def set_climatisation_settings(
        self, vin: str, *, variant: str = "app_dto", method: str = "PUT", **changes: Any
    ) -> None:
        """Change climatisation settings without starting climatisation.

        PUT {bff}/vehicle/v1/vehicles/{vin}/climatisation/settings

        Endpoint and field names are from WeConnect-python, which drives the
        same Cariad BFF. An earlier GET against this path returned 404, which
        was read as the endpoint not existing; it means there is no GET route.
        The honk-and-flash work later demonstrated the same 404-on-GET on this
        API for a path that is perfectly real for its own verb.
        """
        # A single field needs nothing from the car, so it skips the read.
        current = (
            {}
            if variant == "single_field"
            else await self.get_climatisation_settings_raw(vin)
        )
        body = build_climatisation_settings_update(current, variant=variant, **changes)

        headers = {"Authorization": "Bearer " + self._bearer_token_json["access_token"]}
        if variant in JSON_CONTENT_VARIANTS:
            headers["Content-Type"] = "application/json"
        if method not in ("PUT", "POST"):
            raise ValueError(f"Unknown write method: {method!r}")
        await self._api.request(
            method,
            self._get_cariad_url_for_vin(vin, "climatisation/settings"),
            headers=headers,
            data=json.dumps(body),
        )

    def _departure_url(self, vin: str, suffix: str) -> str:
        """The departure timers live under vehicle/v2, not vehicle/v1/vehicles."""
        return self._get_cariad_url(
            "/vehicle/v2/departure/{vin}/" + suffix, vin=vin.upper()
        )

    async def _car_utc_offset_minutes(self, vin: str) -> int:
        """The car's clock offset, from the time it reports for itself."""
        self._api.use_token(self._bearer_token_json)
        raw = await self._api.get(
            self._get_cariad_url_for_vin(
                vin, "selectivestatus?jobs={jobs}", jobs="departureTimers"
            )
        )
        stamp = get_attr(
            raw, "departureTimers.climatisationTimersStatus.value.timeInCar"
        )
        offset = _utc_offset_of(stamp)
        if offset is None:
            raise ValueError("The car did not report its local time; refusing to guess")
        return int(offset.total_seconds() // 60)

    async def create_climatisation_timer(
        self,
        vin: str,
        time_local: str,
        days: list[str],
        *,
        repeat: bool = True,
        enabled: bool = True,
    ) -> Any:
        """Create a climatisation timer.

        POST {bff}/vehicle/v2/departure/{vin}/climatisation/timers, body shaped
        like the myAudi app's (see build_climatisation_timer).
        """
        offset = await self._car_utc_offset_minutes(vin)
        body = build_climatisation_timer(
            time_local,
            days,
            repeat=repeat,
            enabled=enabled,
            utc_offset_minutes=offset,
        )
        headers = {
            "Authorization": "Bearer " + self._bearer_token_json["access_token"],
            "Content-Type": "application/json",
        }
        return await self._api.request(
            "POST",
            self._departure_url(vin, "climatisation/timers"),
            headers=headers,
            data=json.dumps(body),
        )

    async def set_climatisation_timer_enabled(
        self, vin: str, timer_id: int, enabled: bool
    ) -> Any:
        """Switch one climatisation timer on or off.

        PUT {bff}/vehicle/v2/departure/{vin}/climatisation/timers replaces the
        whole list, so the current timers are read, converted to the app's shape
        and all sent back with only this one changed.
        """
        self._api.use_token(self._bearer_token_json)
        raw = await self._api.get(
            self._get_cariad_url_for_vin(
                vin, "selectivestatus?jobs={jobs}", jobs="departureTimers"
            )
        )
        status = get_attr(raw, "departureTimers.climatisationTimersStatus.value") or {}
        stamp = status.get("timeInCar") if isinstance(status, dict) else None
        offset_delta = _utc_offset_of(stamp)
        if offset_delta is None:
            raise ValueError("The car did not report its local time; refusing to guess")
        body = build_climatisation_timers_update(
            status.get("timers"),
            timer_id,
            enabled,
            int(offset_delta.total_seconds() // 60),
        )
        headers = {
            "Authorization": "Bearer " + self._bearer_token_json["access_token"],
            "Content-Type": "application/json",
        }
        return await self._api.request(
            "PUT",
            self._departure_url(vin, "climatisation/timers"),
            headers=headers,
            data=json.dumps(body),
        )

    async def delete_climatisation_timer(self, vin: str, timer_id: int) -> Any:
        """DELETE {bff}/vehicle/v2/departure/{vin}/climatisation/timers/{id}."""
        headers = {"Authorization": "Bearer " + self._bearer_token_json["access_token"]}
        return await self._api.request(
            "DELETE",
            self._departure_url(vin, f"climatisation/timers/{int(timer_id)}"),
            headers=headers,
            data=None,
        )

    async def get_charging_settings_raw(self, vin: str) -> dict[str, Any]:
        """Read actual car charging settings before an Auth0 settings mutation.

        CARIAD charging/settings can replace several settings. Never overwrite
        unknown car preferences with a partial request or guessed defaults.
        """
        self._api.use_token(self._bearer_token_json)
        response = await self._api.get(
            self._get_cariad_url_for_vin(
                vin, "selectivestatus?jobs={jobs}", jobs="charging"
            )
        )
        settings = (response or {}).get("charging", {}).get("chargingSettings", {})
        value = settings.get("value") if isinstance(settings, dict) else None
        if not isinstance(value, dict) or not value:
            raise ValueError(
                "Audi has not returned charging settings; refusing blind update"
            )
        return value

    async def _put_charging_settings(self, vin: str, changes: dict[str, Any]) -> None:
        """Change charging settings without dropping the ones not being changed.

        A CARIAD PUT may replace the complete object, so the current settings are
        read first and sent back with only the requested fields altered. Unknown
        settings stop the write instead of being silently dropped or replayed.
        """
        headers = {"Authorization": "Bearer " + self._bearer_token_json["access_token"]}

        data = dict(changes)
        if self._uses_auth0:
            current = await self.get_charging_settings_raw(vin)
            writable = frozenset(
                (
                    "maxChargeCurrentAC_A",
                    "maxChargeCurrentAC",
                    "autoUnlockPlugWhenCharged",
                    "autoUnlockPlugWhenChargedAC",
                    "targetSOC_pct",
                )
            )
            metadata = frozenset({"carCapturedTimestamp"})
            if set(current) - writable - metadata:
                raise ValueError(
                    "Audi reported unrecognized charging settings; refusing "
                    "a potentially destructive full-replacement PUT"
                )
            # "invalid" is the car's word for "no reading", not a value to send
            # back.
            data = {
                key: current[key]
                for key in writable
                if key in current and current[key] not in (None, "invalid")
            }
            data.update(changes)

        await self._api.request(
            "PUT",
            self._get_cariad_url_for_vin(vin, "charging/settings"),
            headers=headers,
            data=json.dumps(data),
        )

    async def set_target_state_of_charge(self, vin: str, target_soc: int):
        """Set the target state of charge (battery percentage)."""
        if not (20 <= target_soc <= 100):
            raise ValueError(
                "Target state of charge must be between 20 and 100 percent"
            )
        await self._put_charging_settings(vin, {"targetSOC_pct": target_soc})

    async def set_plug_auto_unlock(self, vin: str, enabled: bool):
        """Let the car release the charging plug once charging has finished.

        The values are "on" and "off", the two the open-source clients (WeConnect)
        list as settable. Only the Auth0 path can write it: the legacy endpoints
        are gone, and a blind write there would replace the rest of the
        settings.
        """
        if not self._uses_auth0:
            raise ValueError("Plug auto-unlock needs an Auth0 session")
        await self._put_charging_settings(
            vin, {"autoUnlockPlugWhenChargedAC": "on" if enabled else "off"}
        )

    async def get_climatisation_settings_raw(self, vin: str) -> dict:
        """Fetch just the climatisation job, unparsed.

        The start endpoint replaces the whole settings object, so it needs the
        fields exactly as the car reports them rather than a parsed subset.
        """
        self._api.use_token(self._bearer_token_json)
        data = await self._api.get(
            self._get_cariad_url_for_vin(
                vin, "selectivestatus?jobs={jobs}", jobs="climatisation"
            )
        )
        value = (
            (data or {})
            .get("climatisation", {})
            .get("climatisationSettings", {})
            .get("value")
        )
        return value if isinstance(value, dict) else {}

    def _climate_api_level(self) -> int:
        """Auth0 tokens cannot authorize legacy fs-car climatisation actions.

        Route Auth0 sessions to the existing CARIAD command implementation even
        if the entry still holds the historical API Level 0 configuration.
        Do not change other endpoints or the saved user preference.
        """
        if self._uses_auth0:
            return 1
        return self._api_level

    async def set_climatisation(self, vin: str, start: bool):
        api_level = self._climate_api_level()
        country = self._country

        if start:
            raise NotImplementedError(
                "The 'Start Climatisation (Legacy)' service is deprecated and no longer functional. "
                "Please use the 'Start Climate Control' service instead."
            )
            # data = '{"action":{"type": "startClimatisation","settings": {"targetTemperature": 2940,"climatisationWithoutHVpower": true,"heaterSource": "electric","climaterElementSettings": {"isClimatisationAtUnlock": false, "isMirrorHeatingEnabled": true,}}}}'
        else:
            if api_level == 0:
                data = '{"action":{"type": "stopClimatisation"}}'

                if country == "US":
                    headers = self._get_vehicle_action_header("application/json", None)
                    res = await self._api.request(
                        "POST",
                        f"https://mal-3a.prd.eu.dp.vwg-connect.com/api/bs/climatisation/v1/vehicles/{vin.upper()}/climater/actions",
                        headers=headers,
                        data=data,
                    )
                    checkUrl = "https://mal-3a.prd.eu.dp.vwg-connect.com/api/bs/climatisation/v1/vehicles/{vin}/climater/actions/{actionid}".format(
                        vin=vin.upper(),
                        actionid=res["action"]["actionId"],
                    )

                else:
                    headers = self._get_vehicle_action_header(
                        "application/json", None, "msg.volkswagen.de"
                    )
                    res = await self._api.request(
                        "POST",
                        f"{await self._get_home_region(vin.upper())}/fs-car/bs/climatisation/v1/{self._type}/{self._country}/vehicles/{vin.upper()}/climater/actions",
                        headers=headers,
                        data=data,
                    )

                    checkUrl = "{homeRegion}/fs-car/bs/climatisation/v1/{type}/{country}/vehicles/{vin}/climater/actions/{actionid}".format(
                        homeRegion=await self._get_home_region(vin.upper()),
                        type=self._type,
                        country=self._country,
                        vin=vin.upper(),
                        actionid=res["action"]["actionId"],
                    )

                await self.check_request_succeeded(
                    checkUrl,
                    "stop climatisation",
                    SUCCEEDED,
                    FAILED,
                    "action.actionState",
                )

            elif api_level == 1:
                data = None
                headers = {
                    "Authorization": "Bearer " + self._bearer_token_json["access_token"]
                }
                try:
                    res = await self._api.request(
                        "POST",
                        self._get_cariad_url_for_vin(vin, "climatisation/stop"),
                        headers=headers,
                        data=data,
                    )
                except ClientResponseError as err:
                    if err.status != 204:
                        raise
                    res = None
                request_id = get_attr(res, "data.requestID")
                if request_id:
                    await self._confirm_vehicle_request(
                        vin,
                        "stop",
                        request_id,
                        noun="Climatisation",
                        attempts=CLIMATISATION_CONFIRM_ATTEMPTS,
                        sleep=CLIMATISATION_CONFIRM_SLEEP,
                    )

                # checkUrl = "https://emea.bff.cariad.digital/vehicle/v1/vehicles/{vin}/pendingrequests".format(
                #     vin=vin.upper(),
                #     actionid=res["action"]["actionId"],
                # )

                # await self.check_request_succeeded(
                #     checkUrl,
                #     "startClimatisation",
                #     SUCCEEDED,
                #     FAILED,
                #     "action.actionState",
                # )

    async def start_climate_control(
        self,
        vin: str,
        temp_f: int | None = None,
        temp_c: int | None = None,
        glass_heating: bool | None = None,
        seat_fl: bool | None = None,
        seat_fr: bool | None = None,
        seat_rl: bool | None = None,
        seat_rr: bool | None = None,
        climatisation_at_unlock: bool | None = None,
        climatisation_mode: str | None = None,
    ):
        api_level = self._climate_api_level()
        country = self._country
        target_temperature = None

        _LOGGER.debug(
            "Attempting to start climate control with API Level %s and country %s.",
            api_level,
            country,
        )

        if api_level == 0:
            target_temperature = None
            if temp_f is not None:
                target_temperature = int(((temp_f - 32) * (5 / 9)) * 10 + 2731)
            elif temp_c is not None:
                target_temperature = int(temp_c * 10 + 2731)

            # Default Temp
            target_temperature = target_temperature or 2941

            # Construct Zone Settings
            zone_settings = [
                {"value": {"isEnabled": bool(seat_fl), "position": "frontLeft"}},
                {"value": {"isEnabled": bool(seat_fr), "position": "frontRight"}},
                {"value": {"isEnabled": bool(seat_rl), "position": "rearLeft"}},
                {"value": {"isEnabled": bool(seat_rr), "position": "rearRight"}},
            ]

            data = {
                "action": {
                    "type": "startClimatisation",
                    "settings": {
                        "targetTemperature": target_temperature,
                        "climatisationWithoutHVpower": True,
                        "heaterSource": "electric",
                        "climaterElementSettings": {
                            # bool()-wrapped like the zone settings below: this
                            # endpoint expects a JSON boolean here, never null.
                            # The raw (Optional[bool]) parameter serialises as
                            # `null` when the caller supplies only a temperature
                            # (the climate entity's bare turn_on, #849), and the
                            # legacy fs-car backend rejects that payload with
                            # HTTP 400 before it is queued as a trackable action.
                            "isClimatisationAtUnlock": bool(climatisation_at_unlock),
                            "isMirrorHeatingEnabled": bool(glass_heating),
                            "zoneSettings": {"zoneSetting": zone_settings},
                        },
                    },
                }
            }

            data = json.dumps(data)

            if country == "US":
                headers = self._get_vehicle_action_header("application/json", None)
                res = await self._api.request(
                    "POST",
                    f"https://mal-3a.prd.eu.dp.vwg-connect.com/api/bs/climatisation/v1/vehicles/{vin.upper()}/climater/actions",
                    headers=headers,
                    data=data,
                )

                checkUrl = "https://mal-3a.prd.eu.dp.vwg-connect.com/api/bs/climatisation/v1/vehicles/{vin}/climater/actions/{actionid}".format(
                    vin=vin.upper(),
                    actionid=res["action"]["actionId"],
                )
            else:
                headers = self._get_vehicle_action_header(
                    "application/json", None, "msg.volkswagen.de"
                )
                res = await self._api.request(
                    "POST",
                    f"{await self._get_home_region(vin.upper())}/fs-car/bs/climatisation/v1/{self._type}/{self._country}/vehicles/{vin.upper()}/climater/actions",
                    headers=headers,
                    data=data,
                )

                checkUrl = "{homeRegion}/fs-car/bs/climatisation/v1/{type}/{country}/vehicles/{vin}/climater/actions/{actionid}".format(
                    homeRegion=await self._get_home_region(vin.upper()),
                    type=self._type,
                    country=self._country,
                    vin=vin.upper(),
                    actionid=res["action"]["actionId"],
                )

            await self.check_request_succeeded(
                checkUrl,
                "startClimatisation",
                SUCCEEDED,
                FAILED,
                "action.actionState",
            )

        elif api_level == 1:
            # Some vehicles (for example the Q6 e-tron) reject a settings payload
            # outright, because they have no comfort climatisation profile to apply
            # it to. The vehicle reports the request as failed only after it has
            # synchronised, so the failure shows up in the myAudi app rather than
            # in our HTTP response. When the caller supplied no settings at all,
            # send no body and let the vehicle use the settings stored in the car,
            # which is what the myAudi app does in that case.
            has_settings = any(
                value is not None
                for value in (
                    temp_f,
                    temp_c,
                    climatisation_mode,
                    climatisation_at_unlock,
                    glass_heating,
                    seat_fl,
                    seat_fr,
                    seat_rl,
                    seat_rr,
                )
            )

            data = None
            if has_settings:
                # Read-modify-write: the endpoint replaces the settings object,
                # so anything not sent is cleared. Build from what the car
                # currently holds and change only what the caller asked for.
                stored = await self.get_climatisation_settings_raw(vin)
                if not stored:
                    _LOGGER.debug(
                        "Vehicle reports no climatisation settings; building the start body from defaults."
                    )
                data = json.dumps(
                    build_climatisation_start_body(
                        stored,
                        temp_f=temp_f,
                        temp_c=temp_c,
                        climatisation_mode=climatisation_mode,
                        climatisation_at_unlock=climatisation_at_unlock,
                        glass_heating=glass_heating,
                        seat_fl=seat_fl,
                        seat_fr=seat_fr,
                        seat_rl=seat_rl,
                        seat_rr=seat_rr,
                    )
                )
            else:
                _LOGGER.debug(
                    "No climate settings supplied; starting climatisation with the settings stored in the vehicle."
                )

            headers = {
                "Authorization": "Bearer " + self._bearer_token_json["access_token"]
            }
            try:
                res = await self._api.request(
                    "POST",
                    self._get_cariad_url_for_vin(vin, "climatisation/start"),
                    headers=headers,
                    data=data,
                )
            except ClientResponseError as err:
                # No-content is a valid acknowledgement for certain BFF
                # actions. Never mistake it for a verified vehicle transition.
                if err.status != 204:
                    raise
                res = None

            # The 200 is the gateway accepting the request, not the car acting on
            # it. Measured on a live vehicle 2026-09-13: a start the car ignored
            # returned 200 with a requestID and only reported "timeout" in
            # pendingrequests about a minute later, so without this a command that
            # never ran was announced as success. Same class as #847's rejected
            # switch command.
            request_id = get_attr(res, "data.requestID")
            if request_id is not None:
                await self._confirm_vehicle_request(
                    vin,
                    "start",
                    request_id,
                    noun="Climatisation",
                    attempts=CLIMATISATION_CONFIRM_ATTEMPTS,
                    sleep=CLIMATISATION_CONFIRM_SLEEP,
                )
            else:
                _LOGGER.debug(
                    "Climatisation start accepted for %s with no request id to confirm",
                    vin,
                )

            # checkUrl = "https://emea.bff.cariad.digital/vehicle/v1/vehicles/{vin}/pendingrequests".format(
            #     vin=vin.upper(),
            #     actionid=res["action"]["actionId"],
            # )

            # await self.check_request_succeeded(
            #     checkUrl,
            #     "startClimatisation",
            #     SUCCEEDED,
            #     FAILED,
            #     "action.actionState",
            # )

    async def trigger_vehicle_wakeup(self, vin: str) -> None:
        """Explicit modern CARIAD vehicle wake-up; never called by polling.

        Based on CarConnectivity-connector-audi's wake command. The API can
        acknowledge a request without the car actually waking. Use only on a
        direct user action, respecting Audi's request limits.
        """
        if not self._uses_auth0:
            raise AudiAuthError("Modern CARIAD wake-up requires Auth0")
        headers = {
            "Authorization": "Bearer " + self._bearer_token_json["access_token"],
            "Content-Type": "application/json",
        }
        try:
            await self._api.request(
                "POST",
                self._get_cariad_url_for_vin(vin, "vehiclewakeuptrigger"),
                headers=headers,
                data="{}",
            )
        except ClientResponseError as err:
            if err.status != 204:
                raise

    async def set_window_heating(self, vin: str, start: bool):
        if self._uses_auth0:
            # The legacy fs-car XML endpoint cannot be authorized by Auth0.
            # Do not accidentally reroute proven climate START/STOP here.
            headers = {
                "Authorization": "Bearer " + self._bearer_token_json["access_token"],
                "Content-Type": "application/json",
            }
            suffix = "windowheating/start" if start else "windowheating/stop"
            try:
                await self._api.request(
                    "POST",
                    self._get_cariad_url_for_vin(vin, suffix),
                    headers=headers,
                    data="{}",
                )
            except ClientResponseError as err:
                if err.status != 204:
                    raise
            return
        data = '<?xml version="1.0" encoding= "UTF-8" ?><action><type>{action}</type></action>'.format(
            action="startWindowHeating" if start else "stopWindowHeating"
        )

        headers = self._get_vehicle_action_header(
            "application/vnd.vwg.mbb.ClimaterAction_v1_0_0+xml", None
        )
        res = await self._api.request(
            "POST",
            f"{await self._get_home_region(vin.upper())}/fs-car/bs/climatisation/v1/{self._type}/{self._country}/vehicles/{vin.upper()}/climater/actions",
            headers=headers,
            data=data,
        )

        checkUrl = "{homeRegion}/fs-car/bs/climatisation/v1/{type}/{country}/vehicles/{vin}/climater/actions/{actionid}".format(
            homeRegion=await self._get_home_region(vin.upper()),
            type=self._type,
            country=self._country,
            vin=vin.upper(),
            actionid=res["action"]["actionId"],
        )

        await self.check_request_succeeded(
            checkUrl,
            "start window heating" if start else "stop window heating",
            SUCCEEDED,
            FAILED,
            "action.actionState",
        )

    async def set_pre_heater(
        self, vin: str, activate: bool, duration: int | None = None
    ) -> None:
        if activate:
            if not duration:
                duration = 30
            data = {
                "duration_min": int(duration),
                "spin": self._spin,
            }

            data = json.dumps(data)
        else:
            data = None

        headers = {
            "Accept": "application/json",
            "Accept-charset": "utf-8",
            "Authorization": "Bearer " + self._bearer_token_json["access_token"],
            "User-Agent": AudiAPI.HDR_USER_AGENT,
            "Content-Type": "application/json; charset=utf-8",
            "Accept-encoding": "gzip",
        }
        res = await self._api.request(
            "POST",
            self._get_cariad_url_for_vin(
                vin, "auxiliaryheating/{action}", action="start" if activate else "stop"
            ),
            headers=headers,
            data=data,
        )

        await self.check_bff_request_succeeded(vin, res["data"]["requestID"])

    async def start_engine(self, vin: str) -> None:
        if not self._spin:
            raise Exception("S-PIN is required to start the engine")

        headers = {
            "Accept": "application/json",
            "Accept-charset": "utf-8",
            "Authorization": "Bearer " + self._bearer_token_json["access_token"],
            "User-Agent": AudiAPI.HDR_USER_AGENT,
            "Content-Type": "application/json; charset=utf-8",
            "Accept-encoding": "gzip",
        }

        # Step 1: Obtain userPromptProof
        proof_res = await self._api.request(
            "PUT",
            self._get_cariad_url(
                "/vehicle/v1/engine/{vin}/userpromptproof", vin=vin.upper()
            ),
            headers=headers,
            data=json.dumps({"spin": self._spin}),
        )
        user_prompt_proof = proof_res["userPromptProof"]

        # Step 2: Submit start request
        res = await self._api.request(
            "POST",
            self._get_cariad_url("/vehicle/v1/engine/{vin}/start", vin=vin.upper()),
            headers=headers,
            data=json.dumps(
                {
                    "securedActivationData": user_prompt_proof,
                    "spin": self._spin,
                }
            ),
        )

        await self.check_bff_request_succeeded(vin, res["data"]["requestID"])

    async def stop_engine(self, vin: str) -> None:
        headers = {
            "Accept": "application/json",
            "Accept-charset": "utf-8",
            "Authorization": "Bearer " + self._bearer_token_json["access_token"],
            "User-Agent": AudiAPI.HDR_USER_AGENT,
            "Content-Type": "application/json; charset=utf-8",
            "Accept-encoding": "gzip",
        }

        res = await self._api.request(
            "POST",
            self._get_cariad_url("/vehicle/v1/engine/{vin}/stop", vin=vin.upper()),
            headers=headers,
            data=None,
        )

        await self.check_bff_request_succeeded(vin, res["data"]["requestID"])

    async def check_bff_request_succeeded(self, vin: str, request_id: str):
        headers = {
            "Accept": "application/json",
            "Accept-charset": "utf-8",
            "Authorization": "Bearer " + self._bearer_token_json["access_token"],
            "User-Agent": AudiAPI.HDR_USER_AGENT,
            "Content-Type": "application/json; charset=utf-8",
            "Accept-encoding": "gzip",
        }

        for _ in range(MAX_RESPONSE_ATTEMPTS):
            await asyncio.sleep(REQUEST_STATUS_SLEEP)
            res = await self._api.request(
                "GET",
                "https://{homeRegion}.bff.cariad.digital/vehicle/v1/vehicles/{vin}/pendingrequests".format(
                    homeRegion="na" if self._country.upper() == "US" else "emea",
                    vin=vin.upper(),
                ),
                headers=headers,
                data=None,
            )

            for pending_request in res["data"]:
                if pending_request["id"] == request_id:
                    if pending_request["status"] == "in_progress":
                        break  # continue waiting

                    if pending_request["status"] == "successful":
                        return

                    raise Exception(
                        "Request {} reached unexpected status {}".format(
                            request_id, pending_request["status"]
                        )
                    )

        # A TimeoutError, not a bare Exception: a car that does not answer in time
        # is a normal state (asleep, out of coverage), and callers can tell it from
        # a real failure.
        raise TimeoutError(f"Request {request_id} timed out")

    async def check_request_succeeded(
        self, url: str, action: str, successCode: str, failedCode: str, path: str
    ):
        for _ in range(MAX_RESPONSE_ATTEMPTS):
            await asyncio.sleep(REQUEST_STATUS_SLEEP)

            self._api.use_token(self.vwToken)
            res = await self._api.get(url)

            status = get_attr(res, path)

            if status is None or (failedCode is not None and status == failedCode):
                raise Exception(f"Cannot {action}, return code '{status}'")

            if status == successCode:
                return

        raise Exception(f"Cannot {action}, operation timed out")
