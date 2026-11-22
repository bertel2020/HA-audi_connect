"""Repair hints: the car's online services that have ended or end soon."""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from homeassistant.util import dt as dt_util

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

WARN_DAYS = 30
EXPIRED = "services_expired"
ENDING_SOON = "services_ending_soon"
_SHOWN_SERVICES = 5


def _issue_id(kind: str, entry_id: str, vin: str) -> str:
    # The VIN is hashed: an issue id appears in logs and in the registry file.
    return f"{kind}_{entry_id}_{hashlib.sha256(vin.lower().encode()).hexdigest()[:8]}"


def _aware(value: Any) -> datetime | None:
    if isinstance(value, datetime) and value.tzinfo is not None:
        return value
    return None


def _service_names(items: list[tuple[str, datetime]]) -> str:
    names = [name for name, _ in items[:_SHOWN_SERVICES]]
    if len(items) > _SHOWN_SERVICES:
        names.append("…")
    return ", ".join(names)


def _raise_issue(
    hass: HomeAssistant,
    kind: str,
    issue_id: str,
    vehicle: Any,
    items: list[tuple[str, datetime]],
) -> None:
    ir.async_create_issue(
        hass,
        DOMAIN,
        issue_id,
        is_fixable=False,
        severity=ir.IssueSeverity.WARNING,
        translation_key=kind,
        translation_placeholders={
            "vehicle": getattr(vehicle, "title", None) or "Audi",
            "services": _service_names(items),
            "date": items[0][1].date().isoformat(),
        },
    )


def async_update_service_issues(
    hass: HomeAssistant, entry_id: str, vehicles: list[Any], now: datetime | None = None
) -> None:
    """Raise, change or clear the hint for each car, from the end dates it lists.

    One hint per car at most: "ended" wins over "ends soon". Dates without a time
    zone are ignored, because comparing them with now would only guess.
    """
    now = now or dt_util.utcnow()
    soon = now + timedelta(days=WARN_DAYS)
    for vehicle in vehicles:
        vin = getattr(vehicle, "vin", None)
        if not vin:
            continue
        expired_id = _issue_id(EXPIRED, entry_id, vin)
        soon_id = _issue_id(ENDING_SOON, entry_id, vin)
        dates = sorted(
            (
                (name, when)
                for name, value in getattr(vehicle, "service_expiry", {}).items()
                if (when := _aware(value)) is not None
            ),
            key=lambda item: item[1],
        )
        ended = [item for item in dates if item[1] <= now]
        ending = [item for item in dates if now < item[1] <= soon]

        if ended:
            _raise_issue(hass, EXPIRED, expired_id, vehicle, ended)
            ir.async_delete_issue(hass, DOMAIN, soon_id)
        elif ending:
            _raise_issue(hass, ENDING_SOON, soon_id, vehicle, ending)
            ir.async_delete_issue(hass, DOMAIN, expired_id)
        else:
            ir.async_delete_issue(hass, DOMAIN, expired_id)
            ir.async_delete_issue(hass, DOMAIN, soon_id)


def async_clear_service_issues(hass: HomeAssistant, entry_id: str) -> None:
    """Remove every hint of one entry, when the entry is removed."""
    registry = ir.async_get(hass)
    for domain, issue_id in list(registry.issues):
        if domain == DOMAIN and entry_id in issue_id:
            ir.async_delete_issue(hass, DOMAIN, issue_id)


__all__ = ["async_clear_service_issues", "async_update_service_issues"]
