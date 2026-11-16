"""Switching the plug auto-unlock changes that one setting and nothing else."""

from __future__ import annotations

import asyncio

import pytest

from custom_components.audiconnect.audi_vehicle_properties import (
    AudiVehicleProperties,
)
from custom_components.audiconnect.switch import SWITCH_DESCRIPTIONS
from tests.test_q8_charging_settings_preservation import VIN, service

A6_SETTINGS = {
    "carCapturedTimestamp": "2026-11-10T12:00:00Z",
    "maxChargeCurrentAC": "invalid",
    "autoUnlockPlugWhenCharged": "off",
    "autoUnlockPlugWhenChargedAC": "off",
    "targetSOC_pct": 100,
}


def test_switching_on_changes_only_that_setting():
    svc, api = service(dict(A6_SETTINGS))
    asyncio.run(svc.set_plug_auto_unlock(VIN, True))
    method, url, payload = api.writes[0]
    assert method == "PUT" and url.endswith("/charging/settings")
    assert payload == {
        "autoUnlockPlugWhenCharged": "off",
        "autoUnlockPlugWhenChargedAC": "on",
        "targetSOC_pct": 100,
    }


def test_switching_off_sends_off_and_keeps_the_target():
    svc, api = service({**A6_SETTINGS, "autoUnlockPlugWhenChargedAC": "on"})
    asyncio.run(svc.set_plug_auto_unlock(VIN, False))
    assert api.writes[0][2] == {
        "autoUnlockPlugWhenCharged": "off",
        "autoUnlockPlugWhenChargedAC": "off",
        "targetSOC_pct": 100,
    }


def test_the_cars_no_reading_marker_is_not_sent_back():
    svc, api = service(dict(A6_SETTINGS))
    asyncio.run(svc.set_target_state_of_charge(VIN, 80))
    assert "maxChargeCurrentAC" not in api.writes[0][2]
    assert api.writes[0][2]["targetSOC_pct"] == 80


def test_unknown_settings_stop_the_write():
    svc, api = service({**A6_SETTINGS, "somethingNew": 1})
    with pytest.raises(ValueError, match="potentially destructive"):
        asyncio.run(svc.set_plug_auto_unlock(VIN, True))
    assert api.writes == []


def test_no_settings_means_no_blind_write():
    svc, api = service(None)
    with pytest.raises(ValueError, match="refusing blind update"):
        asyncio.run(svc.set_plug_auto_unlock(VIN, True))
    assert api.writes == []


def test_no_write_without_auth0():
    svc, api = service(dict(A6_SETTINGS), auth0=False)
    with pytest.raises(ValueError, match="Auth0"):
        asyncio.run(svc.set_plug_auto_unlock(VIN, True))
    assert api.writes == [] and api.urls == []


@pytest.mark.parametrize(
    ("raw", "shown"),
    [("off", "disabled"), ("on", "enabled"), ("permanent", "enabled"), ("x", None)],
)
def test_the_reported_value_is_read_either_way(raw, shown):
    class V:
        _vehicle = type("S", (), {"state": {"chargingPlugAutoUnlock": raw}})()

    assert AudiVehicleProperties.charging_plug_auto_unlock.fget(V()) == shown


def test_the_switch_is_experimental_and_follows_the_reported_state():
    description = next(d for d in SWITCH_DESCRIPTIONS if d.key == "plug_auto_unlock")
    assert description.experimental is True
    assert description.value_fn("enabled") is True
    assert description.value_fn("disabled") is False
    assert description.value_fn(None) is False


def test_the_real_a6_settings_do_not_block_a_charge_target_write():
    """The A6 reports autoUnlockPlugWhenCharged next to the AC variant. Treating
    it as an unknown setting made every charge-target write refuse on that car."""
    svc, api = service(dict(A6_SETTINGS))
    asyncio.run(svc.set_target_state_of_charge(VIN, 80))
    assert api.writes[0][2]["targetSOC_pct"] == 80
