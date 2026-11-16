"""Choosing comfort or economy writes the mode with the app's body."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.audiconnect.audi_payloads import (
    build_climatisation_settings_update,
)
from custom_components.audiconnect.select import (
    AudiClimatisationModeSelect,
    climatisation_mode_supported,
)
from homeassistant.exceptions import HomeAssistantError

SETTINGS = {
    "targetTemperature_C": 22.5,
    "climatisationMode": "economy",
    "climatizationAtUnlock": False,
    "zoneFrontLeftEnabled": True,
}


def make(mode="economy", ok=True):
    vehicle = SimpleNamespace(vin="WAUZZZ00000000001", climatisation_mode=mode)
    coordinator = MagicMock()
    coordinator.account.connection.set_climatisation_setting = AsyncMock(
        return_value=ok
    )
    coordinator.async_request_refresh = AsyncMock()
    return AudiClimatisationModeSelect(coordinator, vehicle), coordinator


def test_the_current_mode_and_both_choices_are_offered():
    select, _ = make("economy")
    assert select.current_option == "economy"
    assert select.options == ["comfort", "economy"]


def test_an_unknown_mode_is_added_rather_than_hiding_the_entity():
    select, _ = make("automatic")
    assert select.options == ["comfort", "economy", "automatic"]
    assert select.current_option == "automatic"


def test_no_reading_means_no_current_option():
    assert make("invalid")[0].current_option is None
    assert make(None)[0].current_option is None


def test_selecting_a_mode_writes_it_through_the_settings_request():
    select, coordinator = make("economy")
    asyncio.run(select.async_select_option("comfort"))
    coordinator.account.connection.set_climatisation_setting.assert_awaited_once_with(
        "WAUZZZ00000000001", "climatisationMode", "comfort"
    )
    coordinator.async_request_refresh.assert_awaited_once()


def test_a_refused_write_is_reported():
    select, _ = make(ok=False)
    with pytest.raises(HomeAssistantError):
        asyncio.run(select.async_select_option("comfort"))


def test_the_mode_goes_into_the_app_body_and_the_rest_stays():
    body = build_climatisation_settings_update(SETTINGS, climatisationMode="comfort")
    assert body["climatisationMode"] == "comfort"
    assert body["targetTemperature"] == 22.5
    assert body["zoneFrontLeftEnabled"] is True


@pytest.mark.parametrize(
    ("auth0", "flags", "expected"),
    [
        (True, {}, True),
        (True, {"supportsClimatisationMode": True}, True),
        (True, {"supportsClimatisationMode": False}, False),
        (False, {}, False),
    ],
)
def test_the_select_follows_the_account_and_the_cars_own_answer(auth0, flags, expected):
    vehicle = SimpleNamespace(
        _audi_service=SimpleNamespace(uses_auth0=auth0),
        climatisation_supports=flags,
    )
    assert climatisation_mode_supported(vehicle) is expected
