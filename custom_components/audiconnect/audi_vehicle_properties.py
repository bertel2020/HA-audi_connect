"""State properties of a vehicle, read from the data its updates collected."""

from __future__ import annotations

from datetime import timedelta

from .util import parse_float, parse_int

_INACTIVE_PREHEATER_STATES = frozenset({"off", "invalid", "unsupported", "error", ""})


class AudiVehicleProperties:
    """Read-only views of ``self._vehicle.state``; mixed into AudiConnectVehicle."""

    @property
    def last_update_time(self):
        if self.last_update_time_supported:
            return self._vehicle.state.get("last_update_time")

    @property
    def last_update_time_supported(self):
        check = self._vehicle.state.get("last_update_time")
        if check:
            return True

    @property
    def service_inspection_time(self):
        """Return time left for service inspection"""
        if self.service_inspection_time_supported:
            return int(
                self._vehicle.fields.get("MAINTENANCE_INTERVAL_TIME_TO_INSPECTION")
            )

    @property
    def service_inspection_time_supported(self) -> bool:
        check = self._vehicle.fields.get("MAINTENANCE_INTERVAL_TIME_TO_INSPECTION")
        return parse_int(check) is not None

    @property
    def service_inspection_distance(self):
        """Return distance left for service inspection"""
        if self.service_inspection_distance_supported:
            return int(
                self._vehicle.fields.get("MAINTENANCE_INTERVAL_DISTANCE_TO_INSPECTION")
            )

    @property
    def service_inspection_distance_supported(self) -> bool:
        check = self._vehicle.fields.get("MAINTENANCE_INTERVAL_DISTANCE_TO_INSPECTION")
        return parse_int(check) is not None

    @property
    def service_adblue_distance(self):
        """Return distance left for service inspection"""
        if self.service_adblue_distance_supported:
            return int(self._vehicle.fields.get("ADBLUE_RANGE"))

    @property
    def service_adblue_distance_supported(self) -> bool:
        check = self._vehicle.fields.get("ADBLUE_RANGE")
        return parse_int(check) is not None

    @property
    def oil_change_time(self):
        """Return time left for oil change"""
        if self.oil_change_time_supported:
            return int(
                self._vehicle.fields.get("MAINTENANCE_INTERVAL_TIME_TO_OIL_CHANGE")
            )

    @property
    def oil_change_time_supported(self) -> bool:
        check = self._vehicle.fields.get("MAINTENANCE_INTERVAL_TIME_TO_OIL_CHANGE")
        return parse_int(check) is not None

    @property
    def oil_change_distance(self):
        """Return distance left for oil change"""
        if self.oil_change_distance_supported:
            return int(
                self._vehicle.fields.get("MAINTENANCE_INTERVAL_DISTANCE_TO_OIL_CHANGE")
            )

    @property
    def oil_change_distance_supported(self) -> bool:
        check = self._vehicle.fields.get("MAINTENANCE_INTERVAL_DISTANCE_TO_OIL_CHANGE")
        return parse_int(check) is not None

    @property
    def oil_level(self):
        """Return oil level percentage"""
        if self.oil_level_supported:
            return parse_float(
                self._vehicle.fields.get("OIL_LEVEL_DIPSTICKS_PERCENTAGE")
            )

    @property
    def oil_level_supported(self):
        """Check if oil level is supported."""
        check = self._vehicle.fields.get("OIL_LEVEL_DIPSTICKS_PERCENTAGE")
        return not isinstance(check, bool) and check is not None

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
    def braking_status(self):
        """Return true if braking status is on"""
        if self.braking_status_supported:
            check = self._vehicle.fields.get("BRAKING_STATUS")
            return check != "2"

    @property
    def braking_status_supported(self):
        """Return true if braking status is supported"""
        check = self._vehicle.fields.get("BRAKING_STATUS")
        if check:
            return True

    @property
    def mileage(self):
        if self.mileage_supported:
            check = self._vehicle.fields.get("UTC_TIME_AND_KILOMETER_STATUS")
            return parse_int(check)

    @property
    def mileage_supported(self):
        """Return true if mileage is supported"""
        check = self._vehicle.fields.get("UTC_TIME_AND_KILOMETER_STATUS")
        if check and parse_int(check):
            return True

    @property
    def range(self):
        if self.range_supported:
            check = self._vehicle.fields.get("TOTAL_RANGE")
            return parse_int(check)

    @property
    def range_supported(self) -> bool:
        """Return true if range is supported"""
        check = self._vehicle.fields.get("TOTAL_RANGE")
        return parse_int(check) is not None

    @property
    def tank_level(self):
        if self.tank_level_supported:
            check = self._vehicle.fields.get("TANK_LEVEL_IN_PERCENTAGE")
            return parse_int(check)

    @property
    def tank_level_supported(self) -> bool:
        """Return true if tank_level is supported"""
        check = self._vehicle.fields.get("TANK_LEVEL_IN_PERCENTAGE")
        return parse_int(check) is not None

    @property
    def position(self):
        """Return position."""
        if self.position_supported:
            return self._vehicle.state.get("position")

    @property
    def position_supported(self):
        """Return true if vehicle has position."""
        check = self._vehicle.state.get("position")
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
    def left_front_window_open_supported(self):
        return self._vehicle.fields.get("STATE_LEFT_FRONT_WINDOW")

    @property
    def left_front_window_open(self):
        if self.left_front_window_open_supported:
            return self._vehicle.fields.get("STATE_LEFT_FRONT_WINDOW") != "3"

    @property
    def right_front_window_open_supported(self):
        return self._vehicle.fields.get("STATE_RIGHT_FRONT_WINDOW")

    @property
    def right_front_window_open(self):
        if self.right_front_window_open_supported:
            return self._vehicle.fields.get("STATE_RIGHT_FRONT_WINDOW") != "3"

    @property
    def left_rear_window_open_supported(self):
        return self._vehicle.fields.get("STATE_LEFT_REAR_WINDOW")

    @property
    def left_rear_window_open(self):
        if self.left_rear_window_open_supported:
            return self._vehicle.fields.get("STATE_LEFT_REAR_WINDOW") != "3"

    @property
    def right_rear_window_open_supported(self):
        return self._vehicle.fields.get("STATE_RIGHT_REAR_WINDOW")

    @property
    def right_rear_window_open(self):
        if self.right_rear_window_open_supported:
            return self._vehicle.fields.get("STATE_RIGHT_REAR_WINDOW") != "3"

    @property
    def sun_roof_supported(self):
        return self._vehicle.fields.get("STATE_SUN_ROOF_MOTOR_COVER")

    @property
    def sun_roof(self):
        if self.sun_roof_supported:
            return self._vehicle.fields.get("STATE_SUN_ROOF_MOTOR_COVER") != "3"

    @property
    def roof_cover_supported(self):
        return self._vehicle.fields.get("STATE_ROOF_COVER_WINDOW")

    @property
    def roof_cover(self):
        if self.roof_cover_supported:
            return self._vehicle.fields.get("STATE_ROOF_COVER_WINDOW") != "3"

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
    def left_front_door_open_supported(self):
        return self._vehicle.fields.get("OPEN_STATE_LEFT_FRONT_DOOR")

    @property
    def left_front_door_open(self):
        if self.left_front_door_open_supported:
            return self._vehicle.fields.get("OPEN_STATE_LEFT_FRONT_DOOR") != "3"

    @property
    def right_front_door_open_supported(self):
        return self._vehicle.fields.get("OPEN_STATE_RIGHT_FRONT_DOOR")

    @property
    def right_front_door_open(self):
        if self.right_front_door_open_supported:
            return self._vehicle.fields.get("OPEN_STATE_RIGHT_FRONT_DOOR") != "3"

    @property
    def left_rear_door_open_supported(self):
        return self._vehicle.fields.get("OPEN_STATE_LEFT_REAR_DOOR")

    @property
    def left_rear_door_open(self):
        if self.left_rear_door_open_supported:
            return self._vehicle.fields.get("OPEN_STATE_LEFT_REAR_DOOR") != "3"

    @property
    def right_rear_door_open_supported(self):
        return self._vehicle.fields.get("OPEN_STATE_RIGHT_REAR_DOOR")

    @property
    def right_rear_door_open(self):
        if self.right_rear_door_open_supported:
            return self._vehicle.fields.get("OPEN_STATE_RIGHT_REAR_DOOR") != "3"

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
    def trunk_unlocked(self):
        if self.trunk_unlocked_supported:
            check = self._vehicle.fields.get("LOCK_STATE_TRUNK_LID")
            return check != "2"

    @property
    def trunk_unlocked_supported(self):
        check = self._vehicle.fields.get("LOCK_STATE_TRUNK_LID")
        if check:
            return True

    @property
    def trunk_open(self):
        if self.trunk_open_supported:
            check = self._vehicle.fields.get("OPEN_STATE_TRUNK_LID")
            return check != "3"

    @property
    def trunk_open_supported(self):
        check = self._vehicle.fields.get("OPEN_STATE_TRUNK_LID")
        if check:
            return True

    @property
    def hood_open(self):
        if self.hood_open_supported:
            check = self._vehicle.fields.get("OPEN_STATE_HOOD")
            return check != "3"

    @property
    def hood_open_supported(self):
        check = self._vehicle.fields.get("OPEN_STATE_HOOD")
        if check:
            return True

    @property
    def charging_state(self):
        """Return charging state"""
        if self.charging_state_supported:
            return self._vehicle.state.get("chargingState")

    @property
    def charging_state_supported(self):
        check = self._vehicle.state.get("chargingState")
        if check:
            return True

    @property
    def charging_mode(self):
        """Return charging mode"""
        if self.charging_mode_supported:
            return self._vehicle.state.get("chargeMode")

    @property
    def charging_mode_supported(self):
        check = self._vehicle.state.get("chargeMode")
        return check is not None and check != "unsupported"

    @property
    def preferred_charge_mode(self):
        """Return the charge mode the car is set to, not the one in progress."""
        if self.preferred_charge_mode_supported:
            return self._vehicle.state.get("preferredChargeMode")

    @property
    def preferred_charge_mode_supported(self):
        check = self._vehicle.state.get("preferredChargeMode")
        return check is not None and check != "unsupported"

    @property
    def available_charge_modes(self):
        """Return the modes the car says it accepts, which can be empty."""
        modes = self._vehicle.state.get("availableChargeModes")
        return modes if isinstance(modes, list) else None

    @property
    def energy_flow(self):
        """Return charging mode"""
        if self.energy_flow_supported:
            return self._vehicle.state.get("energyFlow")

    @property
    def energy_flow_supported(self):
        check = self._vehicle.state.get("energyFlow")
        if check is not None:
            return True

    @property
    def charging_type(self):
        """Return charging type"""
        if self.charging_type_supported:
            return self._vehicle.state.get("chargeType")

    @property
    def charging_type_supported(self):
        check = self._vehicle.state.get("chargeType")
        if check and check != "unsupported":
            return True

    @property
    def max_charge_current(self):
        """Return max charge current"""
        if self.max_charge_current_supported:
            try:
                return parse_float(self._vehicle.state.get("maxChargeCurrent"))
            except ValueError:
                return -1

    @property
    def max_charge_current_supported(self):
        check = self._vehicle.state.get("maxChargeCurrent")
        if check is not None:
            return True

    @property
    def actual_charge_rate(self):
        """Return actual charge rate"""
        if self.actual_charge_rate_supported:
            try:
                return parse_float(self._vehicle.state.get("actualChargeRate"))
            except ValueError:
                return -1

    @property
    def actual_charge_rate_supported(self):
        check = self._vehicle.state.get("actualChargeRate")
        if check is not None:
            return True

    @property
    def actual_charge_rate_unit(self):
        return "km/h"

    @property
    def charging_power(self):
        """Return charging power"""
        if self.charging_power_supported:
            try:
                return parse_float(self._vehicle.state.get("chargingPower"))
            except ValueError:
                return -1

    @property
    def charging_power_supported(self):
        check = self._vehicle.state.get("chargingPower")
        if check is not None:
            return True

    @property
    def primary_engine_type(self):
        """Return primary engine type"""
        if self.primary_engine_type_supported:
            return self._vehicle.state.get("engineTypeFirstEngine")

    @property
    def primary_engine_type_supported(self):
        check = self._vehicle.state.get("engineTypeFirstEngine")
        if check and check != "unsupported":
            return True

    @property
    def secondary_engine_type(self):
        """Return secondary engine type"""
        if self.secondary_engine_type_supported:
            return self._vehicle.state.get("engineTypeSecondEngine")

    @property
    def secondary_engine_type_supported(self):
        check = self._vehicle.state.get("engineTypeSecondEngine")
        if check and check != "unsupported":
            return True

    @property
    def primary_engine_range(self):
        """Return primary engine range"""
        if self.primary_engine_range_supported:
            return self._vehicle.state.get("primaryEngineRange")

    @property
    def primary_engine_range_supported(self):
        check = self._vehicle.state.get("primaryEngineRange")
        if check and check != "unsupported":
            return True

    @property
    def primary_engine_range_percent(self):
        """Return primary engine range"""
        if self.primary_engine_range_percent_supported:
            return self._vehicle.state.get("primaryEngineRangePercent")

    @property
    def primary_engine_range_percent_supported(self):
        check = self._vehicle.state.get("primaryEngineRangePercent")
        if check and check != "unsupported":
            return True

    @property
    def secondary_engine_range(self):
        """Return secondary engine range"""
        if self.secondary_engine_range_supported:
            return self._vehicle.state.get("secondaryEngineRange")

    @property
    def secondary_engine_range_supported(self):
        check = self._vehicle.state.get("secondaryEngineRange")
        if check is not None and check != "unsupported":
            return True

    @property
    def car_type(self):
        """Return secondary engine range"""
        if self.car_type_supported:
            return self._vehicle.state.get("carType")

    @property
    def car_type_supported(self):
        check = self._vehicle.state.get("carType")
        if check and check != "unsupported":
            return True

    @property
    def secondary_engine_range_percent(self):
        """Return secondary engine range"""
        if self.secondary_engine_range_percent_supported:
            return self._vehicle.state.get("secondaryEngineRangePercent")

    @property
    def secondary_engine_range_percent_supported(self):
        check = self._vehicle.state.get("secondaryEngineRangePercent")
        if check and check != "unsupported":
            return True

    @property
    def hybrid_range(self):
        """Return hybrid range"""
        if self.hybrid_range_supported:
            return self._vehicle.state.get("hybridRange")

    @property
    def hybrid_range_supported(self):
        check = self._vehicle.state.get("hybridRange")
        if check and check != "unsupported":
            return True

    @property
    def state_of_charge(self):
        """Return state of charge"""
        if self.state_of_charge_supported:
            return parse_int(self._vehicle.state.get("stateOfCharge"))

    @property
    def state_of_charge_supported(self):
        return parse_int(self._vehicle.state.get("stateOfCharge")) is not None

    @property
    def remaining_charging_time(self):
        """Return remaining charging time"""
        if self.remaining_charging_time_supported:
            return self._vehicle.state.get("remainingChargingTime", 0)

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
    def target_state_of_charge(self):
        """Return state of charge"""
        if self.target_state_of_charge_supported:
            return parse_int(self._vehicle.state.get("targetstateOfCharge"))

    @property
    def target_state_of_charge_supported(self):
        return parse_int(self._vehicle.state.get("targetstateOfCharge")) is not None

    @property
    def active_charging_profile_target_soc(self):
        """Return the target SoC of the location profile the car is parked in.

        This is the limit the car actually charges to. target_state_of_charge is
        the global setting, which a location profile overrides, so the two
        disagree whenever a profile is in force (upstream #722).
        """
        if self.active_charging_profile_target_soc_supported:
            return parse_int(self._vehicle.state.get("activeChargingProfileTargetSoc"))

    @property
    def active_charging_profile_target_soc_supported(self):
        return (
            parse_int(self._vehicle.state.get("activeChargingProfileTargetSoc"))
            is not None
        )

    @property
    def active_charging_profile_name(self):
        """Return the name of the charging profile in force at this location."""
        if self.active_charging_profile_name_supported:
            return self._vehicle.state.get("activeChargingProfileName")

    @property
    def active_charging_profile_name_supported(self):
        return self._vehicle.state.get("activeChargingProfileName") is not None

    @property
    def active_charging_profile_id(self):
        if self.active_charging_profile_id_supported:
            return parse_int(self._vehicle.state.get("activeChargingProfileId"))

    @property
    def active_charging_profile_id_supported(self):
        return parse_int(self._vehicle.state.get("activeChargingProfileId")) is not None

    @property
    def active_charging_profile_min_soc(self):
        """Return the minimum SoC the profile tops up to regardless of schedule."""
        if self.active_charging_profile_min_soc_supported:
            return parse_int(self._vehicle.state.get("activeChargingProfileMinSoc"))

    @property
    def active_charging_profile_min_soc_supported(self):
        return (
            parse_int(self._vehicle.state.get("activeChargingProfileMinSoc"))
            is not None
        )

    @property
    def charging_profiles(self):
        """Return every location profile, for the attribute payload."""
        return self._vehicle.state.get("chargingProfiles")

    @property
    def charging_profiles_supported(self):
        return isinstance(self._vehicle.state.get("chargingProfiles"), list)

    @property
    def preferred_charging_time_start(self):
        if self.preferred_charging_time_start_supported:
            return self._vehicle.state.get("preferredChargingTimeStart")

    @property
    def preferred_charging_time_start_supported(self):
        return self._vehicle.state.get("preferredChargingTimeStart") is not None

    @property
    def preferred_charging_time_end(self):
        if self.preferred_charging_time_end_supported:
            return self._vehicle.state.get("preferredChargingTimeEnd")

    @property
    def preferred_charging_time_end_supported(self):
        return self._vehicle.state.get("preferredChargingTimeEnd") is not None

    @property
    def preferred_charging_time_enabled(self):
        return self._vehicle.state.get("preferredChargingTimeEnabled")

    @property
    def charging_timers(self):
        """Return the departure/charging timers, for the attribute payload."""
        return self._vehicle.state.get("chargingTimers")

    @property
    def charging_timers_supported(self):
        return isinstance(self._vehicle.state.get("chargingTimers"), list)

    @property
    def charging_timer_enabled_count(self):
        if self.charging_timer_enabled_count_supported:
            return parse_int(self._vehicle.state.get("chargingTimerEnabledCount"))

    @property
    def charging_timer_enabled_count_supported(self):
        return (
            parse_int(self._vehicle.state.get("chargingTimerEnabledCount")) is not None
        )

    @property
    def next_charging_timer_departure(self):
        return self._vehicle.state.get("nextChargingTimerDeparture")

    @property
    def plug_state(self):
        """Return plug state"""
        if self.plug_state_supported:
            check = self._vehicle.state.get("plugState")
            return check not in ("invalid", "disconnected")

    @property
    def plug_state_supported(self):
        check = self._vehicle.state.get("plugState")
        if check:
            return True

    @property
    def plug_lock_state(self):
        """Return plug lock state"""
        if self.plug_lock_state_supported:
            check = self._vehicle.state.get("plugLockState")
            return check != "locked"

    @property
    def plug_lock_state_supported(self):
        check = self._vehicle.state.get("plugLockState")
        if check:
            return True

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
        return self._vehicle.state.get("externalPower") is not None

    @property
    def plug_led_color(self):
        """Return plug LED Color"""
        if self.plug_led_color_supported:
            return self._vehicle.state.get("plugledColor")

    @property
    def plug_led_color_supported(self):
        check = self._vehicle.state.get("plugledColor")
        if check:
            return True

    @property
    def climatisation_state(self):
        if self.climatisation_state_supported:
            return self._vehicle.state.get("climatisationState")

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
        return capability in caps

    @property
    def climatisation_state_supported(self):
        check = self._vehicle.state.get("climatisationState")
        if check:
            return True

    @property
    def climatisation_target_temperature(self):
        """Return the target temperature the car is set to, in Celsius.

        Reported by the car, so it does not have to be held locally. Note the
        car stores half degrees even though the api_level 1 write truncates to
        whole ones.
        """
        if self.climatisation_target_temperature_supported:
            return self._vehicle.state.get("climatisationTargetTemperatureC")

    @property
    def climatisation_target_temperature_supported(self):
        return self._vehicle.state.get("climatisationTargetTemperatureC") is not None

    @property
    def climatisation_window_heating_enabled(self):
        return self._vehicle.state.get("climatisationWindowHeatingEnabled")

    @property
    def climatisation_window_heating_enabled_supported(self):
        return self._vehicle.state.get("climatisationWindowHeatingEnabled") is not None

    @property
    def climatisation_at_unlock(self):
        return self._vehicle.state.get("climatisationAtUnlock")

    @property
    def climatisation_at_unlock_supported(self):
        return self._vehicle.state.get("climatisationAtUnlock") is not None

    @property
    def climatisation_zone_front_left(self):
        return self._vehicle.state.get("climatisationZoneFrontLeft")

    @property
    def climatisation_zone_front_left_supported(self):
        return self._vehicle.state.get("climatisationZoneFrontLeft") is not None

    @property
    def climatisation_zone_front_right(self):
        return self._vehicle.state.get("climatisationZoneFrontRight")

    @property
    def climatisation_zone_front_right_supported(self):
        return self._vehicle.state.get("climatisationZoneFrontRight") is not None

    @property
    def climatisation_zone_rear_left(self):
        return self._vehicle.state.get("climatisationZoneRearLeft")

    @property
    def climatisation_zone_rear_left_supported(self):
        return self._vehicle.state.get("climatisationZoneRearLeft") is not None

    @property
    def climatisation_zone_rear_right(self):
        return self._vehicle.state.get("climatisationZoneRearRight")

    @property
    def climatisation_zone_rear_right_supported(self):
        return self._vehicle.state.get("climatisationZoneRearRight") is not None

    @property
    def outdoor_temperature(self):
        if self.outdoor_temperature_supported:
            return self._vehicle.state.get("outdoorTemperature")

    @property
    def outdoor_temperature_supported(self):
        check = self._vehicle.state.get("outdoorTemperature")
        if check:
            return True

    @property
    def glass_surface_heating(self):
        if self.glass_surface_heating_supported:
            return self._vehicle.state.get("isMirrorHeatingActive")

    @property
    def glass_surface_heating_supported(self):
        return self._vehicle.state.get("isMirrorHeatingActive") is not None

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
    def park_time(self):
        if self.park_time_supported:
            return self._vehicle.state.get("vehicleParkingClock")

    @property
    def park_time_supported(self):
        return self._vehicle.state.get("vehicleParkingClock") is not None

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
    def door_lock_status(self):
        """The car's own lock verdict for the whole vehicle, "locked" or
        "unlocked". Preferred over doors_trunk_status, which needs all four
        doors and so has nothing to say about a coupé."""
        if self.door_lock_status_supported:
            return self._vehicle.state.get("doorLockStatus")

    @property
    def door_lock_status_supported(self):
        check = self._vehicle.state.get("doorLockStatus")
        return check is not None and check != "unsupported"

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
    def shortterm_current(self):
        """Return shortterm."""
        if self.shortterm_current_supported:
            return self._vehicle.state.get("shortterm_current")

    @property
    def shortterm_current_supported(self):
        """Return true if vehicle has shortterm_current."""
        check = self._vehicle.state.get("shortterm_current")
        if check:
            return True

    @property
    def shortterm_reset(self):
        """Return shortterm."""
        if self.shortterm_reset_supported:
            return self._vehicle.state.get("shortterm_reset")

    @property
    def shortterm_reset_supported(self):
        """Return true if vehicle has shortterm_reset."""
        check = self._vehicle.state.get("shortterm_reset")
        if check:
            return True

    @property
    def longterm_current(self):
        """Return longterm."""
        if self.longterm_current_supported:
            return self._vehicle.state.get("longterm_current")

    @property
    def longterm_current_supported(self):
        """Return true if vehicle has longterm_current."""
        check = self._vehicle.state.get("longterm_current")
        if check:
            return True

    @property
    def longterm_reset(self):
        """Return longterm."""
        if self.longterm_reset_supported:
            return self._vehicle.state.get("longterm_reset")

    @property
    def longterm_reset_supported(self):
        """Return true if vehicle has longterm_reset."""
        check = self._vehicle.state.get("longterm_reset")
        if check:
            return True

    @property
    def is_moving(self):
        """Return true if the vehicle is moving."""
        if self.is_moving_supported:
            return self._vehicle.state.get("is_moving")

    @property
    def is_moving_supported(self):
        """Return true if vehicle can move."""
        return True
