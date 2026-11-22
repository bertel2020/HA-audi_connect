"""The credentials, reconfigure and options steps of the config flow."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest

from custom_components.ha_audi_connect import config_flow as cf
from custom_components.ha_audi_connect.audi_auth import AudiAuthError
from custom_components.ha_audi_connect.const import (
    CONF_REGION,
    CONF_SCAN_INTERVAL,
    CONF_SPIN,
    MIN_UPDATE_INTERVAL,
)


def run(coro):
    return asyncio.run(coro)


# --- credentials ---------------------------------------------------------------------


class FakeConnection:
    def __init__(self, outcome):
        self.outcome = outcome

    async def try_login(self, _log_error):
        if isinstance(self.outcome, Exception):
            raise self.outcome
        return self.outcome


def credentials_flow(outcome):
    flow = cf.AudiConfigFlow()
    flow._build_connection = lambda *_a, **_k: FakeConnection(outcome)
    flow.finished = []

    async def _finish(username, password):
        flow.finished.append((username, password))
        return {"type": "create_entry"}

    flow._finish_password_login = _finish
    return flow


def submit(flow):
    return run(
        flow.async_step_credentials({"username": "me@example.com", "password": "pw"})
    )


def test_a_good_login_finishes_the_entry():
    flow = credentials_flow(True)
    assert submit(flow)["type"] == "create_entry"
    assert flow.finished == [("me@example.com", "pw")]


@pytest.mark.parametrize("outcome", [False, AudiAuthError("no")])
def test_a_refused_login_shows_invalid_credentials(outcome):
    flow = credentials_flow(outcome)
    result = submit(flow)
    assert result["errors"] == {"base": "invalid_credentials"}
    assert flow.finished == []


def test_an_unexpected_error_is_reported_not_raised():
    result = submit(credentials_flow(RuntimeError("outage")))
    assert result["errors"] == {"base": "unexpected"}


def test_the_form_asks_for_username_and_password():
    result = run(cf.AudiConfigFlow().async_step_credentials())
    assert result["step_id"] == "credentials"
    assert {str(k) for k in result["data_schema"].schema} == {"username", "password"}


# --- reconfigure ---------------------------------------------------------------------


def reconfigure_flow(data=None):
    entry = SimpleNamespace(
        entry_id="e", title="me@example.com", data=data or {CONF_REGION: "DE"}
    )
    flow = cf.AudiConfigFlow()
    flow._get_reconfigure_entry = lambda: entry
    flow.hass = SimpleNamespace(
        config_entries=SimpleNamespace(async_schedule_reload=lambda _id: None)
    )
    flow.updates = {}

    def _abort(_entry, data_updates):
        flow.updates = data_updates
        return {"type": "abort", "reason": "reconfigure_successful"}

    flow.async_update_and_abort = _abort
    return flow


def test_reconfigure_stores_region_and_level_and_turns_an_empty_spin_into_none():
    flow = reconfigure_flow()
    region_key = next(iter(cf.REGION_OPTIONS))
    run(
        flow.async_step_reconfigure(
            {CONF_SPIN: "", CONF_REGION: region_key, "api_level": "1"}
        )
    )
    assert flow.updates[CONF_SPIN] is None
    assert flow.updates[CONF_REGION] == cf.REGION_OPTIONS[region_key]
    assert flow.updates["api_level"] == 1


def test_reconfigure_keeps_a_real_spin():
    flow = reconfigure_flow()
    region_key = next(iter(cf.REGION_OPTIONS))
    run(
        flow.async_step_reconfigure(
            {CONF_SPIN: "1234", CONF_REGION: region_key, "api_level": "0"}
        )
    )
    assert flow.updates[CONF_SPIN] == "1234"


def test_the_reconfigure_form_survives_an_entry_without_a_spin():
    """An entry created without an S-PIN stores None, not a missing key."""
    flow = reconfigure_flow({CONF_REGION: "DE", CONF_SPIN: None})
    result = run(flow.async_step_reconfigure())
    assert result["step_id"] == "reconfigure"
    defaults = {str(k): k.default() for k in result["data_schema"].schema}
    assert defaults[CONF_SPIN] == ""


# --- options -------------------------------------------------------------------------


def options_flow(options=None):
    entry = SimpleNamespace(options=options or {}, data={}, runtime_data=None)

    class Flow(cf.OptionsFlowHandler):
        config_entry = entry

    flow = Flow()
    flow.async_create_entry = lambda title, data: {"type": "create_entry", "data": data}
    return flow


def test_the_options_form_has_no_startup_option_any_more():
    result = run(options_flow().async_step_init())
    keys = {str(k) for k in result["data_schema"].schema}
    assert "scan_initial" not in keys
    assert {"climate_quick_start", "experimental_commands", CONF_SCAN_INTERVAL} <= keys


def test_the_scan_interval_is_raised_to_the_minimum():
    result = run(
        options_flow().async_step_init(
            {
                "climate_quick_start": False,
                "experimental_commands": False,
                "refresh_after_action": False,
                "update_sleep": 5,
                CONF_SCAN_INTERVAL: 1,
            }
        )
    )
    assert result["data"][CONF_SCAN_INTERVAL] == MIN_UPDATE_INTERVAL


def test_saving_the_options_stores_exactly_what_was_entered():
    flow = options_flow({"local_dealers": {"vin": {"dealer_name": "X"}}})
    result = run(flow.async_step_init({CONF_SCAN_INTERVAL: 30}))
    assert result["data"] == {CONF_SCAN_INTERVAL: 30}
