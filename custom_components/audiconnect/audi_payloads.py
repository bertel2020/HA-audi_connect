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
        "climatisationMode",
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
CLIMATISATION_WRITE_VARIANTS = (
    "full",
    "without_window_heating",
    "single_field",
    "full_json",
    "app_dto",
)
# Variants sent with Content-Type application/json. The myAudi app always does,
# our other writes carry aiohttp's default text/plain for a string body.
JSON_CONTENT_VARIANTS = frozenset({"full_json", "app_dto"})

# Fields the myAudi app's request object carries (SetClimatisationSettings,
# read from app 5.9.0). All twelve are always part of it; it names the target
# temperature "targetTemperature" with a separate unit, not "targetTemperature_C".
_APP_DTO_FIELDS = (
    "climatisationWithoutExternalPower",
    "climatizationAtUnlock",
    "windowHeatingEnabled",
    "zoneFrontLeftEnabled",
    "zoneFrontRightEnabled",
    "zoneRearLeftEnabled",
    "zoneRearRightEnabled",
    "climatisationMode",
)


def build_climatisation_settings_update(
    value: dict, *, variant: str = "app_dto", **changes: Any
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
    if variant == "app_dto":
        body = {k: value[k] for k in _APP_DTO_FIELDS if value.get(k) is not None}
        temperature = value.get("targetTemperature_C", value.get("targetTemperature"))
        if temperature is not None:
            body["targetTemperature"] = temperature
            body["targetTemperatureUnit"] = "celsius"
        body.update(changes)
        return body
    body = {
        k: v
        for k, v in value.items()
        if k in _CLIMATISATION_SETTING_FIELDS and k not in _NOT_SENT
    }
    if variant == "without_window_heating":
        body.pop("windowHeatingEnabled", None)
    body.update(changes)
    return body


# The profile fields a caller may change. Anything else is refused rather than
# sent, so a typo cannot become a field the car silently drops.
_PROFILE_CHANGEABLE = frozenset({"targetSOC_pct", "maxChargingCurrent"})
CHARGING_CURRENTS = ("max", "reduced")


def build_profile_change(value: dict, profile_id, **changes: Any) -> tuple[int, dict]:
    """Pure read-modify-write core for a location charging profile.

    `value` is chargingProfiles.chargingProfilesStatus.value as the car reports
    it. Returns (resolved_profile_id, put_body) where put_body is exactly what
    goes on the wire: {"profile": <the whole profile, the named fields changed>}.
    The app's request is the same shape (PUT charging/profiles).

    Kept pure and module-level so the field-preservation and profile-selection
    logic is testable against a real payload without standing up the service.
    """
    unknown = set(changes) - _PROFILE_CHANGEABLE
    if unknown:
        raise ValueError(f"Not changeable profile settings: {sorted(unknown)}")
    if "targetSOC_pct" in changes and not (20 <= changes["targetSOC_pct"] <= 100):
        raise ValueError("Target state of charge must be between 20 and 100 percent")
    if (
        "maxChargingCurrent" in changes
        and changes["maxChargingCurrent"] not in CHARGING_CURRENTS
    ):
        raise ValueError(f"Charging current must be one of {CHARGING_CURRENTS}")

    profiles = (value or {}).get("profiles") or []
    if profile_id is None:
        profile_id = (value or {}).get("vehiclePositionedInProfileID")
    profile = next((p for p in profiles if p.get("id") == profile_id), None)
    if profile is None:
        present = [p.get("id") for p in profiles]
        raise ValueError(
            f"No charging profile with id {profile_id} (present: {present})"
        )

    # Change only what was asked; round-trip the rest, position included.
    updated = dict(profile)
    updated.update(changes)
    return profile_id, {"profile": updated}


def build_profile_update(value: dict, profile_id, target_soc: int) -> tuple[int, dict]:
    """The target-SoC change, kept under its old name."""
    return build_profile_change(value, profile_id, targetSOC_pct=target_soc)


WEEKDAYS = (
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
)


def _hhmm(value: str) -> tuple[int, int]:
    try:
        hours, minutes = (int(part) for part in value.strip().split(":")[:2])
    except ValueError as err:
        raise ValueError(f"Time must look like 07:30, got {value!r}") from err
    if not (0 <= hours < 24 and 0 <= minutes < 60):
        raise ValueError(f"Time out of range: {value!r}")
    return hours, minutes


def build_climatisation_timer(
    time_local: str,
    days: list[str],
    *,
    repeat: bool,
    enabled: bool,
    utc_offset_minutes: int,
) -> dict:
    """The body of POST departure/{vin}/climatisation/timers, as the app sends it.

    The app gives each timer both its start in UTC (startTime) and in the car's
    local clock (startTimeLocal), as "HH:mm". A recurring timer names its days
    as {"mondays": true, ...}, a single timer one day as "Monday".
    """
    hours, minutes = _hhmm(time_local)
    chosen = [d.lower() for d in days]
    unknown = [d for d in chosen if d not in WEEKDAYS]
    if unknown or not chosen:
        raise ValueError(f"Days must be some of {WEEKDAYS}, got {days!r}")
    utc_total = (hours * 60 + minutes - utc_offset_minutes) % (24 * 60)
    times = {
        "startTime": f"{utc_total // 60:02d}:{utc_total % 60:02d}",
        "startTimeLocal": f"{hours:02d}:{minutes:02d}",
    }
    if repeat:
        frequency = {
            "recurringTimer": {
                "recurringOn": {f"{d}s": d in chosen for d in WEEKDAYS},
                **times,
            }
        }
    else:
        if len(chosen) != 1:
            raise ValueError("A single timer takes exactly one day")
        frequency = {"singleTimer": {"occurringOn": chosen[0].capitalize(), **times}}
    return {"timer": {"enabled": enabled, **frequency}}


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
