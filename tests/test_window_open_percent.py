"""How far each window is open, in percent."""

from __future__ import annotations

import copy

import pytest

from custom_components.ha_audi_connect.sensor import SENSOR_DESCRIPTIONS
from tests.fixture_a6_etron import PAYLOAD
from tests.test_a6_etron import states_of, vehicle_with

WINDOWS = [
    {"name": "frontLeft", "status": ["closed"], "windowOpen_pct": 0},
    {"name": "frontRight", "status": ["open"], "windowOpen_pct": 35},
    {"name": "rearLeft", "status": ["closed"], "windowOpen_pct": 0},
    {"name": "rearRight", "status": ["unsupported"]},
]


def payload(windows):
    data = copy.deepcopy(PAYLOAD)
    data["access"] = {
        "accessStatus": {
            "value": {
                "carCapturedTimestamp": "2026-11-16T12:39:16+00:00",
                "overallStatus": "safe",
                "doors": [],
                "windows": windows,
            }
        }
    }
    return data


def car(windows):
    return vehicle_with(states_of(payload(windows)))


def test_each_reported_percentage_is_read():
    vehicle = car(WINDOWS)
    assert vehicle.window_open_pct_front_left == 0
    assert vehicle.window_open_pct_front_right == 35
    assert vehicle.window_open_pct_rear_left == 0


def test_a_window_without_a_figure_has_no_value_instead_of_zero():
    assert car(WINDOWS).window_open_pct_rear_right is None


@pytest.mark.parametrize("bad", [-1, 101, "x", True, None])
def test_an_implausible_figure_is_ignored(bad):
    windows = [{"name": "frontLeft", "status": ["open"], "windowOpen_pct": bad}]
    assert car(windows).window_open_pct_front_left is None


def test_there_is_a_sensor_per_window_in_percent():
    keys = {d.key: d for d in SENSOR_DESCRIPTIONS}
    for name in ("front_left", "front_right", "rear_left", "rear_right"):
        description = keys[f"window_open_pct_{name}"]
        assert description.native_unit_of_measurement == "%"
        assert description.state_class is not None
