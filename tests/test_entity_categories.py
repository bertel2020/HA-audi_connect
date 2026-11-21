"""Where entities are filed: what a driver looks at stays in the main view,
connection and mode details go to diagnostics, actions stay controls."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from homeassistant.const import EntityCategory

from custom_components.audiconnect.button import BUTTON_DESCRIPTIONS
from custom_components.audiconnect.sensor import (
    SENSOR_DESCRIPTIONS,
    AudiCloudLastPollSensor,
    AudiVehicleAgeSensor,
    AudiVehicleFreshnessSensor,
)

DIAGNOSTIC = {
    "last_update_time",
    "vehicle_reported_online",
    "vehicle_reported_active",
    "charging_scenario",
    "charging_type",
    "energy_flow",
    "climatisation_mode",
    "charging_current_limit_a",
    "charging_current_limit_mode",
    "battery_care_mode",
    "park_time",
    "access_overall_status",
}
MAIN_VIEW = {
    "mileage",
    "service_inspection_time",
    "service_inspection_distance",
    "oil_change_time",
    "oil_change_distance",
}
SENSORS = {d.key: d for d in SENSOR_DESCRIPTIONS}


@pytest.mark.parametrize("key", sorted(DIAGNOSTIC))
def test_connection_and_mode_sensors_are_diagnostic(key):
    assert SENSORS[key].entity_category is EntityCategory.DIAGNOSTIC


@pytest.mark.parametrize("key", sorted(MAIN_VIEW))
def test_odometer_and_service_are_in_the_main_view(key):
    assert SENSORS[key].entity_category is None


@pytest.mark.parametrize(
    "cls", [AudiVehicleFreshnessSensor, AudiVehicleAgeSensor, AudiCloudLastPollSensor]
)
def test_data_age_sensors_are_diagnostic(cls):
    entity = cls(MagicMock(), SimpleNamespace(vin="WAUZZZ00000000001"))
    assert entity.entity_category is EntityCategory.DIAGNOSTIC


def test_refresh_is_an_action_not_a_diagnostic():
    button = next(b for b in BUTTON_DESCRIPTIONS if b.key == "refresh_vehicle_data")
    assert button.entity_category is None
