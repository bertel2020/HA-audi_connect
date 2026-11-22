"""Readings that change over time carry a state class, so Home Assistant keeps statistics."""

from __future__ import annotations

import pytest
from homeassistant.components.sensor import SensorStateClass

from custom_components.ha_audi_connect.sensor import SENSOR_DESCRIPTIONS

BY_KEY = {d.key: d for d in SENSOR_DESCRIPTIONS}


@pytest.mark.parametrize(
    "key",
    [
        "state_of_charge",
        "range",
        "primary_engine_range",
        "secondary_engine_range",
        "tank_level",
        "charging_power",
        "outdoor_temperature",
    ],
)
def test_measurement_sensors_have_a_state_class(key):
    assert BY_KEY[key].state_class is SensorStateClass.MEASUREMENT
