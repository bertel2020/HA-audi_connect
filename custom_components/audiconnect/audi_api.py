from __future__ import annotations

import asyncio
import json
import logging
import re
from collections import deque
from contextlib import suppress
from datetime import UTC, datetime
from typing import Any

from aiohttp import ClientResponseError, ClientSession
from aiohttp.hdrs import METH_GET, METH_POST, METH_PUT

from .diagnostic_events import build_http_event

# ===========================================
# VERBOSE DEBUG TOGGLE
# Set to True to log EVERYTHING (full headers, full body, raw JSON, etc.)
# Set to False for normal operation (minimal debug output)
# WARNING: when True this also logs access tokens and Authorization headers.
# Never enable it on a system whose logs you share.
DEBUG_VERBOSE = False
# ===========================================

TIMEOUT = 30
_LOGGER = logging.getLogger(__name__)
_WRITE_METHODS = frozenset({METH_POST, METH_PUT})
_ERROR_BODY_CHARS = 300
_VIN_PATTERN = re.compile(r"[A-HJ-NPR-Z0-9]{17}")
# Request-body keys that carry a secret or a position; matched lower-cased.
_SECRET_BODY_KEYS = frozenset(
    {
        "spin",
        "securitypin",
        "securitypinhash",
        "securitytoken",
        "securedactivationdata",
        "userpromptproof",
        "challenge",
        "token",
        "password",
        "userposition",
        "accesstoken",
        "refreshtoken",
    }
)
_SECRET_TEXT = re.compile(
    r"""(["']?(?:{})["']?\s*[:=]\s*)(?:"[^"]*"|'[^']*'|[^\s,&}}]+)""".format(
        "|".join(sorted(_SECRET_BODY_KEYS))
    ),
    re.IGNORECASE,
)


