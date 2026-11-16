"""Every option of the freshness enum sensor has a translated state."""

import json
from pathlib import Path

import pytest

from custom_components.audiconnect.sensor import AudiVehicleFreshnessSensor

ROOT = Path(__file__).parent.parent / "custom_components" / "audiconnect"


@pytest.mark.parametrize(
    "name", ["translations/en.json", "translations/de.json", "strings.json"]
)
def test_each_freshness_option_is_translated(name):
    data = json.loads((ROOT / name).read_text(encoding="utf-8"))
    states = data["entity"]["sensor"]["vehicle_data_freshness"]["state"]
    assert set(states) == set(AudiVehicleFreshnessSensor._attr_options)
