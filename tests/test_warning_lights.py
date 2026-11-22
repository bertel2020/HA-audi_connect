"""The vehicle's warning lights: none, some, and not said at all."""

from __future__ import annotations

import copy

from custom_components.ha_audi_connect.binary_sensor import BINARY_SENSOR_DESCRIPTIONS
from custom_components.ha_audi_connect.sensor import (
    SENSOR_DESCRIPTIONS,
    _warning_light_attrs,
)
from tests.fixture_a6_etron import PAYLOAD
from tests.test_a6_etron import states_of, vehicle_with


def payload_with(value):
    payload = copy.deepcopy(PAYLOAD)
    payload["vehicleHealthWarnings"] = {"warningLights": {"value": value}}
    return payload


def test_an_empty_object_means_no_warnings():
    states = states_of(payload_with({}))
    assert states["warningLights"] == []
    vehicle = vehicle_with({"warningLights": states["warningLights"]})
    assert vehicle.warning_lights == []
    assert vehicle.warning_light_count == 0


def test_lit_warnings_are_counted_and_kept():
    lights = [
        {"text": "Tyre pressure", "category": "yellow", "extra": {"nested": 1}},
        {"text": "Brake", "category": "red"},
    ]
    states = states_of(payload_with({"warningLights": lights}))
    vehicle = vehicle_with({"warningLights": states["warningLights"]})
    assert vehicle.warning_light_count == 2
    attrs = _warning_light_attrs(vehicle)
    assert attrs["warnings"][0] == {"text": "Tyre pressure", "category": "yellow"}
    assert "extra" not in attrs["warnings"][0]


def test_no_job_at_all_means_nothing_is_said():
    payload = copy.deepcopy(PAYLOAD)
    payload.pop("vehicleHealthWarnings", None)
    assert "warningLights" not in states_of(payload)
    vehicle = vehicle_with({})
    assert vehicle.warning_lights is None
    assert vehicle.warning_light_count is None


def test_the_entities_exist():
    assert any(d.key == "warning_light_count" for d in SENSOR_DESCRIPTIONS)
    assert any(d.key == "warning_lights" for d in BINARY_SENSOR_DESCRIPTIONS)
