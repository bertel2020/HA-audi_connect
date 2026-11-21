"""Entity ids are built from the English names, never from the user's language."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock


from custom_components.audiconnect.audi_entity import english_object_name
from custom_components.audiconnect.number import AudiProfileChargeTarget
from custom_components.audiconnect.sensor import SENSOR_DESCRIPTIONS, AudiSensor

TRANSLATIONS = Path(__file__).parent.parent / "custom_components" / "audiconnect"


def test_a_sensor_id_comes_from_the_english_name():
    description = next(
        d for d in SENSOR_DESCRIPTIONS if d.key == "trip_totals_distance"
    )
    sensor = AudiSensor(MagicMock(), description, SimpleNamespace(vin="V1"))
    assert sensor.suggested_object_id == "Long-term trip distance"


def test_placeholders_are_filled_in():
    vehicle = SimpleNamespace(vin="V1", charging_profiles=[])
    entity = AudiProfileChargeTarget(MagicMock(), vehicle, {"id": 1, "name": "Home"})
    assert "Home" in entity.suggested_object_id


def test_an_unknown_key_falls_back():
    assert english_object_name("sensor", "no_such_key", None) is None
    assert english_object_name(None, None, None) is None


def test_every_translated_entity_has_an_english_name():
    """Without one, its id would follow the user's language again."""
    en = json.loads((TRANSLATIONS / "translations/en.json").read_text())["entity"]
    de = json.loads((TRANSLATIONS / "translations/de.json").read_text())["entity"]
    for domain, keys in de.items():
        for key, value in keys.items():
            if isinstance(value, dict) and "name" in value:
                assert english_object_name(domain, key, {"profile": "x"}), (
                    domain,
                    key,
                )
                assert key in en[domain], (domain, key)
