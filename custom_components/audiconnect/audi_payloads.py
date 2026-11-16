"""Pure builders for the request bodies sent to the Audi / CARIAD API."""

from __future__ import annotations

from typing import Any


# The settings the car round-trips. Anything outside this set is rejected rather
# than sent, so a typo becomes an error here instead of a field the car ignores.
_CLIMATISATION_SETTING_FIELDS = frozenset(
    {
        "targetTemperature",
        "targetTemperature_C",
        "targetTemperature_F",
        "targetTemperatureUnit",
        "climatisationWithoutExternalPower",
        "climatizationAtUnlock",
        "windowHeatingEnabled",
        "heaterSource",
        "zoneFrontLeftEnabled",
        "zoneFrontRightEnabled",
        "zoneRearLeftEnabled",
        "zoneRearRightEnabled",
    }
)


# Reported by the car but not part of what it takes back. Sent anyway they gave
# the A6 a 502 (Audi error 2105) on every write, so the body carries only the
# fields in _CLIMATISATION_SETTING_FIELDS, without the redundant Fahrenheit twin
# of the Celsius target.
_NOT_SENT = frozenset({"targetTemperature_F"})


# How much of the stored settings goes back with a change. The A6 answers the
# full object with 502 (error 2105), so the variants exist to find which part it
# refuses: "full" is the whole writable object, "without_window_heating" leaves
# out the one setting the car says it does not support, and "single_field"
# sends only what changes.
CLIMATISATION_WRITE_VARIANTS = ("full", "without_window_heating", "single_field")


def build_climatisation_settings_update(
    value: dict, *, variant: str = "full", **changes: Any
) -> dict:
    """Pure read-modify-write core for the climatisation settings.

    `value` is climatisation.climatisationSettings.value as the car reports it.
    Returns the body for PUT climatisation/settings: every field the car gave
    back, with the named ones changed.

    Read-modify-write for the same reason the charging profile write is: the
    endpoint takes the whole object, so sending one field would drop the rest.
    A toggle of a heated seat must not clear the target temperature or the
    heater source.

    Only the writable settings are sent back. carCapturedTimestamp, unitInCar,
    climatisationMode and the Fahrenheit twin of the target are reports from the
    car, not settings, and echoing them back is meaningless at best.
    """
    if variant not in CLIMATISATION_WRITE_VARIANTS:
        raise ValueError(f"Unknown write variant: {variant!r}")
    if variant != "single_field" and (not isinstance(value, dict) or not value):
        raise ValueError("No climatisation settings to update")

    unknown = set(changes) - set(_CLIMATISATION_SETTING_FIELDS)
    if unknown:
        raise ValueError(f"Not climatisation settings: {sorted(unknown)}")

    if variant == "single_field":
        return dict(changes)
    body = {
        k: v
        for k, v in value.items()
        if k in _CLIMATISATION_SETTING_FIELDS and k not in _NOT_SENT
    }
    if variant == "without_window_heating":
        body.pop("windowHeatingEnabled", None)
    body.update(changes)
    return body


def build_profile_update(value: dict, profile_id, target_soc: int) -> tuple[int, dict]:
    """Pure read-modify-write core for a location charging profile.

    `value` is chargingProfiles.chargingProfilesStatus.value as the car reports
    it. Returns (resolved_profile_id, put_body) where put_body is exactly what
    goes on the wire: {"profile": <the whole profile, one field changed>}.

    Kept pure and module-level so the field-preservation and profile-selection
    logic is testable against a real payload without standing up the service.
    """
    if not (20 <= target_soc <= 100):
        raise ValueError("Target state of charge must be between 20 and 100 percent")

    profiles = (value or {}).get("profiles") or []
    if profile_id is None:
        profile_id = (value or {}).get("vehiclePositionedInProfileID")
    profile = next((p for p in profiles if p.get("id") == profile_id), None)
    if profile is None:
        present = [p.get("id") for p in profiles]
        raise ValueError(
            f"No charging profile with id {profile_id} (present: {present})"
        )

    # Change exactly one field; round-trip the rest, position included.
    updated = dict(profile)
    updated["targetSOC_pct"] = target_soc
    return profile_id, {"profile": updated}


