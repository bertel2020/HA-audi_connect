"""State properties of a vehicle, read from the data its updates collected."""

from __future__ import annotations

from collections.abc import Callable
from datetime import timedelta
from typing import Any

from .util import parse_float, parse_int

_INACTIVE_PREHEATER_STATES = frozenset({"off", "invalid", "unsupported", "error", ""})
_UNSUPPORTED = "unsupported"
_INVALID = "invalid"

_STATE = "state"
_FIELDS = "fields"


# "Is it supported?" tests. They deliberately keep the exact return values the
# hand-written properties had (True/None versus True/False): entities only look
# at truthiness, but a few tests pin the exact value.
def _truthy(v: Any) -> bool | None:
    return True if v else None


def _valid(v: Any) -> bool | None:
    """Present and not Audi's ``invalid``, which means "no reading", not a state."""
    return True if v and v != _INVALID else None


def _truthy_known(v: Any) -> bool | None:
    return True if v and v != _UNSUPPORTED else None


def _not_none(v: Any) -> bool | None:
    return True if v is not None else None


def _known_not_none(v: Any) -> bool | None:
    return True if v is not None and v != _UNSUPPORTED else None


def _truthy_int(v: Any) -> bool | None:
    return True if v and parse_int(v) else None


def _is_not_none(v: Any) -> bool:
    return v is not None


def _is_known(v: Any) -> bool:
    return v is not None and v != _UNSUPPORTED


def _int_parses(v: Any) -> bool:
    return parse_int(v) is not None


def _is_bool(v: Any) -> bool:
    return isinstance(v, bool)


def _is_dict(v: Any) -> bool:
    return isinstance(v, dict) and bool(v)


def _is_list(v: Any) -> bool:
    return isinstance(v, list)


def _is_numeric_level(v: Any) -> bool:
    return not isinstance(v, bool) and v is not None


def _raw(v: Any) -> Any:
    return v


# Value conversions.
def _is_not_3(v: Any) -> bool:
    return v != "3"


def _is_not_2(v: Any) -> bool:
    return v != "2"


def _is_connected(v: Any) -> bool:
    return v not in ("invalid", "disconnected")


def _is_not_locked(v: Any) -> bool:
    return v != "locked"


def _float_or_minus_one(v: Any) -> float | int | None:
    try:
        return parse_float(v)
    except ValueError:
        return -1


# A capability a car may announce under another id.
_CAPABILITY_ALIASES: dict[str, frozenset[str]] = {
    "climatisationTimers": frozenset({"departureTimers"}),
    "chargingTimers": frozenset({"departureTimers"}),
}


class _Field:
    """One value read from the vehicle's ``state`` or ``fields`` dict.

    Declaring ``name = _Field(...)`` in the class body creates two read-only
    properties: ``name`` and ``name_supported``. The value is None unless the
    car reports it (``gated``); ``gated=False`` returns the stored value as is.
    """

    def __init__(
        self,
        source: str,
        key: str,
        present: Callable[[Any], Any],
        convert: Callable[[Any], Any] | None = None,
        *,
        gated: bool = True,
        doc: str | None = None,
    ) -> None:
        self._source = source
        self._key = key
        self._present = present
        self._convert = convert
        self._gated = gated
        self._doc = doc

    def __set_name__(self, owner: type, name: str) -> None:
        source, key, present = self._source, self._key, self._present
        convert, gated = self._convert, self._gated

        def raw(obj: Any) -> Any:
            return getattr(obj._vehicle, source).get(key)

        def supported(obj: Any) -> Any:
            return present(raw(obj))

        def value(obj: Any) -> Any:
            v = raw(obj)
            if gated and not present(v):
                return None
            return v if convert is None else convert(v)

        setattr(owner, name, property(value, doc=self._doc))
        setattr(owner, f"{name}_supported", property(supported))


