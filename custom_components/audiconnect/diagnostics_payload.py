"""Redaction for what the ``probe_api`` service hands back.

The diagnostics download never carries raw API answers; this service does, on
explicit request, so VINs, positions and credentials are removed first.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from datetime import date, datetime
from typing import Any

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


def redact(value: Any, vin_pattern: re.Pattern[str] | None) -> Any:
    """Copy ``value`` into JSON-safe types with secrets and VINs removed."""
    if isinstance(value, Mapping):
        return {
            str(key): (
                REDACTED
                if str(key).lower() in _REDACT_KEYS
                else redact(item, vin_pattern)
            )
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple, set, frozenset)):
        return [redact(item, vin_pattern) for item in value]
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, str):
        return vin_pattern.sub(REDACTED_VIN, value) if vin_pattern else value
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return str(value)