def _redact_secrets(value: Any) -> Any:
    """Return ``value`` with PINs, tokens and positions replaced by a marker."""
    if isinstance(value, dict):
        return {
            k: "<redacted>"
            if str(k).lower().replace("_", "") in _SECRET_BODY_KEYS
            else _redact_secrets(v)
            for k, v in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [_redact_secrets(v) for v in value]
    if isinstance(value, (bytes, bytearray)):
        value = value.decode("utf-8", "replace")
    if isinstance(value, str):
        stripped = value.lstrip()
        if stripped[:1] in "{[":
            try:
                return _redact_secrets(json.loads(value))
            except ValueError:
                pass
        return _SECRET_TEXT.sub(r"\1<redacted>", value)
    return value


class AudiAPI:
    HDR_XAPP_VERSION = "4.31.0"
    HDR_USER_AGENT = "Android/4.31.0 (Build 800341641.root project 'myaudi_android'.ext.buildTime) Android/13"

    def __init__(self, session: ClientSession) -> None:
        self.__token: dict[str, Any] | None = None
        self.__xclientid: str | None = None
        self._session = session
        self.vcf_remaining_calls: int | None = None
        self.vcf_remaining_calls_last_observed: datetime | None = None
        self.diagnostic_events = deque(maxlen=40)

    def use_token(self, token: dict[str, Any] | None) -> None:
        self.__token = token
        if DEBUG_VERBOSE:
            _LOGGER.debug("[use_token] Token set: %s", token)

    def set_xclient_id(self, xclientid: str | None) -> None:
        self.__xclientid = xclientid
        if DEBUG_VERBOSE:
            _LOGGER.debug("[set_xclient_id] X-Client-ID set: %s", xclientid)

    async def _log_rejected_write(
        self, method: str, url: str, response: Any, sent: Any = None
    ) -> None:
        """Say why Audi refused a write.

        The status line alone ("502 Bad Gateway") cannot tell a rejected body
        from a sleeping car. The reply body usually can, and the body we sent
        says what was asked. Settings are logged, headers never are: PINs, tokens and
        positions are redacted, the VIN is masked and the length capped.
        """
        try:
            text = await response.text()
        except Exception:  # noqa: BLE001 - diagnostics must never mask the error
            return
        route = re.sub(r"/vehicles/[A-Za-z0-9]+", "/vehicles/<vin>", url.split("?")[0])
        reply = re.sub(r"[A-HJ-NPR-Z0-9]{17}", "<vin>", text.strip())[
            :_ERROR_BODY_CHARS
        ]
        _LOGGER.warning(
            "Audi rejected %s %s with %s %s: %s (sent: %s)",
            method.upper(),
            route,
            response.status,
            response.reason,
            reply or "(empty reply)",
            _VIN_PATTERN.sub("<vin>", str(_redact_secrets(sent)))[:_ERROR_BODY_CHARS],
        )

    async def request(
        self,
        method: str,
        url: str,
        data: Any,
        headers: dict[str, str] | None = None,
        raw_reply: bool = False,
        raw_contents: bool = False,
        rsp_wtxt: bool = False,
        **kwargs: Any,
    ) -> Any:
        if DEBUG_VERBOSE:
            _LOGGER.debug("[REQUEST INITIATED]")
            _LOGGER.debug("Method: %s", method)
            _LOGGER.debug("URL: %s", url)
            _LOGGER.debug("Data: %s", data)
            _LOGGER.debug("Headers: %s", headers)
            _LOGGER.debug("Kwargs: %s", kwargs)

        try:
            async with asyncio.timeout(TIMEOUT):
                async with self._session.request(
                    method, url, headers=headers, data=data, **kwargs
                ) as response:
                    # Record status and route only; never retain URL, VIN, body or headers.
                    event = build_http_event(method, url, response.status)
                    if event is not None:
                        self.diagnostic_events.append(event)
                    if DEBUG_VERBOSE:
                        _LOGGER.debug("[RESPONSE RECEIVED]")
                        _LOGGER.debug("Status: %s", response.status)
                        _LOGGER.debug("Reason: %s", response.reason)
                        _LOGGER.debug("Headers: %s", dict(response.headers))

                    vcf_remaining = response.headers.get("Vcf-Remaining-Calls")
                    if vcf_remaining is not None:
                        try:
                            remaining = int(vcf_remaining)
                        except ValueError:
                            remaining = None
                        if remaining is not None:
                            self.vcf_remaining_calls = remaining
                            self.vcf_remaining_calls_last_observed = datetime.now(UTC)
                            if remaining < 10:
                                _LOGGER.warning(
                                    "[VCF-RATE-LIMIT] Remaining calls: %d — warning: VCF call limit nearly exhausted",
                                    remaining,
                                )
                            else:
                                _LOGGER.debug(
                                    "[VCF-RATE-LIMIT] Remaining calls: %d",
                                    remaining,
                                )

                    if raw_reply:
                        if DEBUG_VERBOSE:
                            _LOGGER.debug("Returning raw reply object.")
                        return response

                    if rsp_wtxt:
                        txt = await response.text()
                        if DEBUG_VERBOSE:
                            _LOGGER.debug("Response text (full): %s", txt)
                        else:
                            _LOGGER.debug(
                                "Returning response text; length=%d", len(txt)
                            )
                        return response, txt

                    elif raw_contents:
                        contents = await response.read()
                        if DEBUG_VERBOSE:
                            _LOGGER.debug("Raw contents (bytes): %s", contents)
                        else:
                            _LOGGER.debug(
                                "Returning raw contents; length=%d", len(contents)
                            )
                        return contents

                    elif response.status in (200, 202, 207):
                        raw_body = await response.text()
                        if DEBUG_VERBOSE:
                            _LOGGER.debug(
                                "Raw JSON text (before parsing): %s", raw_body
                            )
                        # Some CARIAD mutation endpoints acknowledge with
                        # HTTP 200/202 and an empty body (not JSON). Accept the
                        # transport response without inventing vehicle success.
                        if not raw_body.strip():
                            return None
                        json_data = json_loads(raw_body)
                        if DEBUG_VERBOSE:
                            _LOGGER.debug("Parsed JSON data (full): %s", json_data)
                        else:
                            _LOGGER.debug(
                                "Returning parsed JSON response (payload redacted)"
                            )
                        return json_data

                    else:
                        # this should be refactored:
                        # 204 is a valid response for some requests (e.g. update_vehicle_position)
                        # and should not raise an error.
                        # request should return a tuple indicating the response itself and the
                        # http-status
                        if response.status != 204:
                            _LOGGER.debug(
                                "Non-success response: status=%s, reason=%s — will be handled by caller",
                                response.status,
                                response.reason,
                            )
                            if method.upper() in _WRITE_METHODS:
                                await self._log_rejected_write(
                                    method, url, response, data
                                )
                            if DEBUG_VERBOSE:
                                _LOGGER.debug(
                                    "Response url: %s, body: %s",
                                    url,
                                    await response.text(),
                                )
                        raise ClientResponseError(
                            response.request_info,
                            response.history,
                            status=response.status,
                            message=response.reason,
                        )

        except TimeoutError:
            if DEBUG_VERBOSE:
                _LOGGER.debug("Request timed out after %s seconds.", TIMEOUT)
            raise

        except Exception:
            if DEBUG_VERBOSE:
                _LOGGER.exception("Unexpected exception during request")
            raise

    async def get(
        self,
        url: str,
        raw_reply: bool = False,
        raw_contents: bool = False,
        **kwargs: Any,
    ) -> Any:
        full_headers = self.__get_headers()
        if DEBUG_VERBOSE:
            _LOGGER.debug("[GET] URL: %s | Headers: %s", url, full_headers)
        return await self.request(
            METH_GET,
            url,
            data=None,
            headers=full_headers,
            raw_reply=raw_reply,
            raw_contents=raw_contents,
            **kwargs,
        )

    async def put(
        self, url: str, data: Any = None, headers: dict[str, str] | None = None
    ) -> Any:
        full_headers = self.__get_headers()
        if headers:
            full_headers.update(headers)
        if DEBUG_VERBOSE:
            _LOGGER.debug(
                "[PUT] URL: %s | Data: %s | Headers: %s", url, data, full_headers
            )
        return await self.request(METH_PUT, url, headers=full_headers, data=data)

    async def post(
        self,
        url: str,
        data: Any = None,
        headers: dict[str, str] | None = None,
        use_json: bool = True,
        raw_reply: bool = False,
        raw_contents: bool = False,
        **kwargs: Any,
    ) -> Any:
        full_headers = self.__get_headers()
        if headers:
            full_headers.update(headers)
        if use_json and data is not None:
            data = json.dumps(data)
        if DEBUG_VERBOSE:
            _LOGGER.debug(
                "[POST] URL: %s | Data: %s | Headers: %s", url, data, full_headers
            )
        return await self.request(
            METH_POST,
            url,
            headers=full_headers,
            data=data,
            raw_reply=raw_reply,
            raw_contents=raw_contents,
            **kwargs,
        )

    def __get_headers(self) -> dict[str, str]:
        data: dict[str, str] = {
            "Accept": "application/json",
            "Accept-Charset": "utf-8",
            "X-App-Version": self.HDR_XAPP_VERSION,
            "X-App-Name": "myAudi",
            "User-Agent": self.HDR_USER_AGENT,
        }
        if self.__token is not None:
            data["Authorization"] = "Bearer " + self.__token.get("access_token")
        if self.__xclientid is not None:
            data["X-Client-ID"] = self.__xclientid
        if DEBUG_VERBOSE:
            _LOGGER.debug("[HEADERS BUILT]: %s", data)
        return data


def obj_parser(obj):
    """Parse datetime."""
    for key, val in obj.items():
        with suppress(TypeError, ValueError):
            obj[key] = datetime.strptime(val, "%Y-%m-%dT%H:%M:%S%z")
    return obj


def json_loads(s: str) -> Any:
    return json.loads(s, object_hook=obj_parser)


__all__ = ["AudiAPI", "json_loads", "obj_parser"]
