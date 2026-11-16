"""What an A6 e-tron reports, and what the integration now makes of it."""

from __future__ import annotations

import copy
from types import SimpleNamespace

import pytest

from custom_components.audiconnect.audi_connect_account import AudiConnectVehicle
from custom_components.audiconnect.audi_models import VehicleDataResponse
from custom_components.audiconnect.capability_jobs import BASE_SELECTIVE_JOBS
from custom_components.audiconnect import sensor as sensor_platform
from custom_components.audiconnect.sensor import (
    SENSOR_DESCRIPTIONS,
    is_sensor_available_for,
    sensor_descriptions_to_create,
)

from tests.fixture_a6_etron import PAYLOAD


def states_of(payload):
    return {s["name"]: s["value"] for s in VehicleDataResponse(payload).states}


def vehicle_with(state):
    """A real AudiConnectVehicle reading the given state, without any network."""
    vehicle = object.__new__(AudiConnectVehicle)
    vehicle._vehicle = SimpleNamespace(state=state, fields={})
    return vehicle


# --- the new values are parsed --------------------------------------------------


def test_the_new_settings_are_parsed():
    states = states_of(copy.deepcopy(PAYLOAD))

    assert states["batteryCareMode"] == "deactivated"
    assert states["chargingScenario"] == "off"
    assert states["climatisationMode"] == "economy"
    assert states["parkingBrake"] is True


def test_the_battery_care_mode_survives_having_no_timestamp():
    """The A6 sends the setting without a capture time. Dropping it for that left
    the sensor unavailable on a real car while a fixture with a made-up
    timestamp passed."""
    payload = copy.deepcopy(PAYLOAD)
    assert "carCapturedTimestamp" not in str(
        payload["charging"]["chargingCareSettings"]
    )
    vehicle = vehicle_with(states_of(payload))

    assert vehicle.battery_care_mode == "deactivated"


def test_a_state_without_a_timestamp_does_not_move_the_last_update_time():
    response = VehicleDataResponse(copy.deepcopy(PAYLOAD))
    care = next(s for s in response.states if s["name"] == "batteryCareMode")

    assert care["measure_time"] is None


def test_the_parking_brake_job_is_requested():
    assert "parkingBrake" in BASE_SELECTIVE_JOBS


def test_a_parking_brake_that_is_off_is_still_a_reading():
    payload = copy.deepcopy(PAYLOAD)
    payload["parkingBrake"]["parkingBrakeStatus"]["value"]["value"] = False
    vehicle = vehicle_with(states_of(payload))

    assert vehicle.parking_brake is False
    assert vehicle.parking_brake_supported is True


def test_a_car_without_the_job_has_no_parking_brake():
    payload = copy.deepcopy(PAYLOAD)
    del payload["parkingBrake"]
    vehicle = vehicle_with(states_of(payload))

    assert vehicle.parking_brake is None
    assert not vehicle.parking_brake_supported


# --- "invalid" is no reading, not a state -------------------------------------------


@pytest.mark.parametrize(
    "prop", ["plug_state", "plug_lock_state", "plug_led_color", "external_power"]
)
def test_invalid_plug_values_are_not_reported(prop):
    vehicle = vehicle_with(states_of(copy.deepcopy(PAYLOAD)))

    assert getattr(vehicle, prop) is None
    assert not getattr(vehicle, f"{prop}_supported")


def test_the_current_limit_mode_ignores_invalid():
    vehicle = vehicle_with(states_of(copy.deepcopy(PAYLOAD)))

    assert vehicle.charging_current_limit_mode is None


def test_a_real_plug_state_still_comes_through():
    state = states_of(copy.deepcopy(PAYLOAD))
    state.update(plugState="connected", plugLockState="locked", externalPower="ready")
    vehicle = vehicle_with(state)

    assert vehicle.plug_state is True
    assert vehicle.plug_lock_state is False  # locked is the "closed" side
    assert vehicle.external_power == "Ready"


# --- sensors the account cannot feed --------------------------------------------------


def _trip_descriptions():
    return [d for d in SENSOR_DESCRIPTIONS if d.requires == "support_trip_data"]


def test_the_four_trip_sensors_need_trip_support():
    assert {d.key for d in _trip_descriptions()} == {
        "shortterm_current",
        "shortterm_reset",
        "longterm_current",
        "longterm_reset",
    }


def test_trip_sensors_are_off_when_the_account_cannot_poll_trips():
    auth0 = SimpleNamespace(support_trip_data=False)
    legacy = SimpleNamespace(support_trip_data=True)

    for description in _trip_descriptions():
        assert is_sensor_available_for(description, auth0) is False
        assert is_sensor_available_for(description, legacy) is True


def test_sensors_without_a_requirement_are_unaffected():
    plain = next(d for d in SENSOR_DESCRIPTIONS if d.key == "mileage")

    assert is_sensor_available_for(plain, SimpleNamespace()) is True


def test_the_platform_hands_the_requirement_to_the_creation_gate(monkeypatch):
    """The call site, not just the helper: a registry entry must not bring a trip
    sensor back, which only holds if ``configured`` reaches should_create_entity."""
    seen = {}

    def gate(
        hass, platform, key, vehicle, attr_key, capability=None, *, configured=True
    ):
        seen[key] = configured
        return configured

    monkeypatch.setattr(sensor_platform, "should_create_entity", gate)
    created = {
        d.key
        for d in sensor_descriptions_to_create(
            None, SimpleNamespace(support_trip_data=False)
        )
    }

    assert seen["longterm_current"] is False and seen["mileage"] is True
    assert "longterm_current" not in created and "mileage" in created
