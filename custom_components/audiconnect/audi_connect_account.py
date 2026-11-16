from __future__ import annotations

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from typing import Any

from aiohttp import ClientConnectionError, ClientResponseError, ClientSession

from .audi_api import AudiAPI
from .audi_connect_vehicle import AudiConnectVehicle
from .audi_services import AudiAuthError, AudiService
from .util import log_exception
import builtins

__all__ = ["AudiConnectAccount", "AudiConnectObserver", "AudiConnectVehicle"]

_LOGGER = logging.getLogger(__name__)

MAX_RESPONSE_ATTEMPTS = 10
REQUEST_STATUS_SLEEP = 5

# Ceiling for the exponential backoff between login attempts, so a larger retry
# count can never stretch a single login into an unbounded wait.
MAX_LOGIN_RETRY_DELAY = 60

ACTION_LOCK = "lock"
ACTION_CLIMATISATION = "climatisation"
ACTION_CHARGER = "charger"
ACTION_WINDOW_HEATING = "window_heating"
ACTION_PRE_HEATER = "pre_heater"
ACTION_ENGINE = "engine"

_INACTIVE_PREHEATER_STATES = frozenset({"off", "invalid", "unsupported", "error", ""})


class AudiConnectObserver(ABC):
    @abstractmethod
    async def handle_notification(self, vin: str, action: str) -> None:
        pass