# Fields the start body carries straight over from the car's stored settings.
# Only those the car actually reports are sent: a vehicle with no rear zones
# never receives zoneRear* keys, which is also the shape the myAudi app sends.
_START_PASSTHROUGH = (
    "climatisationWithoutExternalPower",
    "climatizationAtUnlock",
    "windowHeatingEnabled",
    "zoneFrontLeftEnabled",
    "zoneFrontRightEnabled",
    "zoneRearLeftEnabled",
    "zoneRearRightEnabled",
    "heaterSource",
)

# Caller parameter -> the field it overrides in the start body.
_START_OVERRIDES = {
    "climatisation_at_unlock": "climatizationAtUnlock",
    "glass_heating": "windowHeatingEnabled",
    "seat_fl": "zoneFrontLeftEnabled",
    "seat_fr": "zoneFrontRightEnabled",
    "seat_rl": "zoneRearLeftEnabled",
    "seat_rr": "zoneRearRightEnabled",
}

# What the start body was built from before it read the car's settings (2.4.0).
# Used only when the car reports no climatisationSettings at all (#873): there is
# nothing stored to preserve then, and refusing to start leaves no way to start
# climatisation with any settings from Home Assistant.
_START_DEFAULTS = {
    "climatisationWithoutExternalPower": True,
    "climatizationAtUnlock": False,
    "windowHeatingEnabled": False,
    "zoneFrontLeftEnabled": False,
    "zoneFrontRightEnabled": False,
    "zoneRearLeftEnabled": False,
    "zoneRearRightEnabled": False,
}


def build_climatisation_start_body(settings: dict, **params: Any) -> dict:
    """Pure read-modify-write core for climatisation/start.

    `settings` is climatisation.climatisationSettings.value as the car reports
    it. Returns the body for POST climatisation/start: the car's own settings,
    with only the parameters the caller actually supplied changed.

    Built this way because the endpoint REPLACES rather than merges. The
    previous body was assembled from constants, so every parameter the caller
    omitted went out as bool(None), which is False. Starting climatisation from
    the climate entity, which passes only a target temperature, therefore wiped
    the stored window heating, every seat zone and climatisation-at-unlock.
    Found on a live vehicle 2026-09-12: the myAudi app's own start kept those
    settings and ours cleared them, on the same car minutes apart.

    A parameter left as None means "leave whatever the car has", never False.

    Some cars report the climatisation status but no settings at all (#873, a
    2024 Q8 Sportback e-tron: selectivestatus has no climatisationSettings).
    Then there is nothing to preserve, so the body is built from the defaults
    the start used before this became a read-modify-write, and an unsupplied
    parameter means False again. Raising here instead made every start with
    settings fail before anything was sent.
    """
    if not isinstance(settings, dict) or not settings:
        settings = dict(_START_DEFAULTS)

    body: dict[str, Any] = {
        key: settings[key] for key in _START_PASSTHROUGH if key in settings
    }

    temp_f = params.get("temp_f")
    temp_c = params.get("temp_c")
    if temp_f is not None:
        target: Any = int((temp_f - 32) * (5 / 9))
    elif temp_c is not None:
        target = int(temp_c)
    else:
        # Unchanged, so pass the car's own value through rather than rounding
        # it: the car stores half degrees and we were not asked to touch this.
        target = settings.get("targetTemperature_C")
    body["targetTemperature"] = 21 if target is None else target
    body["targetTemperatureUnit"] = "celsius"

    # Unchanged from before this became a read-modify-write: #771 fixed a literal
    # null going on the wire, and "comfort" is the value that has been accepted
    # on real vehicles. The car does not report a mode in its settings, so there
    # is nothing stored to preserve and no evidence that omitting it is safe.
    mode = params.get("climatisation_mode") or settings.get("climatisationMode")
    body["climatisationMode"] = mode or "comfort"

    for name, field in _START_OVERRIDES.items():
        value = params.get(name)
        if value is not None:
            body[field] = bool(value)

    return body
