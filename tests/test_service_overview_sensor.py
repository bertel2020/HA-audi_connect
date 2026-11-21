"""The service overview shows the maintenance figures the car reports."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace as NS

from custom_components.audiconnect.sensor import AudiServiceOverviewSensor


class Coordinator:
    last_update_success = True


def make():
    car = NS(
        vin="TESTVIN00000000001",
        title="Audi Q8",
        model="Q8",
        model_year="2023",
        service_inspection_time=90,
        service_inspection_distance=12000,
        oil_change_time=60,
        oil_change_distance=7000,
    )
    entry = NS(options={"scan_interval": 15})
    return car, entry


def test_service_overview_follows_the_cars_inspection_and_oil_figures():
    car, entry = make()
    summary = AudiServiceOverviewSensor(Coordinator(), car, entry)
    assert summary.available
    assert summary.native_value == "scheduled"
    assert summary.extra_state_attributes["inspection_due_days"] == 90
    car.service_inspection_time = 14
    assert summary.native_value == "due_soon"
    car.oil_change_time = -1
    assert summary.native_value == "overdue"
    car.service_inspection_time = None
    car.oil_change_time = None
    assert summary.native_value == "unknown"


def test_the_overview_has_no_locally_entered_fields():
    car, entry = make()
    attributes = AudiServiceOverviewSensor(
        Coordinator(), car, entry
    ).extra_state_attributes
    assert not [key for key in attributes if key.endswith("_local")]
    assert "appointment_source" not in attributes


def test_the_options_form_no_longer_offers_the_local_dealer_steps():
    root = Path(__file__).resolve().parents[1] / "custom_components/audiconnect"
    for name in ("strings.json", "translations/en.json", "translations/nl.json"):
        data = json.loads((root / name).read_text())
        steps = data["options"]["step"]
        assert "edit_local_dealer" not in steps["init"]["data"]
        assert "dealer_vehicle" not in steps
        assert "dealer" not in steps
        assert "experimental_commands" in steps["init"]["data"]
        assert "set_local_dealer" not in data["services"]
