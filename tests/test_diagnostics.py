"""Diagnostics: the raw selectivestatus answer, with nothing identifying left in it."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from types import SimpleNamespace

from custom_components.audiconnect.audi_services import SELECTIVESTATUS_JOBS
from custom_components.audiconnect.diagnostics import (
    REDACTED,
    REDACTED_VIN,
    async_get_config_entry_diagnostics,
)

VIN = "WAUZZZF2XPN012345"


def _vehicle(payload):
    inner = SimpleNamespace(
        fields={"TOTAL_RANGE": "300"},
        state={
            "position": {"latitude": 48.1, "longitude": 11.5},
            "last_update_time": datetime(2026, 11, 16, tzinfo=UTC),
        },
    )
    return SimpleNamespace(vin=VIN, last_status_payload=payload, _vehicle=inner)


def _entry(vehicles):
    account = SimpleNamespace(
        config_vehicles=[SimpleNamespace(vehicle=v) for v in vehicles]
    )
    return SimpleNamespace(
        data={"region": "DE", "refresh_token": "secret", "spin": "1234"},
        options={"scan_interval": 15},
        runtime_data=SimpleNamespace(account=account),
    )


PAYLOAD = {
    "access": {
        "accessStatus": {
            "value": {
                "carCapturedTimestamp": datetime(2026, 11, 16, tzinfo=UTC),
                "doorLockStatus": "locked",
                "note": f"vin {VIN.lower()} here",
            }
        }
    },
    "charging": {"chargingStatus": {"error": {"message": "boom"}}},
    "parkingPosition": {"value": {"latitude": 48.1, "longitude": 11.5}},
}


async def test_the_payload_is_json_safe_and_has_no_identifying_data() -> None:
    result = await async_get_config_entry_diagnostics(None, _entry([_vehicle(PAYLOAD)]))

    text = json.dumps(result)  # datetimes must already be strings
    assert VIN not in text and VIN.lower() not in text
    assert "48.1" not in text and "11.5" not in text
    assert "secret" not in text and "1234" not in text
    assert result["entry"]["data"]["refresh_token"] == REDACTED
    assert result["entry"]["data"]["region"] == "DE"
    assert result["entry"]["options"] == {"scan_interval": 15}

    (vehicle,) = result["vehicles"]
    assert vehicle["vin"].endswith(VIN[-4:]) and VIN[:-4] not in vehicle["vin"]
    status = vehicle["selectivestatus"]["access"]["accessStatus"]["value"]
    assert status["doorLockStatus"] == "locked"
    assert status["note"] == f"vin {REDACTED_VIN} here"
    assert vehicle["parsed_fields"] == {"TOTAL_RANGE": "300"}


async def test_the_job_summary_says_what_answered_errored_or_is_missing() -> None:
    result = await async_get_config_entry_diagnostics(None, _entry([_vehicle(PAYLOAD)]))
    jobs = result["vehicles"][0]["jobs"]

    assert jobs["answered"]["access"] == {"accessStatus": "value"}
    assert jobs["answered"]["charging"] == {"chargingStatus": "error"}
    assert "access" not in jobs["not_returned"]
    assert set(jobs["not_returned"]) == SELECTIVESTATUS_JOBS - {
        "access",
        "charging",
        "parkingPosition",
    }


async def test_a_vehicle_that_has_not_been_polled_yet_does_not_break_it() -> None:
    result = await async_get_config_entry_diagnostics(None, _entry([_vehicle(None)]))
    vehicle = result["vehicles"][0]

    assert vehicle["jobs"] is None and vehicle["selectivestatus"] is None


async def test_an_entry_that_is_not_loaded_still_reports_its_configuration() -> None:
    entry = _entry([])
    entry.runtime_data = None
    result = await async_get_config_entry_diagnostics(None, entry)

    assert result["vehicles"] == [] and result["entry"]["data"]["region"] == "DE"
