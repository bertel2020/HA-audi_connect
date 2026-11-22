"""Fixed, privacy-safe capability catalogue, inspired by observed myAudi identifiers.

The presence of a capability is not proof that a remote command is authorized
or functional. Raw myAudi HAR data is never imported or persisted.
"""

from __future__ import annotations

from typing import Any

CAPABILITY_GROUPS: dict[str, tuple[str, ...]] = {
    "charging": ("charging", "chargingTimers", "chargingProfiles"),
    "climate": ("climatisation", "climatisationTimers", "auxiliaryHeating"),
    "vehicle_status": (
        "measurements",
        "fuelStatus",
        "vehicleHealthInspection",
        "vehicleHealthWarnings",
        "oilLevelStatus",
    ),
    "mobility": ("tripStatistics", "parkingPosition", "b2bVDATrip"),
    "service": ("dealerAppointment", "onlineCarCare", "onlineLogBook"),
    "remote": ("access", "honkAndFlash", "vehicleWakeUp", "vehicleWakeUpTrigger"),
}


def _ids(value: Any) -> list[str]:
    """Capability identifiers the car lists: product names, not personal data."""
    if not isinstance(value, (set, frozenset, list, tuple)):
        return []
    return sorted(item for item in value if isinstance(item, str))


def _flags(value: Any) -> dict[str, bool]:
    """The car's "supports..." answers, true or false, nothing else."""
    if not isinstance(value, dict):
        return {}
    return {
        key: answer
        for key, answer in sorted(value.items())
        if isinstance(key, str)
        and key.startswith("supports")
        and isinstance(answer, bool)
    }


def snapshot_capabilities(vehicle: Any) -> dict[str, Any]:
    """Return only predeclared identifiers and a conservative tri-state verdict."""
    checker = getattr(vehicle, "has_capability", None)
    impaired = getattr(vehicle, "impaired_capabilities", frozenset()) or frozenset()
    groups: dict[str, dict[str, str]] = {}
    for family, names in CAPABILITY_GROUPS.items():
        statuses = {}
        for name in names:
            result = checker(name) if callable(checker) else None
            if result is True:
                statuses[name] = "reported_impaired" if name in impaired else "reported"
            elif result is False:
                statuses[name] = "not_reported_for_this_vehicle"
            else:
                statuses[name] = "unknown"
        groups[family] = statuses
    count = getattr(vehicle, "capabilities", None)
    return {
        "capability_ids": _ids(count),
        "impaired_capability_ids": _ids(impaired),
        "supports_flags": {
            "climatisation": _flags(getattr(vehicle, "climatisation_supports", None)),
            "chargingProfiles": _flags(
                getattr(vehicle, "charging_profiles_supports", None)
            ),
        },
        "source": "vehicle_poll_not_browser_session",
        "advertised_capability_count": len(count)
        if isinstance(count, (set, frozenset, list, tuple))
        else None,
        "groups": groups,
        "command_authorization_confirmed": False,
    }
