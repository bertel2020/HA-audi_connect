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


def test_the_symbol_stays_out_of_the_sensor_attributes():
    lights = [
        {
            "text": "Bitte Batterie laden",
            "iconName": "E194_yellow.svg",
            "icon": "data:image/svg+xml;base64,PHN2Zz48L3N2Zz4=",
        }
    ]
    vehicle = vehicle_with({"warningLights": lights})
    warning = _warning_light_attrs(vehicle)["warnings"][0]
    assert "icon" not in warning
    assert warning["iconName"] == "E194_yellow.svg"


def test_a_symbol_is_learned_once_and_only_when_it_looks_like_one():
    from unittest.mock import MagicMock, patch

    from custom_components.ha_audi_connect import warning_icons

    svg = "data:image/svg+xml;base64,PHN2Zz48L3N2Zz4="
    with patch.object(warning_icons, "Store", MagicMock()):
        store = warning_icons.WarningIconStore(MagicMock())
    lights = [
        {"iconName": "E1_yellow.svg", "icon": svg},
        {"iconName": "../evil", "icon": svg},
        {"iconName": "E2.svg", "icon": "data:text/html;base64,AAAA"},
        {"iconName": "E3.svg"},
        "not a dict",
    ]
    assert store.learn(lights) is True
    assert store.icons == {"E1_yellow.svg": svg}
    assert store.learn(lights) is False
    assert store.learn(None) is False
