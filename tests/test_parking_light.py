"""The parking light reads each side, tolerates odd data and shows both sides."""

from types import SimpleNamespace as NS

import pytest

from custom_components.audiconnect.audi_vehicle_properties import (
    AudiVehicleProperties,
)


def props(value):
    fields = {} if value is None else {"LIGHT_STATUS": value}
    obj = AudiVehicleProperties.__new__(AudiVehicleProperties)
    obj._vehicle = NS(fields=fields)
    return obj


def lights(left, right):
    return [{"name": "left", "status": left}, {"name": "right", "status": right}]


@pytest.mark.parametrize(
    ("left", "right", "expected"),
    [("off", "off", False), ("on", "off", True), ("off", "on", True)],
)
def test_on_when_either_side_is_on(left, right, expected):
    assert props(lights(left, right)).parking_light is expected


def test_both_sides_are_exposed():
    assert props(lights("on", "off")).parking_light_sides == {
        "left": "on",
        "right": "off",
    }


def test_a_single_entry_does_not_crash():
    p = props([{"name": "left", "status": "on"}])
    assert p.parking_light is True


def test_garbage_gives_unknown_not_an_error():
    p = props(["x", {"name": "left"}])
    assert p.parking_light is None
    assert p.parking_light_sides is None


def test_not_supported_without_the_field():
    p = props(None)
    assert not p.parking_light_supported
    assert p.parking_light is None
