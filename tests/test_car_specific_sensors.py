"""Sensors that only make sense for some cars are only created for those."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from custom_components.ha_audi_connect import sensor
from custom_components.ha_audi_connect.sensor import (
    SENSOR_DESCRIPTIONS,
    is_sensor_available_for,
)
from tests.test_a6_etron import vehicle_with

ENGINE_KEYS = (
    "primary_engine_type",
    "hybrid_range",
    "primary_engine_range",
    "primary_engine_range_percent",
    "secondary_engine_type",
    "secondary_engine_range",
    "secondary_engine_range_percent",
)
BY_KEY = {d.key: d for d in SENSOR_DESCRIPTIONS}


@pytest.mark.parametrize(
    ("car_type", "expected"),
    [("electric", False), ("hybrid", True), ("combustion", True), (None, True)],
)
def test_only_a_purely_electric_car_has_no_further_engine(car_type, expected):
    state = {} if car_type is None else {"carType": car_type}
    assert vehicle_with(state).has_non_electric_engine is expected


@pytest.mark.parametrize("key", ENGINE_KEYS)
def test_engine_sensors_are_not_made_for_an_electric_car(key):
    electric = SimpleNamespace(has_non_electric_engine=False)
    hybrid = SimpleNamespace(has_non_electric_engine=True)
    assert is_sensor_available_for(BY_KEY[key], electric) is False
    assert is_sensor_available_for(BY_KEY[key], hybrid) is True


def test_the_car_type_is_not_a_sensor_but_part_of_the_device():
    assert "car_type" not in BY_KEY


def _created(options, **figures):
    vehicle = SimpleNamespace(vin="WAUZZZ00000000001", **figures)
    entry = MagicMock()
    entry.options = options
    entry.runtime_data.account.config_vehicles = [SimpleNamespace(vehicle=vehicle)]
    entry.runtime_data.coordinator = MagicMock()
    added: list = []
    with patch.object(sensor, "sensor_descriptions_to_create", lambda *a: []):
        asyncio.run(sensor.async_setup_entry(MagicMock(), entry, added.extend))
    return {type(e).__name__ for e in added}


def test_a_single_service_figure_makes_no_overview():
    names = _created({}, service_inspection_time=307)
    assert "AudiServiceOverviewSensor" not in names


def test_a_car_reporting_two_service_figures_gets_the_overview():
    names = _created({}, service_inspection_time=307, oil_change_time=100)
    assert "AudiServiceOverviewSensor" in names
