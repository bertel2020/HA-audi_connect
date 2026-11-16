"""The parking-heater switch belongs to legacy accounts only.

On an Auth0 car its state falls back to climatisationState, so it duplicated
the climate switch, and its command targets the legacy parking-heater API.
"""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from custom_components.audiconnect import switch


def _created_keys(uses_auth0: bool) -> set[str]:
    vehicle = SimpleNamespace(
        vin="WAUZZZ00000000001",
        _audi_service=SimpleNamespace(uses_auth0=uses_auth0),
    )
    entry = MagicMock()
    entry.options = {"experimental_commands": True}
    entry.runtime_data.account.config_vehicles = [SimpleNamespace(vehicle=vehicle)]
    added: list = []

    def fake_should_create(hass, platform, key, vehicle, attr_key, *a, configured=True):
        return configured

    with patch.object(switch, "should_create_entity", fake_should_create):
        asyncio.run(switch.async_setup_entry(MagicMock(), entry, added.extend))
    return {e.entity_description.key for e in added if hasattr(e, "entity_description")}


def test_auth0_car_gets_no_parking_heater_switch():
    assert "preheater_active" not in _created_keys(uses_auth0=True)


def test_legacy_account_keeps_the_parking_heater_switch():
    assert "preheater_active" in _created_keys(uses_auth0=False)


@pytest.mark.parametrize("uses_auth0", [True, False])
def test_other_switches_are_unaffected(uses_auth0):
    assert "plug_auto_unlock" in _created_keys(uses_auth0=uses_auth0)


def test_unlock_setting_does_not_share_the_window_heating_icon():
    icons = {d.key: d.icon for d in switch.SWITCH_DESCRIPTIONS}
    assert icons["climatisation_at_unlock"] != icons["climatisation_window_heating"]


def _setting_keys(flags):
    vehicle = SimpleNamespace(
        vin="WAUZZZ00000000001",
        _audi_service=SimpleNamespace(uses_auth0=True),
        climatisation_supports=flags,
    )
    entry = MagicMock()
    entry.options = {}
    entry.runtime_data.account.config_vehicles = [SimpleNamespace(vehicle=vehicle)]
    added: list = []

    def fake_should_create(hass, platform, key, vehicle, attr_key, *a, configured=True):
        return configured

    with patch.object(switch, "should_create_entity", fake_should_create):
        asyncio.run(switch.async_setup_entry(MagicMock(), entry, added.extend))
    return {e.entity_description.key for e in added if hasattr(e, "entity_description")}


def test_window_heating_is_hidden_when_the_car_says_it_is_unsupported():
    keys = _setting_keys({"supportsWindowHeatingEnabled": False})
    assert "climatisation_window_heating" not in keys
    assert "climatisation_zone_front_left" in keys


def test_a_setting_stays_when_the_car_gave_no_answer():
    assert "climatisation_window_heating" in _setting_keys({})


def test_a_setting_stays_when_the_car_says_it_is_supported():
    assert "climatisation_zone_rear_left" in _setting_keys(
        {"supportsZoneRearLeftEnabled": True}
    )
