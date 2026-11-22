"""The raw reply log is opt-in, never covers sign-in routes and masks what it should."""

from __future__ import annotations

import asyncio
import json
import logging
from types import SimpleNamespace

from custom_components.ha_audi_connect.audi_api import AudiAPI
from custom_components.ha_audi_connect.config_flow import OptionsFlowHandler
from custom_components.ha_audi_connect.const import (
    CONF_LOG_RAW_RESPONSES,
    CONF_LOG_RAW_UNREDACTED,
)

VIN = "WAUZZZGH7SA000001"
VEHICLE_URL = f"https://emea.bff.cariad.digital/vehicle/v1/vehicles/{VIN}/selectivestatus?jobs=access"
TOKEN_URL = "https://identity.vwgroup.io/oidc/v1/token"
BODY = {
    "access": {
        "accessStatus": {"value": {"doors": [{"name": "bonnet", "status": ["closed"]}]}}
    },
    "position": {"lat": 48.1234, "lon": 11.5678},
    "vin": VIN,
    "spin": "1234",
}


class _Response:
    status = 200
    reason = "OK"
    headers: dict = {}

    def __init__(self, body):
        self._body = json.dumps(body)

    async def text(self):
        return self._body

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False


class _Session:
    def __init__(self, body):
        self._body = body

    def request(self, *a, **kw):
        return _Response(self._body)


def _get(url, mode):
    api = AudiAPI(_Session(BODY))
    if mode is not None:
        api.raw_logging = mode
    return asyncio.run(api.request("GET", url, data=None))


def test_nothing_is_logged_by_default(caplog):
    with caplog.at_level(logging.DEBUG):
        _get(VEHICLE_URL, None)
    assert "Raw API response" not in caplog.text


def test_the_reply_is_logged_whole_with_the_secrets_masked(caplog):
    with caplog.at_level(logging.DEBUG):
        _get(VEHICLE_URL, "redacted")
    text = caplog.text
    assert "Raw API response" in text and '"bonnet"' in text and '"closed"' in text
    assert VIN not in text and "<vin>" in text
    assert "48.1234" not in text and "11.5678" not in text and "<position>" in text
    assert '"spin": "<redacted>"' in text


def test_the_full_mode_leaves_the_vin_and_the_position_alone(caplog):
    with caplog.at_level(logging.DEBUG):
        _get(VEHICLE_URL, "full")
    assert VIN in caplog.text and "48.1234" in caplog.text


def test_sign_in_routes_are_never_logged(caplog):
    for mode in ("redacted", "full"):
        caplog.clear()
        with caplog.at_level(logging.DEBUG):
            _get(TOKEN_URL, mode)
        assert "Raw API response" not in caplog.text


def _flow(options=None):
    entry = SimpleNamespace(options=options or {}, data={}, runtime_data=None)

    class Flow(OptionsFlowHandler):
        config_entry = entry

    return Flow()


def test_the_options_form_offers_both_logging_options_off_by_default():
    result = asyncio.run(_flow().async_step_init())
    schema = {str(k): k for k in result["data_schema"].schema}
    assert schema[CONF_LOG_RAW_RESPONSES].default() is False
    assert schema[CONF_LOG_RAW_UNREDACTED].default() is False


def test_a_reply_with_parsed_timestamps_is_logged(caplog):
    # The real replies are parsed with a loader that turns timestamps into datetimes.
    from datetime import UTC, datetime

    payload = {"carCapturedTimestamp": datetime(2026, 11, 22, 8, 19, 3, tzinfo=UTC)}
    for mode in ("redacted", "full"):
        caplog.clear()
        api = AudiAPI(_Session({}))
        api.raw_logging = mode
        with caplog.at_level(logging.DEBUG):
            api._log_raw_response(VEHICLE_URL, payload)
        assert "Raw API response" in caplog.text and "2026-11-22" in caplog.text


def test_a_reply_that_cannot_be_logged_never_breaks_the_request(caplog):
    loop: dict = {}
    loop["me"] = loop  # json refuses a circular reply
    api = AudiAPI(_Session({}))
    api.raw_logging = "full"
    with caplog.at_level(logging.DEBUG):
        api._log_raw_response(VEHICLE_URL, loop)
    assert "could not be logged" in caplog.text


def test_the_user_id_is_masked_unless_the_full_mode_is_chosen(caplog):
    payload = {"data": [{"userId": "c4a5777b-ae3b-412e-b866-d92cf2ca1bf8"}]}
    api = AudiAPI(_Session({}))
    api.raw_logging = "redacted"
    with caplog.at_level(logging.DEBUG):
        api._log_raw_response(VEHICLE_URL, payload)
    assert "c4a5777b" not in caplog.text and "<redacted>" in caplog.text
    caplog.clear()
    api.raw_logging = "full"
    with caplog.at_level(logging.DEBUG):
        api._log_raw_response(VEHICLE_URL, payload)
    assert "c4a5777b" in caplog.text
