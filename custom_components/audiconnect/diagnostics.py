"""Diagnostics for Audi Connect: what the car actually reports.

Home Assistant's "Download diagnostics" button lands here. The point is to see
the raw ``selectivestatus`` answer for each vehicle, so a missing or odd entity
can be traced to what the API returned instead of guessed at. VINs, positions
and credentials are removed before anything leaves the instance.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from datetime import date, datetime
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .audi_services import SELECTIVESTATUS_JOBS

REDACTED = "**REDACTED**"
REDACTED_VIN = "**REDACTED_VIN**"

# Compared case-insensitively, at any depth.
_REDACT_KEYS = frozenset(
    {
        "vin",
        "latitude",
        "longitude",
        "lat",
        "lon",
        "position",
        "access_token",
        "refresh_token",
        "id_token",
        "token",
        "username",
        "password",
        "spin",
        "email",
        "licenseplate",
        "nickname",
        "vehiclenickname",
    }
)


def _redact(value: Any, vin_pattern: re.Pattern[str] | None) -> Any:
    """Copy ``value`` into JSON-safe types with secrets and VINs removed."""
    if isinstance(value, Mapping):
        return {
            str(key): (
                REDACTED
                if str(key).lower() in _REDACT_KEYS
                else _redact(item, vin_pattern)
            )
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_redact(item, vin_pattern) for item in value]
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, str):
        return vin_pattern.sub(REDACTED_VIN, value) if vin_pattern else value
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return str(value)


def _summarise_jobs(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Which jobs answered, which errored, and which the car left out."""
    jobs: dict[str, Any] = {}
    for job, statuses in payload.items():
        if not isinstance(statuses, Mapping):
            jobs[job] = "unexpected"
            continue
        jobs[job] = {
            name: (
                "error"
                if isinstance(body, Mapping) and "error" in body
                else "value"
                if isinstance(body, Mapping) and "value" in body
                else "other"
            )
            for name, body in statuses.items()
        }
    return {
        "answered": jobs,
        "not_returned": sorted(SELECTIVESTATUS_JOBS - set(payload)),
    }


def _vehicle_diagnostics(vehicle: Any) -> dict[str, Any]:
    vin = getattr(vehicle, "vin", None)
    pattern = re.compile(re.escape(vin), re.IGNORECASE) if vin else None
    payload = getattr(vehicle, "last_status_payload", None)
    inner = getattr(vehicle, "_vehicle", None)
    return {
        "vin": f"{'*' * (len(vin) - 4)}{vin[-4:]}" if vin else None,
        "jobs": _summarise_jobs(payload) if isinstance(payload, Mapping) else None,
        "selectivestatus": _redact(payload, pattern),
        "parsed_fields": _redact(getattr(inner, "fields", None), pattern),
        "parsed_state": _redact(getattr(inner, "state", None), pattern),
    }


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    runtime_data = getattr(entry, "runtime_data", None)
    vehicles = (
        [
            data.vehicle
            for data in runtime_data.account.config_vehicles
            if data.vehicle is not None
        ]
        if runtime_data is not None
        else []
    )
    return {
        "entry": {
            "data": _redact(entry.data, None),
            "options": _redact(entry.options, None),
        },
        "vehicles": [_vehicle_diagnostics(vehicle) for vehicle in vehicles],
    }
