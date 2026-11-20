"""What the probe_api service returns carries nothing identifying."""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime

from custom_components.audiconnect.diagnostics_payload import (
    REDACTED,
    REDACTED_VIN,
    redact,
)

VIN = "WAUZZZF2XPN000001"

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
    "parkingPosition": {"value": {"latitude": 48.1, "longitude": 11.5}},
}


def test_the_payload_is_json_safe_and_has_no_identifying_data() -> None:
    result = redact(PAYLOAD, re.compile(re.escape(VIN), re.IGNORECASE))

    text = json.dumps(result)  # datetimes must already be strings
    assert VIN not in text and VIN.lower() not in text
    assert "48.1" not in text and "11.5" not in text
    status = result["access"]["accessStatus"]["value"]
    assert status["doorLockStatus"] == "locked"
    assert status["note"] == f"vin {REDACTED_VIN} here"


def test_credentials_are_redacted_at_any_depth() -> None:
    cleaned = redact(
        {"data": {"refresh_token": "secret", "spin": "1234", "region": "DE"}}, None
    )

    assert cleaned["data"]["refresh_token"] == REDACTED
    assert cleaned["data"]["spin"] == REDACTED
    assert cleaned["data"]["region"] == "DE"
