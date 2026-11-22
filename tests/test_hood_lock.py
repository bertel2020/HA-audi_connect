"""The hood lock reads the car's own lock state: 2 is locked, anything else is not."""

from types import SimpleNamespace as NS

import pytest

from custom_components.audiconnect.audi_vehicle_properties import (
    AudiVehicleProperties,
)


def props(value):
    fields = {} if value is None else {"LOCK_STATE_HOOD": value}
    obj = AudiVehicleProperties.__new__(AudiVehicleProperties)
    obj._vehicle = NS(fields=fields)
    return obj


@pytest.mark.parametrize(("raw", "unlocked"), [("2", False), ("1", True)])
def test_unlocked_unless_the_car_says_locked(raw, unlocked):
    p = props(raw)
    assert p.hood_unlocked_supported
    assert p.hood_unlocked is unlocked


def test_not_supported_when_the_car_does_not_report_it():
    p = props(None)
    assert not p.hood_unlocked_supported
    assert p.hood_unlocked is None