class AudiVehicleProperties:
    """Read-only views of ``self._vehicle.state``; mixed into AudiConnectVehicle."""

    # Declarative properties: each line defines ``name`` and ``name_supported``.
    # Explicit properties below cover everything that needs more than one key.
    last_update_time = _Field(_STATE, "last_update_time", _truthy)
    service_inspection_time = _Field(
        _FIELDS, "MAINTENANCE_INTERVAL_TIME_TO_INSPECTION", _int_parses, int
    )
    service_inspection_distance = _Field(
        _FIELDS, "MAINTENANCE_INTERVAL_DISTANCE_TO_INSPECTION", _int_parses, int
    )
    service_adblue_distance = _Field(_FIELDS, "ADBLUE_RANGE", _int_parses, int)
    oil_change_time = _Field(
        _FIELDS, "MAINTENANCE_INTERVAL_TIME_TO_OIL_CHANGE", _int_parses, int
    )
    oil_change_distance = _Field(
        _FIELDS, "MAINTENANCE_INTERVAL_DISTANCE_TO_OIL_CHANGE", _int_parses, int
    )
    oil_level = _Field(
        _FIELDS, "OIL_LEVEL_DIPSTICKS_PERCENTAGE", _is_numeric_level, parse_float
    )
    braking_status = _Field(_FIELDS, "BRAKING_STATUS", _truthy, _is_not_2)
    mileage = _Field(_FIELDS, "UTC_TIME_AND_KILOMETER_STATUS", _truthy_int, parse_int)
    range = _Field(_FIELDS, "TOTAL_RANGE", _int_parses, parse_int)
    tank_level = _Field(_FIELDS, "TANK_LEVEL_IN_PERCENTAGE", _int_parses, parse_int)
    position = _Field(_STATE, "position", _truthy)

    @property
    def window_open_percent(self) -> dict[str, int | float]:
        """How far each window is open, by the car's own window name."""
        state = self._vehicle.state
        return {
            key.removeprefix("windowOpenPct_"): value
            for key, value in state.items()
            if key.startswith("windowOpenPct_")
            and isinstance(value, (int, float))
            and not isinstance(value, bool)
        }

    @property
    def window_open_pct_front_left(self):
        return self.window_open_percent.get("frontLeft")

    @property
    def window_open_pct_front_right(self):
        return self.window_open_percent.get("frontRight")

    @property
    def window_open_pct_rear_left(self):
        return self.window_open_percent.get("rearLeft")

    @property
    def window_open_pct_rear_right(self):
        return self.window_open_percent.get("rearRight")

    left_front_window_open = _Field(_FIELDS, "STATE_LEFT_FRONT_WINDOW", _raw, _is_not_3)
    right_front_window_open = _Field(
        _FIELDS, "STATE_RIGHT_FRONT_WINDOW", _raw, _is_not_3
    )
    left_rear_window_open = _Field(_FIELDS, "STATE_LEFT_REAR_WINDOW", _raw, _is_not_3)
    right_rear_window_open = _Field(_FIELDS, "STATE_RIGHT_REAR_WINDOW", _raw, _is_not_3)
    sun_roof = _Field(_FIELDS, "STATE_SUN_ROOF_MOTOR_COVER", _raw, _is_not_3)
    roof_cover = _Field(_FIELDS, "STATE_ROOF_COVER_WINDOW", _raw, _is_not_3)
    left_front_door_open = _Field(
        _FIELDS, "OPEN_STATE_LEFT_FRONT_DOOR", _raw, _is_not_3
    )
    right_front_door_open = _Field(
        _FIELDS, "OPEN_STATE_RIGHT_FRONT_DOOR", _raw, _is_not_3
    )
    left_rear_door_open = _Field(_FIELDS, "OPEN_STATE_LEFT_REAR_DOOR", _raw, _is_not_3)
    right_rear_door_open = _Field(
        _FIELDS, "OPEN_STATE_RIGHT_REAR_DOOR", _raw, _is_not_3
    )
    trunk_unlocked = _Field(_FIELDS, "LOCK_STATE_TRUNK_LID", _truthy, _is_not_2)
    trunk_open = _Field(_FIELDS, "OPEN_STATE_TRUNK_LID", _truthy, _is_not_3)
    hood_open = _Field(_FIELDS, "OPEN_STATE_HOOD", _truthy, _is_not_3)
    charging_state = _Field(_STATE, "chargingState", _truthy)
    charging_mode = _Field(_STATE, "chargeMode", _is_known)
    preferred_charge_mode = _Field(
        _STATE,
        "preferredChargeMode",
        _is_known,
        doc="Return the charge mode the car is set to, not the one in progress.",
    )
    energy_flow = _Field(_STATE, "energyFlow", _not_none)
    charging_type = _Field(_STATE, "chargeType", _truthy_known)
    max_charge_current = _Field(
        _STATE, "maxChargeCurrent", _not_none, _float_or_minus_one
    )
    actual_charge_rate = _Field(
        _STATE, "actualChargeRate", _not_none, _float_or_minus_one
    )
    charging_power = _Field(_STATE, "chargingPower", _not_none, _float_or_minus_one)
    primary_engine_type = _Field(_STATE, "engineTypeFirstEngine", _truthy_known)
    secondary_engine_type = _Field(_STATE, "engineTypeSecondEngine", _truthy_known)
    primary_engine_range = _Field(_STATE, "primaryEngineRange", _truthy_known)
    primary_engine_range_percent = _Field(
        _STATE, "primaryEngineRangePercent", _truthy_known
    )
    secondary_engine_range = _Field(_STATE, "secondaryEngineRange", _known_not_none)
    car_type = _Field(_STATE, "carType", _truthy_known)
    secondary_engine_range_percent = _Field(
        _STATE, "secondaryEngineRangePercent", _truthy_known
    )
    hybrid_range = _Field(_STATE, "hybridRange", _truthy_known)

    @property
    def has_non_electric_engine(self) -> bool:
        """False only when the car says it is purely electric.

        A combustion or hybrid engine has a fuel range and a second engine to
        report; a battery-electric car has neither, and its "primary engine"
        range and level only repeat the main range and charge. An unknown car
        type counts as "might have one", so nothing disappears on a guess.
        """
        return str(getattr(self, "car_type", None) or "").lower() != "electric"

    state_of_charge = _Field(_STATE, "stateOfCharge", _int_parses, parse_int)
    target_state_of_charge = _Field(
        _STATE, "targetstateOfCharge", _int_parses, parse_int
    )
    active_charging_profile_target_soc = _Field(
        _STATE,
        "activeChargingProfileTargetSoc",
        _int_parses,
        parse_int,
        doc="Return the target SoC of the location profile the car is parked in.\n\nThis is the limit the car actually charges to. target_state_of_charge is\nthe global setting, which a location profile overrides, so the two\ndisagree whenever a profile is in force (upstream #722).",
    )
    active_charging_profile_name = _Field(
        _STATE,
        "activeChargingProfileName",
        _is_not_none,
        doc="Return the name of the charging profile in force at this location.",
    )
    active_charging_profile_id = _Field(
        _STATE, "activeChargingProfileId", _int_parses, parse_int
    )
    active_charging_profile_min_soc = _Field(
        _STATE,
        "activeChargingProfileMinSoc",
        _int_parses,
        parse_int,
        doc="Return the minimum SoC the profile tops up to regardless of schedule.",
    )
    active_charging_profile_max_current = _Field(
        _STATE,
        "activeChargingProfileMaxCurrent",
        _is_not_none,
        doc='The charging current limit of the profile the car is parked in ("max" or "reduced").',
    )
    active_charging_profile_uses_preferred_times = _Field(
        _STATE, "activeChargingProfileUsesPreferredTimes", _is_not_none
    )
    preferred_charging_time_start = _Field(
        _STATE, "preferredChargingTimeStart", _is_not_none
    )
    preferred_charging_time_end = _Field(
        _STATE, "preferredChargingTimeEnd", _is_not_none
    )
    charging_timer_enabled_count = _Field(
        _STATE, "chargingTimerEnabledCount", _int_parses, parse_int
    )
    plug_state = _Field(_STATE, "plugState", _valid, _is_connected)
    plug_lock_state = _Field(_STATE, "plugLockState", _valid, _is_not_locked)
    plug_led_color = _Field(_STATE, "plugledColor", _valid)
    climatisation_state = _Field(_STATE, "climatisationState", _truthy)
    climatisation_target_temperature = _Field(
        _STATE,
        "climatisationTargetTemperatureC",
        _is_not_none,
        doc="Return the target temperature the car is set to, in Celsius.\n\nReported by the car, so it does not have to be held locally. Note the\ncar stores half degrees even though the api_level 1 write truncates to\nwhole ones.",
    )
    outdoor_temperature = _Field(_STATE, "outdoorTemperature", _truthy)
    glass_surface_heating = _Field(_STATE, "isMirrorHeatingActive", _is_not_none)
    door_lock_status = _Field(
        _STATE,
        "doorLockStatus",
        _is_known,
        doc='The car\'s own lock verdict for the whole vehicle, "locked" or\n"unlocked". Preferred over doors_trunk_status, which needs all four\ndoors and so has nothing to say about a coupé.',
    )
    access_overall_status = _Field(
        _STATE,
        "accessOverallStatus",
        _is_known,
        doc=(
            "The car's own one-word verdict on doors, windows and locks together, "
            '"safe" when everything is closed and locked.'
        ),
    )
    last_trip = _Field(
        _STATE,
        "lastTripShortTerm",
        _is_dict,
        doc="The car's last short-term trip: distance, duration, consumption.",
    )
    trip_totals = _Field(
        _STATE,
        "lastTripLongTerm",
        _is_dict,
        doc="The car's long-term trip: totals since its counter was last reset.",
    )
    shortterm_current = _Field(_STATE, "shortterm_current", _truthy)
    shortterm_reset = _Field(_STATE, "shortterm_reset", _truthy)
    longterm_current = _Field(_STATE, "longterm_current", _truthy)
    longterm_reset = _Field(_STATE, "longterm_reset", _truthy)

    # Returned whether or not the car reports it:
    charging_profiles = _Field(_STATE, "chargingProfiles", _is_list, gated=False)
    charging_timers = _Field(
        _STATE,
        "chargingTimers",
        _is_list,
        gated=False,
        doc="Return the departure/charging timers, for the attribute payload.",
    )
    climatisation_window_heating_enabled = _Field(
        _STATE, "climatisationWindowHeatingEnabled", _is_not_none, gated=False
    )
    climatisation_at_unlock = _Field(
        _STATE, "climatisationAtUnlock", _is_not_none, gated=False
    )
    climatisation_zone_front_left = _Field(
        _STATE, "climatisationZoneFrontLeft", _is_not_none, gated=False
    )
    climatisation_zone_front_right = _Field(
        _STATE, "climatisationZoneFrontRight", _is_not_none, gated=False
    )
    climatisation_zone_rear_left = _Field(
        _STATE, "climatisationZoneRearLeft", _is_not_none, gated=False
    )
    climatisation_zone_rear_right = _Field(
        _STATE, "climatisationZoneRearRight", _is_not_none, gated=False
    )

    @property
    def oil_level_binary(self):
        """Return oil level binary."""
        if self.oil_level_binary_supported:
            return not self._vehicle.fields.get("OIL_LEVEL_DIPSTICKS_PERCENTAGE")

    @property
    def oil_level_binary_supported(self):
        """Check if oil level binary is supported."""
        return isinstance(
            self._vehicle.fields.get("OIL_LEVEL_DIPSTICKS_PERCENTAGE"), bool
        )

    @property
    def preheater_active(self):
        state = self._vehicle.state.get("climatisationState")
        legacy = self._vehicle.state.get("preheaterState")
        if legacy:
            report = legacy.get("climatisationStateReport") or {}
            if (legacy_state := report.get("climatisationState")) is not None:
                state = legacy_state
        if state is None:
            return None
        return str(state).lower() not in _INACTIVE_PREHEATER_STATES

    @property
    def preheater_active_supported(self):
        return self.preheater_active is not None

    @property
    def preheater_duration(self):
        if self.preheater_duration_supported:
            res = (
                self._vehicle.state["preheaterState"]
                .get("climatisationStateReport")
                .get("climatisationDuration")
            )
            return parse_int(res)

    @property
    def preheater_duration_supported(self):
        return self.preheater_state_supported

    @property
    def preheater_remaining_supported(self):
        return self.preheater_state_supported

    @property
    def preheater_remaining(self):
        if self.preheater_remaining_supported:
            res = (
                self._vehicle.state["preheaterState"]
                .get("climatisationStateReport")
                .get("remainingClimateTime")
            )
            return parse_int(res)

    @property
    def warning_lights(self) -> list[dict[str, Any]] | None:
        """The warning lights the car reports as lit, or None when it says nothing."""
        value = self._vehicle.state.get("warningLights")
        if not isinstance(value, list):
            return None
        return [item for item in value if isinstance(item, dict)]

    @property
    def warning_light_count(self) -> int | None:
        lights = self.warning_lights
        return None if lights is None else len(lights)

    @property
    def parking_light(self):
        """Return true if parking light is on"""
        if self.parking_light_supported:
            try:
                check = self._vehicle.fields.get("LIGHT_STATUS")
                return check[0]["status"] != "off" or check[1]["status"] != "off"
            except KeyError:
                return False

    @property
    def parking_light_supported(self):
        """Return true if parking light is supported"""
        check = self._vehicle.fields.get("LIGHT_STATUS")
        if check:
            return True

    @property
    def any_window_open_supported(self):
        """Return true if window state is supported"""
        checkLeftFront = self._vehicle.fields.get("STATE_LEFT_FRONT_WINDOW")
        checkLeftRear = self._vehicle.fields.get("STATE_LEFT_REAR_WINDOW")
        checkRightFront = self._vehicle.fields.get("STATE_RIGHT_FRONT_WINDOW")
        checkRightRear = self._vehicle.fields.get("STATE_RIGHT_REAR_WINDOW")
        checkSunRoof = self._vehicle.fields.get("STATE_SUN_ROOF_MOTOR_COVER", None)
        checkRoofCover = self._vehicle.fields.get("STATE_ROOF_COVER_WINDOW", None)
        acceptable_window_states = ["3", "0", None]
        if (
            checkLeftFront
            and checkLeftRear
            and checkRightFront
            and checkRightRear
            and (checkSunRoof in acceptable_window_states)
            and (checkRoofCover in acceptable_window_states)
        ):
            return True

    @property
    def any_window_open(self):
        if self.any_window_open_supported:
            checkLeftFront = self._vehicle.fields.get("STATE_LEFT_FRONT_WINDOW")
            checkLeftRear = self._vehicle.fields.get("STATE_LEFT_REAR_WINDOW")
            checkRightFront = self._vehicle.fields.get("STATE_RIGHT_FRONT_WINDOW")
            checkRightRear = self._vehicle.fields.get("STATE_RIGHT_REAR_WINDOW")
            checkSunRoof = self._vehicle.fields.get("STATE_SUN_ROOF_MOTOR_COVER", None)
            checkRoofCover = self._vehicle.fields.get("STATE_ROOF_COVER_WINDOW", None)
            acceptable_window_states = ["3", None]
            return not (
                checkLeftFront == "3"
                and checkLeftRear == "3"
                and checkRightFront == "3"
                and checkRightRear == "3"
                and (checkSunRoof in acceptable_window_states)
                and (checkRoofCover in acceptable_window_states)
            )

    @property
    def any_door_unlocked_supported(self):
        checkLeftFront = self._vehicle.fields.get("LOCK_STATE_LEFT_FRONT_DOOR")
        checkLeftRear = self._vehicle.fields.get("LOCK_STATE_LEFT_REAR_DOOR")
        checkRightFront = self._vehicle.fields.get("LOCK_STATE_RIGHT_FRONT_DOOR")
        checkRightRear = self._vehicle.fields.get("LOCK_STATE_RIGHT_REAR_DOOR")
        if checkLeftFront and checkLeftRear and checkRightFront and checkRightRear:
            return True

    @property
    def any_door_unlocked(self):
        if self.any_door_unlocked_supported:
            checkLeftFront = self._vehicle.fields.get("LOCK_STATE_LEFT_FRONT_DOOR")
            checkLeftRear = self._vehicle.fields.get("LOCK_STATE_LEFT_REAR_DOOR")
            checkRightFront = self._vehicle.fields.get("LOCK_STATE_RIGHT_FRONT_DOOR")
            checkRightRear = self._vehicle.fields.get("LOCK_STATE_RIGHT_REAR_DOOR")
            return not (
                checkLeftFront == "2"
                and checkLeftRear == "2"
                and checkRightFront == "2"
                and checkRightRear == "2"
            )

    @property
    def any_door_open_supported(self):
        checkLeftFront = self._vehicle.fields.get("OPEN_STATE_LEFT_FRONT_DOOR")
        checkLeftRear = self._vehicle.fields.get("OPEN_STATE_LEFT_REAR_DOOR")
        checkRightFront = self._vehicle.fields.get("OPEN_STATE_RIGHT_FRONT_DOOR")
        checkRightRear = self._vehicle.fields.get("OPEN_STATE_RIGHT_REAR_DOOR")
        if checkLeftFront and checkLeftRear and checkRightFront and checkRightRear:
            return True

    @property
    def any_door_open(self):
        if self.any_door_open_supported:
            checkLeftFront = self._vehicle.fields.get("OPEN_STATE_LEFT_FRONT_DOOR")
            checkLeftRear = self._vehicle.fields.get("OPEN_STATE_LEFT_REAR_DOOR")
            checkRightFront = self._vehicle.fields.get("OPEN_STATE_RIGHT_FRONT_DOOR")
            checkRightRear = self._vehicle.fields.get("OPEN_STATE_RIGHT_REAR_DOOR")
            return not (
                checkLeftFront == "3"
                and checkLeftRear == "3"
                and checkRightFront == "3"
                and checkRightRear == "3"
            )

    @property
    def doors_trunk_status_supported(self):
        return (
            self.any_door_open_supported
            and self.any_door_unlocked_supported
            and self.trunk_open_supported
            and self.trunk_unlocked_supported
        )

    @property
    def doors_trunk_status(self):
        if (
            self.any_door_open_supported
            and self.any_door_unlocked_supported
            and self.trunk_open_supported
            and self.trunk_unlocked_supported
        ):
            if self.any_door_open or self.trunk_open:
                return "Open"
            elif self.any_door_unlocked or self.trunk_unlocked:
                return "Closed"
            else:
                return "Locked"

    @property
    def available_charge_modes(self):
        """Return the modes the car says it accepts, which can be empty."""
        modes = self._vehicle.state.get("availableChargeModes")
        return modes if isinstance(modes, list) else None

    @property
    def actual_charge_rate_unit(self):
        return "km/h"

    @property
    def remaining_charging_time(self):
        """Return remaining charging time"""
        if self.remaining_charging_time_supported:
            reported = self._vehicle.state.get("remainingChargingTime")
            if reported is not None:
                return reported
            # A car that charges without ever saying how long (the A6 e-tron
            # does not) must not read "0 minutes left". Not charging, there is
            # nothing left, so 0 is still right.
            charging = str(self._vehicle.state.get("chargingState", "")).lower()
            return None if charging == "charging" else 0

    @property
    def remaining_charging_time_unit(self):
        return "min"

    @property
    def remaining_charging_time_supported(self):
        return self.car_type in ["hybrid", "electric"]

    @property
    def charging_complete_time(self):
        """Return the datetime when charging is or was expected to be complete."""
        # Check if remaining charging time is not supported
        if not self.remaining_charging_time_supported:
            return None
        # If there's no last update or remaining time, we can't calculate
        if self.last_update_time is None or self.remaining_charging_time is None:
            return None
        # Calculate the complete time whenever there is a positive remaining time
        if self.remaining_charging_time > 0:
            calculated_time = self.last_update_time + timedelta(
                minutes=self.remaining_charging_time
            )
            self.charging_complete_time_frozen = (
                calculated_time  # Always update the frozen time
            )
            return calculated_time
        # If the remaining time is zero or negative, and no frozen time is set,
        # we have no knowledge of the last completion time, so return None
        if self.charging_complete_time_frozen is None:
            return None
        # Otherwise, return the frozen complete time
        return self.charging_complete_time_frozen

    @property
    def park_time(self):
        """Legacy true parking clock or a labeled last parked-position capture.

        CARIAD parkingposition supplies carCapturedTimestamp. It is the time
        Audi captured the *parked GPS position*, not a verified parking-start
        or engine-off event. Never claim a more precise meaning.
        """
        legacy = self._vehicle.state.get("vehicleParkingClock")
        if legacy is not None:
            return legacy
        position = self._vehicle.state.get("position") or {}
        if isinstance(position, dict):
            return position.get("parktime") or position.get("timestamp")
        return None

    @property
    def park_time_source(self):
        if self._vehicle.state.get("vehicleParkingClock") is not None:
            return "vehicle_parking_clock"
        if self.park_time is not None:
            return "last_parked_position_capture_estimate"
        return "unavailable"

    @property
    def park_time_supported(self):
        return self.park_time is not None

    @property
    def charging_current_limit_a(self):
        """Modern numeric AC charging current limit reported by CARIAD."""
        value = self._vehicle.state.get("chargingCurrentLimitA")
        return parse_float(value) if value is not None else None

    @property
    def charging_current_limit_mode(self):
        value = self._vehicle.state.get("chargingCurrentLimitMode")
        return None if value == _INVALID else value

    @property
    def charging_plug_auto_unlock(self):
        value = self._vehicle.state.get("chargingPlugAutoUnlock")
        # "on" is what older code assumed; "permanent" is what the capability
        # (allowPlugUnlockACPermanent) announces. Either means enabled.
        if value in ("on", "permanent"):
            return "enabled"
        if value == "off":
            return "disabled"
        return None

    @property
    def vehicle_reported_online(self):
        value = self._vehicle.state.get("vehicleReportedOnline")
        if value is True:
            return "online"
        if value is False:
            return "offline"
        return None

    @property
    def vehicle_reported_active(self):
        value = self._vehicle.state.get("vehicleReportedActive")
        if value is True:
            return "active"
        if value is False:
            return "inactive"
        return None

    @property
    def climatisation_timers(self):
        return self._vehicle.state.get("climatisationTimers")

    @property
    def climatisation_timer_count(self):
        return self._vehicle.state.get("climatisationTimerCount")

    @property
    def climatisation_timer_enabled_count(self):
        return self._vehicle.state.get("climatisationTimerEnabledCount")

    @property
    def next_climatisation_timer_local(self):
        return self._vehicle.state.get("nextClimatisationTimerLocal")

    @property
    def preferred_charging_time_enabled(self):
        return self._vehicle.state.get("preferredChargingTimeEnabled")

    @property
    def next_charging_timer_departure(self):
        return self._vehicle.state.get("nextChargingTimerDeparture")

    @property
    def external_power(self):
        """Return external Power"""
        if self.external_power_supported:
            external_power_status = self._vehicle.state.get("externalPower")
            if external_power_status == "unavailable":
                return "Not Ready"
            elif external_power_status == "ready":
                return "Ready"
            else:
                return external_power_status

    @property
    def external_power_supported(self):
        value = self._vehicle.state.get("externalPower")
        return value is not None and value != _INVALID

    battery_care_mode = _Field(_STATE, "batteryCareMode", _valid)
    charging_scenario = _Field(_STATE, "chargingScenario", _valid)
    climatisation_mode = _Field(_STATE, "climatisationMode", _valid)
    parking_brake = _Field(_STATE, "parkingBrake", _is_bool)

    @property
    def charge_target_limits(self) -> dict[str, int]:
        """Lowest charge target and step size the car says it accepts."""
        value = self._vehicle.state.get("chargeTargetLimits")
        return value if isinstance(value, dict) else {}

    @property
    def climatisation_supports(self) -> dict[str, bool]:
        """What the car says its climatisation does ("supports..." answers)."""
        value = self._vehicle.state.get("climatisationSupports")
        return value if isinstance(value, dict) else {}

    @property
    def charging_profiles_supports(self) -> dict[str, bool]:
        """What the car says its charging profiles do ("supports..." answers)."""
        value = self._vehicle.state.get("chargingProfilesSupports")
        return value if isinstance(value, dict) else {}

    @property
    def charge_target_min(self) -> int | None:
        return self.charge_target_limits.get("min")

    @property
    def charge_target_step(self) -> int | None:
        return self.charge_target_limits.get("step")

    @property
    def service_expiry(self) -> dict[str, Any]:
        """End date per time-limited online service, as the car lists them."""
        value = self._vehicle.state.get("serviceExpiry")
        return value if isinstance(value, dict) else {}

    @property
    def service_expiry_date(self):
        """The first date on which one of the online services ends."""
        dates = self.service_expiry
        return min(dates.values()) if dates else None

    @property
    def service_expiry_date_supported(self):
        return bool(self.service_expiry)

    @property
    def capabilities(self) -> frozenset[str]:
        """What the car says it can do. Empty when it does not report the list,
        which every caller must treat as "unknown", never as "nothing"."""
        value = self._vehicle.state.get("userCapabilities")
        return frozenset(value) if isinstance(value, list) else frozenset()

    @property
    def impaired_capabilities(self) -> frozenset[str]:
        """Capabilities the car lists while also reporting an error against
        them. Listed is not the same as working."""
        value = self._vehicle.state.get("userCapabilitiesImpaired")
        return frozenset(value) if isinstance(value, list) else frozenset()

    def has_capability(self, capability: str) -> bool | None:
        """True, False, or None when the car reports no capability list at all.

        Three-valued deliberately: a caller that cannot tell "not capable" from
        "did not say" will delete entities on the vehicles that never report
        the list.
        """
        caps = self.capabilities
        if not caps:
            return None
        if capability in caps:
            return True
        # Some cars announce one "departureTimers" capability for both kinds.
        return bool(_CAPABILITY_ALIASES.get(capability, frozenset()) & caps)

    @property
    def position_last_updated(self):
        """When the vehicle last reported the position, not when HA last polled.

        parkingposition carries its own carCapturedTimestamp and only moves when
        the car reports a new position, so a location can be hours old while the
        entity looks current. Exposing the capture time lets an automation decide
        whether a position is fresh enough to act on.
        """
        if self.position_last_updated_supported:
            return (self._vehicle.state.get("position") or {}).get("timestamp")

    @property
    def position_last_updated_supported(self):
        return (self._vehicle.state.get("position") or {}).get("timestamp") is not None

    @property
    def remaining_climatisation_time(self):
        if self.remaining_climatisation_time_supported:
            remaining_time = self._vehicle.state.get("remainingClimatisationTime")
            if remaining_time is not None and remaining_time < 0:
                return 0
            elif remaining_time is not None:
                return remaining_time
        return None

    @property
    def remaining_climatisation_time_supported(self):
        return self._vehicle.state.get("remainingClimatisationTime") is not None

    @property
    def preheater_state(self):
        check = self._vehicle.state.get("preheaterState")
        if check:
            return True

    @property
    def preheater_state_supported(self):
        check = self._vehicle.state.get("preheaterState")
        if check:
            return True

    @property
    def lock_supported(self):
        """A property, not a method. As a method the support check saw a bound
        function, which is always truthy, and created the lock on every car
        including those with no S-PIN and no way to know the state (#861)."""
        return bool(
            self._audi_service._spin is not None
            and (self.door_lock_status_supported or self.doors_trunk_status_supported)
        )

    @property
    def is_moving(self):
        """Return true if the vehicle is moving."""
        if self.is_moving_supported:
            return self._vehicle.state.get("is_moving")

    @property
    def is_moving_supported(self):
        """Return true if vehicle can move."""
        return True
