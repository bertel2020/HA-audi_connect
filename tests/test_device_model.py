"""The kind of drive shows in the device's model line."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from custom_components.ha_audi_connect.audi_entity import AudiEntity


def model_of(car_type, model="Audi", model_year=None):
    vehicle = SimpleNamespace(
        vin="WAUZZZ00000000001",
        model=model,
        title="Audi",
        model_year=model_year,
        car_type=car_type,
    )
    return AudiEntity(MagicMock(), vehicle).device_info["model"]


@pytest.mark.parametrize(
    ("car_type", "expected"),
    [("electric", "Audi (Electric)"), ("hybrid", "Audi (Hybrid)"), (None, "Audi")],
)
def test_the_car_type_is_part_of_the_model(car_type, expected):
    assert model_of(car_type) == expected


def test_the_model_year_stays_in_front():
    assert model_of("electric", model_year="2025") == "Audi (2025, Electric)"
