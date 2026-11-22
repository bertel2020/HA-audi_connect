"""The diagnostics say which trip figures are held, never what they are."""

from __future__ import annotations

from datetime import UTC, datetime

from custom_components.audiconnect.diagnostics import _trip_view


def test_a_complete_block_is_described_without_its_values():
    block = {
        "tripEndTimestamp": "2026-11-15T17:36:15+00:00",
        "mileage_km": 4711,
        "travelTime": 4712,
        "averageElectricConsumption": 47.13,
        "averageSpeed_kmph": 4714,
        "totalElectricConsumption_kwh": 47.15,
    }
    view = _trip_view(block)

    assert view["held"] is True
    assert view["end_timestamp_readable"] is True
    assert view["end_timestamp_type"] == "str"
    assert "mileage_km" in view["fields_present"]
    text = repr(view)
    assert "4711" not in text and "17:36" not in text and "47.13" not in text


def test_a_missing_block_is_reported_as_not_held():
    assert _trip_view(None) == {"held": False}
    assert _trip_view("junk") == {"held": False}


def test_an_unreadable_end_time_is_visible():
    for end in (
        "not a time",
        "2026-11-15T17:36:15",
        123,
        None,
        datetime(2026, 11, 15, 17, 36, 15),
    ):
        view = _trip_view({"tripEndTimestamp": end, "mileage_km": 1})
        assert view["end_timestamp_readable"] is False


def test_unknown_fields_are_not_listed():
    view = _trip_view({"id": "secret-id", "mileage_km": 1})
    assert view["fields_present"] == ["mileage_km"]


def test_a_parsed_end_time_with_a_time_zone_is_readable():
    # The loader turns timestamps into datetimes, so this is what the car really sends.
    end = datetime(2026, 11, 15, 17, 36, 15, tzinfo=UTC)
    view = _trip_view({"tripEndTimestamp": end, "mileage_km": 1})
    assert view["end_timestamp_readable"] is True
    assert view["end_timestamp_type"] == "datetime"
    assert "17:36" not in repr(view)
