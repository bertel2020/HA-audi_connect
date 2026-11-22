"""Sensors for values only some cars report exist only for cars that report them.

The A6 e-tron sends no connectionState in readiness and "invalid" for the AC
current limit, so it gets none of these four. A car that does report them keeps
them. An entity created earlier is kept by should_create_entity, as for every
other sensor.
"""

from __future__ import annotations

from types import SimpleNamespace as NS

import pytest

from custom_components.ha_audi_connect.audi_connect_account import AudiConnectVehicle
from custom_components.ha_audi_connect.audi_entity import is_entity_supported
from custom_components.ha_audi_connect.sensor import SENSOR_DESCRIPTIONS

KEYS = (
    "vehicle_reported_online",
    "vehicle_reported_active",
    "charging_current_limit_a",
    "charging_current_limit_mode",
)


def _car(state):
    car = AudiConnectVehicle(None, NS(vin="FAKEVIN", state={}, fields={}))
    car._vehicle.state.update(state)
    return car


def _description(key):
    return next(d for d in SENSOR_DESCRIPTIONS if d.key == key)


@pytest.mark.parametrize("key", KEYS)
def test_a_car_that_reports_nothing_gets_no_sensor(key):
    # The A6: no readiness block, current limit "invalid".
    car = _car({"chargingCurrentLimitMode": "invalid"})
    description = _description(key)
    assert not is_entity_supported(car, description.attr_key, description.capability)


def test_a_car_that_reports_them_gets_all_four():
    car = _car(
        {
            "vehicleReportedOnline": True,
            "vehicleReportedActive": False,
            "chargingCurrentLimitA": 12,
            "chargingCurrentLimitMode": "reduced",
        }
    )
    for key in KEYS:
        description = _description(key)
        assert is_entity_supported(car, description.attr_key, description.capability)


def test_the_charging_capability_alone_no_longer_creates_the_limit_sensors():
    # Before, "charging" in the capability list created them for every car
    # that charges, whether or not it reports a limit.
    for key in ("charging_current_limit_a", "charging_current_limit_mode"):
        assert _description(key).capability is None