class AudiConnectAccount:
    """Representation of an Audi Connect Account."""

    def __init__(
        self,
        session: ClientSession,
        country: str,
        spin: str | None,
        api_level: int,
        excluded_vins: list[str] | None = None,
        refresh_token: str | None = None,
        username: str | None = None,
        password: str | None = None,
    ) -> None:
        self._api = AudiAPI(session)
        self._audi_service = AudiService(self._api, country, spin, api_level)

        # Either a device-code refresh token (Europe) or username/password
        # (regions where Audi has not enforced Play Integrity attestation).
        self._refresh_token = refresh_token
        self._username = username
        self._password = password
        self._loggedin = False
        self._support_vehicle_refresh = True
        self._logintime: float = 0

        self._connect_retries = 3
        self._connect_delay = 10

        self._update_listeners: list[Any] = []
        self._on_refresh_token_update: Callable[[str], None] | None = None

        self._vehicles: list[AudiConnectVehicle] = []
        self._audi_vehicles: list[Any] = []
        self._excluded_vins = [v.lower() for v in (excluded_vins or [])]

        self._observers: list[AudiConnectObserver] = []

        # Per-vehicle, in-memory diagnostic probe results; no raw response data.
        self._readonly_probe_reports: dict[str, dict[str, Any]] = {}
        self._readonly_probe_attempted: dict[str, float] = {}
        self._readonly_probe_lock = asyncio.Lock()

    async def probe_read_only_api(
        self, vin: str, *, extended: bool = False
    ) -> dict[str, Any]:
        """Explicit, rate-limited diagnostic GET probes; never a vehicle action."""
        vin_key = vin.lower()
        if not self._loggedin:
            raise RuntimeError("Audi connection is not authenticated")
        if not any(vehicle.vin.lower() == vin_key for vehicle in self._vehicles):
            raise ValueError("Vehicle is not present in this Audi account")

        async with self._readonly_probe_lock:
            now = time.monotonic()
            last_attempt = self._readonly_probe_attempted.get(vin_key)
            if last_attempt is not None and now - last_attempt < 900:
                report = self._readonly_probe_reports.get(vin_key)
                expected_mode = "extended" if extended else "core"
                if report is not None and report.get("mode") == expected_mode:
                    return report
                raise RuntimeError(
                    "API diagnostic probe cooldown is active; retry later"
                )
            # Record before dispatch so repeated failed scans cannot hammer Audi.
            self._readonly_probe_attempted[vin_key] = now
            report = await self._audi_service.probe_known_read_only_paths(
                vin, extended=extended
            )
            self._readonly_probe_reports[vin_key] = report
            return report

    def get_read_only_probe_report(self, vin: str) -> dict[str, Any] | None:
        """Return only the sanitized previous report, never start new traffic."""
        return self._readonly_probe_reports.get(vin.lower())

    @property
    def refresh_token(self) -> str | None:
        """Return the current IDK refresh token."""
        return self._refresh_token

    def account_identifier(self) -> str | None:
        """Return a stable identifier for the signed-in account."""
        return self._audi_service.get_id_token_subject()

    def set_refresh_token_listener(self, callback: Callable[[str], None]) -> None:
        """Register a callback invoked with the new refresh token when it rotates."""
        self._on_refresh_token_update = callback

    def _sync_refresh_token(self) -> None:
        new_token = self._audi_service.current_refresh_token()
        if new_token and new_token != self._refresh_token:
            self._refresh_token = new_token
            if self._on_refresh_token_update is not None:
                self._on_refresh_token_update(new_token)

    async def get_auth0_authorization_url(self, code_challenge: str, state: str) -> str:
        """Return the interactive myAudi authorization URL."""
        return await self._audi_service.get_auth0_authorization_url(
            code_challenge, state
        )

    async def login_with_auth0_code(self, code: str, code_verifier: str) -> None:
        """Complete an interactive Auth0 login."""
        self._refresh_token = await self._audi_service.login_with_auth0_code(
            code, code_verifier
        )
        self._loggedin = True
        self._logintime = time.time()

    async def request_device_code(self) -> dict[str, Any]:
        """Start the device authorization grant (used by config/reauth flow)."""
        return await self._audi_service.request_device_code()

    async def poll_device_token(self, device_code: str) -> str:
        """Poll once for device-code approval; capture the session on success."""
        status = await self._audi_service.poll_device_token(device_code)
        if status == "ok":
            self._loggedin = True
            self._logintime = time.time()
            self._sync_refresh_token()
        return status

    @property
    def vehicles(self) -> list[AudiConnectVehicle]:
        """Return the list of discovered vehicles."""
        return self._vehicles

    def add_observer(self, observer: AudiConnectObserver) -> None:
        self._observers.append(observer)

    async def notify(self, vin: str, action: str) -> None:
        for observer in self._observers:
            await observer.handle_notification(vin, action)

    @property
    def uses_password_login(self) -> bool:
        """True when this account authenticates with username/password."""
        return not self._refresh_token and bool(self._username and self._password)

    async def login(self):
        if not self._refresh_token and not self.uses_password_login:
            raise AudiAuthError("No stored authorization; reauthentication is required")
        for i in range(self._connect_retries):
            self._loggedin = await self.try_login(i == self._connect_retries - 1)
            if self._loggedin is True:
                self._logintime = time.time()
                break

            if i < self._connect_retries - 1:
                # Back off between attempts. When the Audi service is having a
                # bad day, hammering it at a fixed interval neither helps us nor
                # them. The last attempt logs the real error, so the ones in
                # between stay at debug and don't fill the log on every poll.
                delay = min(self._connect_delay * 2**i, MAX_LOGIN_RETRY_DELAY)
                _LOGGER.debug(
                    "LOGIN: Login to Audi service failed, retrying in %s seconds",
                    delay,
                )
                await asyncio.sleep(delay)

    async def try_login(self, logError):
        try:
            if self._refresh_token:
                _LOGGER.debug("LOGIN: Refreshing Audi session from stored token...")
                new_refresh_token = await self._audi_service.login_with_refresh_token(
                    self._refresh_token
                )
                if new_refresh_token and new_refresh_token != self._refresh_token:
                    self._refresh_token = new_refresh_token
                    if self._on_refresh_token_update is not None:
                        self._on_refresh_token_update(new_refresh_token)
            else:
                _LOGGER.debug("LOGIN: Signing in to the Audi service with credentials")
                await self._audi_service.login(self._username, self._password)
            _LOGGER.debug("LOGIN: Audi session established")
            return True
        except AudiAuthError:
            # Credentials/token rejected: propagate so Home Assistant starts reauth
            # instead of retrying something that can never work.
            raise
        except Exception as exception:  # noqa: BLE001
            # A rejected token or credentials raised AudiAuthError above, so this
            # is a failure that a new sign-in won't fix (an outage, or a change on
            # Audi's side). Don't point the user at reconfiguring: removing the
            # entry can leave them unable to add it back until the cause is fixed.
            if logError:
                _LOGGER.error(
                    "LOGIN: Failed to establish an Audi session: %s. "
                    "Will keep retrying. If this persists, check the Audi Connect "
                    "issue tracker before removing the integration; re-adding it "
                    "may not be possible while the cause is on Audi's side.",
                    str(exception),
                )
            return False

    async def update(self, vinlist):
        """Update the state of all vehicles."""
        if not self._loggedin:
            await self.login()

        if not self._loggedin:
            return False

        elapsed_sec = time.time() - self._logintime
        if await self._audi_service.refresh_token_if_necessary(elapsed_sec):
            # Store current timestamp when refresh was performed and successful
            self._logintime = time.time()
            self._sync_refresh_token()

        try:
            if len(self._audi_vehicles) > 0:
                for vehicle in self._audi_vehicles:
                    if vehicle.vin and vehicle.vin.lower() in self._excluded_vins:
                        continue
                    await self.add_or_update_vehicle(vehicle, vinlist)

            else:
                vehicles_response = await self._audi_service.get_vehicle_information()
                self._audi_vehicles = vehicles_response.vehicles
                self._vehicles = []
                for vehicle in self._audi_vehicles:
                    if vehicle.vin and vehicle.vin.lower() in self._excluded_vins:
                        _LOGGER.debug("Skipping excluded vehicle VIN: %s", vehicle.vin)
                        continue
                    await self.add_or_update_vehicle(vehicle, vinlist)

            for listener in self._update_listeners:
                listener()

            # TR/2021-12-01: do not set to False as refresh_token is used
            # self._loggedin = False

            return True

        except (OSError, ClientConnectionError):
            # Force a re-login in case of failure/exception
            self._loggedin = False
            _LOGGER.exception("Failed to update Audi Connect vehicle data")
            return False

    async def add_or_update_vehicle(self, vehicle, vinlist):
        if vehicle.vin is not None and (
            vinlist is None or vehicle.vin.lower() in vinlist
        ):
            vupd = [x for x in self._vehicles if x.vin == vehicle.vin.lower()]
            if len(vupd) > 0:
                if await vupd[0].update() is False:
                    self._loggedin = False
            else:
                try:
                    audiVehicle = AudiConnectVehicle(self._audi_service, vehicle)
                    if await audiVehicle.update() is False:
                        self._loggedin = False
                    self._vehicles.append(audiVehicle)
                except Exception as exception:  # noqa: BLE001
                    log_exception(
                        exception,
                        "Unable to add vehicle "
                        f"{'*' * (len(vehicle.vin) - 4) + vehicle.vin[-4:]}",
                    )

    async def probe(self, vin: str, path_and_query: str) -> dict[str, Any]:
        """One read-only GET below the vehicle URL; errors are returned, not raised."""
        if not self._loggedin:
            await self.login()
        if not self._loggedin:
            return {"error": "not logged in"}
        try:
            return {
                "status": "ok",
                "body": await self._audi_service.probe_vehicle_endpoint(
                    vin, path_and_query
                ),
            }
        except ClientResponseError as exception:
            return {"status": exception.status, "error": exception.message}
        except TimeoutError:
            return {"error": "timeout"}

    async def refresh_vehicle_data(self, vin: str):
        redacted_vin = "*" * (len(vin) - 4) + vin[-4:]
        if not self._loggedin:
            await self.login()

        if not self._loggedin:
            return False

        if not self._support_vehicle_refresh:
            _LOGGER.debug(
                "Vehicle refresh support is disabled for VIN: %s. Exiting update process.",
                redacted_vin,
            )
            return "disabled"

        try:
            _LOGGER.debug(
                "Sending command to refresh vehicle data for VIN: %s",
                redacted_vin,
            )

            await self._audi_service.refresh_vehicle_data(vin)

            _LOGGER.debug(
                "Successfully refreshed vehicle data for VIN: %s",
                redacted_vin,
            )

            return True

        except builtins.TimeoutError:
            _LOGGER.debug(
                "TimeoutError encountered while refreshing vehicle data for VIN: %s.",
                redacted_vin,
            )
            return False
        except ClientResponseError as cre:
            if cre.status == 404:
                _LOGGER.debug(
                    "VEHICLE REFRESH: ClientResponseError with status %s for VIN: %s. Vehicle does not support vehicle refresh — disabling.",
                    cre.status,
                    redacted_vin,
                )
                self._support_vehicle_refresh = False
                return "disabled"
            elif cre.status in (403, 502):
                _LOGGER.debug(
                    "VEHICLE REFRESH: Received status %s while refreshing vehicle data for VIN: %s. This is typically transient and may resolve on its own.",
                    cre.status,
                    redacted_vin,
                )
                return False
            elif cre.status != 204:
                _LOGGER.debug(
                    "VEHICLE REFRESH: ClientResponseError with status %s while refreshing vehicle data for VIN: %s. Error: %s",
                    cre.status,
                    redacted_vin,
                    cre,
                )
                return False
            else:
                _LOGGER.debug(
                    "VEHICLE REFRESH: Refresh vehicle data currently not available for VIN: %s. Received 204 status.",
                    redacted_vin,
                )
                return False

        except Exception as e:
            _LOGGER.error(
                "VEHICLE REFRESH: An unexpected error occurred while refreshing vehicle data for VIN: %s. Error: %s",
                redacted_vin,
                e,
            )
            return False

    async def _run_command(
        self,
        vin: str,
        description: str,
        call: Callable[[], Awaitable[Any]],
        *,
        notify_action: str | None = None,
        notify_label: str | None = None,
    ) -> bool:
        """Log in if needed, send one vehicle command and say whether it worked.

        A command that cannot be sent is logged and reported as ``False``; it
        must never take the integration down, whatever the cause. When
        ``notify_action`` is given the cloud refresh is requested afterwards,
        successful or not, and a failure of that refresh is only a warning.
        """
        if not self._loggedin:
            await self.login()
        if not self._loggedin:
            return False

        try:
            _LOGGER.debug("Sending command to %s", description)
            await call()
            _LOGGER.debug("Command succeeded: %s", description)
            return True
        except Exception as exception:
            log_exception(exception, f"Unable to {description}")
            return False
        finally:
            if notify_action is not None:
                try:
                    await self.notify(vin, notify_action)
                except Exception as ex:
                    _LOGGER.warning(
                        "Cloud refresh failed after %s for %s: %s",
                        notify_label or description,
                        vin,
                        ex,
                    )

    async def set_vehicle_lock(self, vin: str, lock: bool, *, refresh: bool = True):
        action = "lock" if lock else "unlock"
        masked_vin = "*" * max(0, len(vin) - 4) + vin[-4:]
        return await self._run_command(
            vin,
            f"{action} vehicle {masked_vin}",
            lambda: self._audi_service.set_vehicle_lock(vin, lock),
            notify_action=ACTION_LOCK if refresh else None,
            notify_label="lock/unlock",
        )

    async def trigger_vehicle_wakeup(self, vin: str) -> bool:
        """User-initiated wake request, not background polling or confirmation."""
        if not self._loggedin:
            await self.login()
        if not self._loggedin:
            return False
        try:
            await self._audi_service.trigger_vehicle_wakeup(vin)
            return True
        except Exception:
            _LOGGER.warning(
                "Audi wake-up request failed (no VIN or authentication details logged)"
            )
            return False

    async def set_location_charge_target(self, vin: str, profile_id, target_soc: int):
        """Set a location charging profile's target SoC (the governing value)."""
        return await self._run_command(
            vin,
            f"set location charge target to {target_soc}% "
            f"(profile {profile_id}) for vehicle {vin}",
            lambda: self._audi_service.set_location_charge_target(
                vin, profile_id, target_soc
            ),
        )

    async def set_profile_charging_current(self, vin: str, profile_id, current: str):
        """Set a location profile's charging current (max or reduced)."""
        return await self._run_command(
            vin,
            f"set profile charging current to {current} for vehicle {vin}",
            lambda: self._audi_service.set_profile_charging_current(
                vin, profile_id, current
            ),
        )

    async def set_charge_mode(self, vin: str, mode: str):
        """Set the preferred charge mode (manual or timer)."""
        return await self._run_command(
            vin,
            f"set charge mode to {mode} for vehicle {vin}",
            lambda: self._audi_service.set_preferred_charge_mode(vin, mode),
        )

    async def set_climatisation_setting(
        self,
        vin: str,
        field: str,
        value,
        variant: str = "app_dto",
        method: str = "PUT",
    ) -> bool:
        """Change one climatisation setting, leaving the others as they are."""
        return await self._run_command(
            vin,
            f"set {field}={value} for vehicle {vin} ({variant} body, {method})",
            lambda: self._audi_service.set_climatisation_settings(
                vin.lower(), variant=variant, method=method, **{field: value}
            ),
            notify_action=ACTION_CLIMATISATION,
            notify_label="a climatisation setting",
        )

    async def flash_lights(self, vin: str, duration_s: int = 10) -> bool:
        """Flash the vehicle's lights. Never sounds the horn."""
        if not self._loggedin:
            await self.login()
        if not self._loggedin:
            return False

        vehicle = next((v for v in self.vehicles if v.vin.lower() == vin.lower()), None)
        position = getattr(vehicle, "position", None) if vehicle else None
        latitude = (position or {}).get("latitude")
        longitude = (position or {}).get("longitude")
        if latitude is None or longitude is None:
            # The API requires it, so failing here is clearer than a 400 from
            # the far end.
            _LOGGER.warning(
                "Cannot flash lights for %s: the car has not reported a position",
                vin,
            )
            return False

        return await self._run_command(
            vin,
            f"flash lights of vehicle {vin}",
            lambda: self._audi_service.flash_lights(
                vin, latitude, longitude, duration_s
            ),
        )

    async def honk_horn(self, vin: str, duration_s: int = 10) -> bool:
        """Sound the horn and flash the lights, at the car's reported position."""
        if not self._loggedin:
            await self.login()
        if not self._loggedin:
            return False

        vehicle = next((v for v in self.vehicles if v.vin.lower() == vin.lower()), None)
        position = getattr(vehicle, "position", None) if vehicle else None
        latitude = (position or {}).get("latitude")
        longitude = (position or {}).get("longitude")
        if latitude is None or longitude is None:
            _LOGGER.warning(
                "Cannot honk for %s: the car has not reported a position", vin
            )
            return False

        return await self._run_command(
            vin,
            f"honk the horn of vehicle {vin}",
            lambda: self._audi_service.honk_horn(vin, latitude, longitude, duration_s),
        )

    async def set_target_state_of_charge(self, vin: str, target_soc: int):
        """Set the target state of charge for the vehicle battery."""
        return await self._run_command(
            vin,
            f"set target state of charge to {target_soc}% for vehicle {vin}",
            lambda: self._audi_service.set_target_state_of_charge(vin, target_soc),
        )

    async def set_plug_auto_unlock(self, vin: str, enabled: bool):
        """Let the car release the charging plug when charging is done."""
        state = "on" if enabled else "off"
        return await self._run_command(
            vin,
            f"switch plug auto-unlock {state} for vehicle {vin}",
            lambda: self._audi_service.set_plug_auto_unlock(vin, enabled),
        )

    async def set_vehicle_climatisation(self, vin: str, activate: bool):
        action = "start" if activate else "stop"
        return await self._run_command(
            vin,
            f"{action} climatisation of vehicle {vin}",
            lambda: self._audi_service.set_climatisation(vin, activate),
            notify_action=ACTION_CLIMATISATION,
            notify_label="climatisation",
        )

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
        return await self._run_command(
            vin,
            f"start climate control of vehicle {vin} (Temp(F): {temp_f}, "
            f"Temp(C): {temp_c}, Glass Heating: {glass_heating}, "
            f"Seat FL: {seat_fl}, Seat FR: {seat_fr}, Seat RL: {seat_rl}, "
            f"Seat RR: {seat_rr}, Climatisation at Unlock: "
            f"{climatisation_at_unlock}, Climatisation Mode: {climatisation_mode})",
            lambda: self._audi_service.start_climate_control(
                vin,
                temp_f,
                temp_c,
                glass_heating,
                seat_fl,
                seat_fr,
                seat_rl,
                seat_rr,
                climatisation_at_unlock,
                climatisation_mode,
            ),
            notify_action=ACTION_CLIMATISATION,
            notify_label="climate control",
        )

    async def set_battery_charger(self, vin: str, activate: bool, timer: bool):
        action = "start" if activate else "stop"
        return await self._run_command(
            vin,
            f"{action}{' timed' if timer else ''} charger of vehicle {vin}",
            lambda: self._audi_service.set_battery_charger(vin, activate, timer),
            notify_action=ACTION_CHARGER,
            notify_label="charger action",
        )

    async def set_vehicle_window_heating(self, vin: str, activate: bool):
        action = "start" if activate else "stop"
        return await self._run_command(
            vin,
            f"{action} window heating of vehicle {vin}",
            lambda: self._audi_service.set_window_heating(vin, activate),
            notify_action=ACTION_WINDOW_HEATING,
            notify_label="window heating",
        )

    async def set_vehicle_pre_heater(self, vin: str, activate: bool, **kwargs):
        action = "start" if activate else "stop"
        return await self._run_command(
            vin,
            f"{action} pre-heater of vehicle {vin}",
            lambda: self._audi_service.set_pre_heater(vin, activate, **kwargs),
            notify_action=ACTION_PRE_HEATER,
            notify_label="pre-heater",
        )

    async def start_engine(self, vin: str):
        return await self._run_command(
            vin,
            f"start engine of vehicle {vin}",
            lambda: self._audi_service.start_engine(vin),
            notify_action=ACTION_ENGINE,
            notify_label="engine start",
        )

    async def stop_engine(self, vin: str):
        return await self._run_command(
            vin,
            f"stop engine of vehicle {vin}",
            lambda: self._audi_service.stop_engine(vin),
            notify_action=ACTION_ENGINE,
            notify_label="engine stop",
        )
