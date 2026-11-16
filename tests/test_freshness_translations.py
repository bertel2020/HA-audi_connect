"""Every option of the freshness enum sensor has a translated state."""

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from custom_components.audiconnect.freshness import vehicle_freshness

# Every value vehicle_freshness can return, one input per branch.
OPTIONS = {
    vehicle_freshness(None),
    vehicle_freshness(
        datetime(2026, 1, 1, 12, 0, tzinfo=UTC),
        now=datetime(2026, 1, 1, 12, 10, tzinfo=UTC),
    ),
    vehicle_freshness(
        datetime(2026, 1, 1, 12, 0, tzinfo=UTC),
        now=datetime(2026, 1, 1, 13, 0, tzinfo=UTC),
    ),
    vehicle_freshness(
        datetime(2026, 1, 1, 12, 0, tzinfo=UTC),
        now=datetime(2026, 1, 1, 15, 0, tzinfo=UTC),
    ),
}
ROOT = Path(__file__).parent.parent / "custom_components" / "audiconnect"


@pytest.mark.parametrize(
    "name", ["translations/en.json", "translations/de.json", "strings.json"]
)
def test_each_freshness_option_is_translated(name):
    data = json.loads((ROOT / name).read_text(encoding="utf-8"))
    states = data["entity"]["sensor"]["vehicle_data_freshness"]["state"]
    assert set(states) == OPTIONS
