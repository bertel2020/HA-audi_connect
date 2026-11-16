"""The profile's charging current: max or reduced, written into the whole profile."""

from __future__ import annotations

import asyncio
import copy
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.exceptions import HomeAssistantError

from custom_components.audiconnect.audi_payloads import build_profile_change
from custom_components.audiconnect.select import (
    AudiProfileCurrentSelect,
    profile_current_supported,
)

VALUE = {
    "vehiclePositionedInProfileID": 1,
    "profiles": [
        {
            "id": 1,
            "uuid": "u",
            "name": "Zuhause",
            "maxChargingCurrent": "max",
            "minSOC_pct": 25,
            "options": {"autoUnlockPlugWhenCharged": "invalid"},
            "position": {"lat": 1.0, "lon": 2.0},
            "preferredChargingTimes": [{"id": 1, "enabled": False}],
        }
    ],
}


def make(current="max", ok=True):
    vehicle = SimpleNamespace(
        vin="WAUZZZ00000000001", active_charging_profile_max_current=current
    )
    coordinator = MagicMock()
    coordinator.account.connection.set_profile_charging_current = AsyncMock(
        return_value=ok
    )
    coordinator.async_request_refresh = AsyncMock()
    return AudiProfileCurrentSelect(coordinator, vehicle), coordinator


def test_only_the_current_changes_and_everything_else_is_sent_back():
    original = copy.deepcopy(VALUE)
    profile_id, body = build_profile_change(VALUE, None, maxChargingCurrent="reduced")
    assert profile_id == 1
    sent = body["profile"]
    assert sent["maxChargingCurrent"] == "reduced"
    expected = dict(original["profiles"][0], maxChargingCurrent="reduced")
    assert sent == expected
    assert original == VALUE, "the car's own data is not modified"


@pytest.mark.parametrize("bad", ["fast", "", None, "MAX"])
def test_an_unknown_current_is_refused(bad):
    with pytest.raises(ValueError, match="current"):
        build_profile_change(VALUE, None, maxChargingCurrent=bad)


def test_an_unknown_profile_setting_is_refused():
    with pytest.raises(ValueError, match="Not changeable"):
        build_profile_change(VALUE, None, name="x")


def test_the_select_shows_the_current_and_writes_a_new_one():
    select, coordinator = make("max")
    assert select.current_option == "max"
    assert select.options == ["max", "reduced"]
    asyncio.run(select.async_select_option("reduced"))
    coordinator.account.connection.set_profile_charging_current.assert_awaited_once_with(
        "WAUZZZ00000000001", None, "reduced"
    )


def test_a_value_it_does_not_know_is_no_option():
    assert make("invalid")[0].current_option is None


def test_a_refused_write_is_reported():
    select, _ = make(ok=False)
    with pytest.raises(HomeAssistantError):
        asyncio.run(select.async_select_option("reduced"))


@pytest.mark.parametrize(
    ("auth0", "flags", "expected"),
    [
        (True, {}, True),
        (True, {"supportsMaxChargingCurrent": True}, True),
        (True, {"supportsMaxChargingCurrent": False}, False),
        (False, {}, False),
    ],
)
def test_the_select_follows_the_account_and_the_cars_answer(auth0, flags, expected):
    vehicle = SimpleNamespace(
        _audi_service=SimpleNamespace(uses_auth0=auth0),
        charging_profiles_supports=flags,
    )
    assert profile_current_supported(vehicle) is expected
