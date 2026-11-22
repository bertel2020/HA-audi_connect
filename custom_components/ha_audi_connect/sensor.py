"""Support for Audi Connect sensors."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from homeassistant.components.sensor import (
    RestoreSensor,
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfElectricCurrent,
    UnitOfEnergy,
    UnitOfLength,
    UnitOfPower,
    UnitOfSpeed,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import AudiRuntimeData
from .audi_entity import AudiEntity, entity_unique_id, should_create_entity
from .coordinator import AudiDataUpdateCoordinator
from .freshness import usable_vehicle_timestamp, vehicle_age_minutes, vehicle_freshness
from .util import parse_datetime


# Read-only: the coordinator fetches, so the entities never need to queue.
PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class AudiSensorEntityDescription(SensorEntityDescription):
    """Describes an Audi sensor entity."""

    attr_key: str
    # The car's own capability id, where one maps cleanly. Given one, entity
    # creation follows the capability rather than whether this poll carried
    # the value, so a partial poll leaves the entity unavailable instead of
    # deleting it.
    capability: str | None = None
    # Name of a vehicle flag that must be true for the entity to exist. A hard
    # "no" (see should_create_entity's ``configured``): a stale registry entry
    # must not bring back a sensor the account cannot feed at all.
    requires: str | None = None
    value_fn: Callable[[Any], Any] | None = None
    extra_attrs_fn: Callable[[Any], dict[str, Any]] | None = None
    unit_fn: Callable[[Any], str | None] | None = None


def is_sensor_available_for(
    description: AudiSensorEntityDescription, vehicle: Any
) -> bool:
    """False when the account cannot feed this sensor at all (e.g. trips on Auth0)."""
    if description.requires is None:
        return True
    return bool(getattr(vehicle, description.requires, True))


def service_figures_reported(vehicle: Any) -> int:
    """How many of the four service figures the car itself reports."""
    return sum(
        getattr(vehicle, name, None) is not None
        for name in (
            "service_inspection_time",
            "service_inspection_distance",
            "oil_change_time",
            "oil_change_distance",
        )
    )


def sensor_descriptions_to_create(
    hass: HomeAssistant, vehicle: Any
) -> list[AudiSensorEntityDescription]:
    """The sensor descriptions this vehicle gets an entity for."""
    return [
        description
        for description in SENSOR_DESCRIPTIONS
        if should_create_entity(
            hass,
            "sensor",
            description.key,
            vehicle,
            description.attr_key,
            description.capability,
            configured=is_sensor_available_for(description, vehicle),
        )
    ]


def _warning_light_attrs(vehicle: Any) -> dict[str, Any] | None:
    """The lit warnings, reduced to plain values and capped."""
    lights = getattr(vehicle, "warning_lights", None)
    if lights is None:
        return None
    keep = (str, int, float, bool)
    return {
        "warnings": [
            {k: v for k, v in item.items() if isinstance(v, keep)}
            for item in lights[:20]
        ]
    }


def _window_sensors() -> tuple[AudiSensorEntityDescription, ...]:
    """One opening-in-percent sensor per window; a window the car does not name
    (a two-door body) simply gets none."""
    return tuple(
        AudiSensorEntityDescription(
            key=f"window_open_pct_{key}",
            attr_key=f"window_open_pct_{key}",
            translation_key=f"window_open_pct_{key}",
            native_unit_of_measurement=PERCENTAGE,
            state_class=SensorStateClass.MEASUREMENT,
            entity_category=EntityCategory.DIAGNOSTIC,
        )
        for key in ("front_left", "front_right", "rear_left", "rear_right")
    )


def _trip_figure(attr_key: str, field: str):
    """One figure out of the car's last-trip or trip-totals block."""

    def value(vehicle: Any) -> Any:
        block = getattr(vehicle, attr_key, None)
        raw = block.get(field) if isinstance(block, dict) else None
        return (
            raw if isinstance(raw, (int, float)) and not isinstance(raw, bool) else None
        )

    return value


def _trip_time(attr_key: str, field: str):
    """The time a trip ended, only if the car gave a real time with a time zone."""

    def value(vehicle: Any) -> Any:
        block = getattr(vehicle, attr_key, None)
        raw = block.get(field) if isinstance(block, dict) else None
        return raw if isinstance(raw, datetime) and raw.tzinfo is not None else None

    return value


def _trip_sensors(
    attr_key: str, prefix: str, *, enabled: bool, cumulative: bool = False
) -> tuple[AudiSensorEntityDescription, ...]:
    """The distance, time, consumption, energy and speed of one kind of trip.

    cumulative marks the long-term totals, which only grow (until the car's
    counter is reset) and so get long-term statistics as total_increasing.
    """
    base = {"attr_key": attr_key, "entity_registry_enabled_default": enabled}
    counting = (
        SensorStateClass.TOTAL_INCREASING
        if cumulative
        else SensorStateClass.MEASUREMENT
    )
    # One trip's energy is not a running meter, so it gets no state class.
    energy = SensorStateClass.TOTAL_INCREASING if cumulative else None
    return (
        AudiSensorEntityDescription(
            key=f"{prefix}_distance",
            translation_key=f"{prefix}_distance",
            native_unit_of_measurement=UnitOfLength.KILOMETERS,
            device_class=SensorDeviceClass.DISTANCE,
            suggested_display_precision=0,
            state_class=counting,
            value_fn=_trip_figure(attr_key, "mileage_km"),
            **base,
        ),
        AudiSensorEntityDescription(
            key=f"{prefix}_duration",
            translation_key=f"{prefix}_duration",
            native_unit_of_measurement=UnitOfTime.MINUTES,
            device_class=SensorDeviceClass.DURATION,
            suggested_display_precision=0,
            state_class=counting,
            value_fn=_trip_figure(attr_key, "travelTime"),
            **base,
        ),
        AudiSensorEntityDescription(
            key=f"{prefix}_consumption",
            translation_key=f"{prefix}_consumption",
            native_unit_of_measurement="kWh/100 km",
            suggested_display_precision=1,
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=_trip_figure(attr_key, "averageElectricConsumption"),
            **base,
        ),
        AudiSensorEntityDescription(
            key=f"{prefix}_energy",
            translation_key=f"{prefix}_energy",
            native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
            device_class=SensorDeviceClass.ENERGY,
            suggested_display_precision=1,
            state_class=energy,
            value_fn=_trip_figure(attr_key, "totalElectricConsumption_kwh"),
            **base,
        ),
        AudiSensorEntityDescription(
            key=f"{prefix}_speed",
            translation_key=f"{prefix}_speed",
            native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
            device_class=SensorDeviceClass.SPEED,
            suggested_display_precision=0,
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=_trip_figure(attr_key, "averageSpeed_kmph"),
            **base,
        ),
    )


def _trip_data_value(vehicle: Any, attr_key: str) -> Any:
    """Extract timestamp from trip data dict as the sensor state."""
    td = getattr(vehicle, attr_key, None)
    if td and isinstance(td, dict):
        return parse_datetime(td.get("timestamp"))
    return None


def _trip_data_attrs(vehicle: Any, attr_key: str) -> dict[str, Any]:
    """Extract extra attributes from trip data dict."""
    td = getattr(vehicle, attr_key, None)
    if not td or not isinstance(td, dict):
        return {}
    return {
        "averageElectricEngineConsumption": td.get("averageElectricEngineConsumption"),
        "averageFuelConsumption": td.get("averageFuelConsumption"),
        "averageSpeed": td.get("averageSpeed"),
        "mileage": td.get("mileage"),
        "overallMileage": td.get("overallMileage"),
        "startMileage": td.get("startMileage"),
        "traveltime": td.get("traveltime"),
        "tripID": td.get("tripID"),
        "zeroEmissionDistance": td.get("zeroEmissionDistance"),
    }


def _active_profile_attrs(vehicle: Any) -> dict[str, Any]:
    """Everything needed to see why the car is charging to the number it is."""
    attrs: dict[str, Any] = {
        "profile_id": getattr(vehicle, "active_charging_profile_id", None),
        "profile_name": getattr(vehicle, "active_charging_profile_name", None),
        "min_soc_pct": getattr(vehicle, "active_charging_profile_min_soc", None),
        "global_target_soc_pct": getattr(vehicle, "target_state_of_charge", None),
        "preferred_charging_time_start": getattr(
            vehicle, "preferred_charging_time_start", None
        ),
        "preferred_charging_time_end": getattr(
            vehicle, "preferred_charging_time_end", None
        ),
        "preferred_charging_time_enabled": getattr(
            vehicle, "preferred_charging_time_enabled", None
        ),
        "profiles": getattr(vehicle, "charging_profiles", None),
    }
    return {k: v for k, v in attrs.items() if v is not None}


def _climatisation_timer_attrs(vehicle: Any) -> dict[str, Any]:
    """Safe, bounded climate timers returned by the car (not inferred)."""
    timers = getattr(vehicle, "climatisation_timers", None)
    return {
        "timers": timers[:12] if isinstance(timers, list) else [],
        "start_timezone": "vehicle_local_not_inferred",
        "meaning": "Configured climate timers, not proof that the car will start",
    }


def _service_expiry_attrs(vehicle: Any) -> dict[str, Any]:
    """Which services end when, soonest first."""
    ordered = sorted(vehicle.service_expiry.items(), key=lambda item: item[1])
    return {
        "services": {name: when.isoformat() for name, when in ordered},
        "count": len(ordered),
    }


def _charging_timer_attrs(vehicle: Any) -> dict[str, Any]:
    attrs: dict[str, Any] = {
        "timers": getattr(vehicle, "charging_timers", None),
        "next_departure": getattr(vehicle, "next_charging_timer_departure", None),
    }
    return {k: v for k, v in attrs.items() if v is not None}


def _model_attrs(vehicle: Any) -> dict[str, Any]:
    """Disclose when Model is sourced from a user nickname, not Audi metadata."""
    return {
        "model_source": getattr(vehicle, "model_source", "unavailable"),
        "model_year": getattr(vehicle, "model_year", "") or None,
    }


def _park_time_attrs(vehicle: Any) -> dict[str, Any]:
    """A GPS-position capture is an approximation, not an engine-off event."""
    source = getattr(vehicle, "park_time_source", "unavailable")
    return {
        "time_source": source,
        "estimated": source == "last_parked_position_capture_estimate",
        "meaning": (
            "Time Audi reported the last parked location; not verified time parked"
            if source == "last_parked_position_capture_estimate"
            else "Vehicle parking clock"
            if source == "vehicle_parking_clock"
            else "No parking timestamp reported"
        ),
    }


SENSOR_DESCRIPTIONS: tuple[AudiSensorEntityDescription, ...] = (
    AudiSensorEntityDescription(
        key="last_update_time",
        attr_key="last_update_time",
        translation_key="last_update_time",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    *_trip_sensors("last_trip", "last_trip", enabled=True),
    AudiSensorEntityDescription(
        key="last_trip_end",
        attr_key="last_trip",
        translation_key="last_trip_end",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=_trip_time("last_trip", "tripEndTimestamp"),
    ),
    *_trip_sensors("trip_totals", "trip_totals", enabled=True, cumulative=True),
    AudiSensorEntityDescription(
        key="shortterm_current",
        attr_key="shortterm_current",
        requires="support_trip_data",
        translation_key="shortterm_current",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda v: _trip_data_value(v, "shortterm_current"),
        extra_attrs_fn=lambda v: _trip_data_attrs(v, "shortterm_current"),
    ),
    AudiSensorEntityDescription(
        key="shortterm_reset",
        attr_key="shortterm_reset",
        requires="support_trip_data",
        translation_key="shortterm_reset",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda v: _trip_data_value(v, "shortterm_reset"),
        extra_attrs_fn=lambda v: _trip_data_attrs(v, "shortterm_reset"),
    ),
    AudiSensorEntityDescription(
        key="longterm_current",
        attr_key="longterm_current",
        requires="support_trip_data",
        translation_key="longterm_current",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda v: _trip_data_value(v, "longterm_current"),
        extra_attrs_fn=lambda v: _trip_data_attrs(v, "longterm_current"),
    ),
    AudiSensorEntityDescription(
        key="longterm_reset",
        attr_key="longterm_reset",
        requires="support_trip_data",
        translation_key="longterm_reset",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda v: _trip_data_value(v, "longterm_reset"),
        extra_attrs_fn=lambda v: _trip_data_attrs(v, "longterm_reset"),
    ),
    AudiSensorEntityDescription(
        key="model",
        attr_key="model",
        translation_key="model",
        extra_attrs_fn=_model_attrs,
    ),
    AudiSensorEntityDescription(
        key="mileage",
        attr_key="mileage",
        translation_key="mileage",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.DISTANCE,
        suggested_display_precision=0,
    ),
    AudiSensorEntityDescription(
        key="service_adblue_distance",
        attr_key="service_adblue_distance",
        translation_key="service_adblue_distance",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        suggested_display_precision=0,
    ),
    AudiSensorEntityDescription(
        key="range",
        state_class=SensorStateClass.MEASUREMENT,
        attr_key="range",
        translation_key="range",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        suggested_display_precision=0,
    ),
    AudiSensorEntityDescription(
        key="hybrid_range",
        requires="has_non_electric_engine",
        attr_key="hybrid_range",
        translation_key="hybrid_range",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        suggested_display_precision=0,
    ),
    AudiSensorEntityDescription(
        key="service_inspection_time",
        attr_key="service_inspection_time",
        translation_key="service_inspection_time",
        native_unit_of_measurement=UnitOfTime.DAYS,
    ),
    AudiSensorEntityDescription(
        key="service_inspection_distance",
        attr_key="service_inspection_distance",
        translation_key="service_inspection_distance",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        suggested_display_precision=0,
    ),
    AudiSensorEntityDescription(
        key="oil_change_time",
        attr_key="oil_change_time",
        translation_key="oil_change_time",
        native_unit_of_measurement=UnitOfTime.DAYS,
    ),
    AudiSensorEntityDescription(
        key="oil_change_distance",
        attr_key="oil_change_distance",
        translation_key="oil_change_distance",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        suggested_display_precision=0,
    ),
    AudiSensorEntityDescription(
        key="oil_level",
        attr_key="oil_level",
        translation_key="oil_level",
        native_unit_of_measurement=PERCENTAGE,
    ),
    AudiSensorEntityDescription(
        key="charging_state",
        attr_key="charging_state",
        translation_key="charging_state",
    ),
    AudiSensorEntityDescription(
        key="charging_mode",
        attr_key="charging_mode",
        translation_key="charging_mode",
    ),
    AudiSensorEntityDescription(
        key="charging_scenario",
        attr_key="charging_scenario",
        translation_key="charging_scenario",
        capability="charging",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    AudiSensorEntityDescription(
        key="battery_care_mode",
        attr_key="battery_care_mode",
        translation_key="battery_care_mode",
        capability="batteryChargingCare",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    AudiSensorEntityDescription(
        key="access_overall_status",
        attr_key="access_overall_status",
        translation_key="access_overall_status",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    AudiSensorEntityDescription(
        key="climatisation_mode",
        attr_key="climatisation_mode",
        translation_key="climatisation_mode",
        capability="climatisation",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    AudiSensorEntityDescription(
        key="charging_type",
        attr_key="charging_type",
        translation_key="charging_type",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    AudiSensorEntityDescription(
        key="energy_flow",
        attr_key="energy_flow",
        translation_key="energy_flow",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    AudiSensorEntityDescription(
        key="max_charge_current",
        attr_key="max_charge_current",
        translation_key="max_charge_current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
    ),
    AudiSensorEntityDescription(
        key="charging_current_limit_a",
        attr_key="charging_current_limit_a",
        translation_key="charging_current_limit_a",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    AudiSensorEntityDescription(
        key="charging_current_limit_mode",
        attr_key="charging_current_limit_mode",
        translation_key="charging_current_limit_mode",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    AudiSensorEntityDescription(
        key="charging_plug_auto_unlock",
        attr_key="charging_plug_auto_unlock",
        capability="charging",
        translation_key="charging_plug_auto_unlock",
    ),
    AudiSensorEntityDescription(
        key="service_expiry_date",
        attr_key="service_expiry_date",
        translation_key="service_expiry_date",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda v: v.service_expiry_date,
        extra_attrs_fn=_service_expiry_attrs,
    ),
    AudiSensorEntityDescription(
        key="vehicle_reported_online",
        attr_key="vehicle_reported_online",
        translation_key="vehicle_reported_online",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    AudiSensorEntityDescription(
        key="vehicle_reported_active",
        attr_key="vehicle_reported_active",
        translation_key="vehicle_reported_active",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    AudiSensorEntityDescription(
        key="primary_engine_type",
        requires="has_non_electric_engine",
        attr_key="primary_engine_type",
        translation_key="primary_engine_type",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    AudiSensorEntityDescription(
        key="secondary_engine_type",
        requires="has_non_electric_engine",
        attr_key="secondary_engine_type",
        translation_key="secondary_engine_type",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    AudiSensorEntityDescription(
        key="primary_engine_range",
        state_class=SensorStateClass.MEASUREMENT,
        requires="has_non_electric_engine",
        attr_key="primary_engine_range",
        translation_key="primary_engine_range",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        suggested_display_precision=0,
    ),
    AudiSensorEntityDescription(
        key="secondary_engine_range",
        state_class=SensorStateClass.MEASUREMENT,
        requires="has_non_electric_engine",
        attr_key="secondary_engine_range",
        translation_key="secondary_engine_range",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        suggested_display_precision=0,
    ),
    AudiSensorEntityDescription(
        key="primary_engine_range_percent",
        requires="has_non_electric_engine",
        attr_key="primary_engine_range_percent",
        translation_key="primary_engine_range_percent",
        native_unit_of_measurement=PERCENTAGE,
    ),
    AudiSensorEntityDescription(
        key="secondary_engine_range_percent",
        requires="has_non_electric_engine",
        attr_key="secondary_engine_range_percent",
        translation_key="secondary_engine_range_percent",
        native_unit_of_measurement=PERCENTAGE,
    ),
    AudiSensorEntityDescription(
        key="charging_power",
        state_class=SensorStateClass.MEASUREMENT,
        attr_key="charging_power",
        translation_key="charging_power",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
    ),
    AudiSensorEntityDescription(
        key="actual_charge_rate",
        attr_key="actual_charge_rate",
        translation_key="actual_charge_rate",
        unit_fn=lambda v: getattr(v, "actual_charge_rate_unit", None),
    ),
    AudiSensorEntityDescription(
        key="tank_level",
        state_class=SensorStateClass.MEASUREMENT,
        attr_key="tank_level",
        translation_key="tank_level",
        native_unit_of_measurement=PERCENTAGE,
    ),
    AudiSensorEntityDescription(
        key="state_of_charge",
        state_class=SensorStateClass.MEASUREMENT,
        attr_key="state_of_charge",
        translation_key="state_of_charge",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
    ),
    AudiSensorEntityDescription(
        key="remaining_charging_time",
        attr_key="remaining_charging_time",
        translation_key="remaining_charging_time",
        unit_fn=lambda v: getattr(v, "remaining_charging_time_unit", None),
    ),
    AudiSensorEntityDescription(
        key="charging_complete_time",
        attr_key="charging_complete_time",
        translation_key="charging_complete_time",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
    AudiSensorEntityDescription(
        key="external_power",
        attr_key="external_power",
        translation_key="external_power",
    ),
    AudiSensorEntityDescription(
        key="plug_led_color",
        attr_key="plug_led_color",
        translation_key="plug_led_color",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    AudiSensorEntityDescription(
        key="doors_trunk_status",
        attr_key="doors_trunk_status",
        translation_key="doors_trunk_status",
    ),
    AudiSensorEntityDescription(
        key="climatisation_state",
        attr_key="climatisation_state",
        translation_key="climatisation_state",
    ),
    AudiSensorEntityDescription(
        key="outdoor_temperature",
        state_class=SensorStateClass.MEASUREMENT,
        attr_key="outdoor_temperature",
        translation_key="outdoor_temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
    ),
    AudiSensorEntityDescription(
        key="park_time",
        attr_key="park_time",
        capability="parkingPosition",
        translation_key="park_time",
        device_class=SensorDeviceClass.TIMESTAMP,
        extra_attrs_fn=_park_time_attrs,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    AudiSensorEntityDescription(
        key="position_last_updated",
        attr_key="position_last_updated",
        capability="parkingPosition",
        translation_key="position_last_updated",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    AudiSensorEntityDescription(
        key="remaining_climatisation_time",
        attr_key="remaining_climatisation_time",
        translation_key="remaining_climatisation_time",
        native_unit_of_measurement=UnitOfTime.MINUTES,
    ),
    AudiSensorEntityDescription(
        key="preheater_duration",
        attr_key="preheater_duration",
        translation_key="preheater_duration",
        native_unit_of_measurement=UnitOfTime.MINUTES,
    ),
    AudiSensorEntityDescription(
        key="preheater_remaining",
        attr_key="preheater_remaining",
        translation_key="preheater_remaining",
        native_unit_of_measurement=UnitOfTime.MINUTES,
    ),
    AudiSensorEntityDescription(
        key="active_charging_profile_target_soc",
        attr_key="active_charging_profile_target_soc",
        translation_key="active_charging_profile_target_soc",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        extra_attrs_fn=_active_profile_attrs,
    ),
    AudiSensorEntityDescription(
        key="active_charging_profile_name",
        attr_key="active_charging_profile_name",
        translation_key="active_charging_profile_name",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    AudiSensorEntityDescription(
        key="active_charging_profile_min_soc",
        attr_key="active_charging_profile_min_soc",
        translation_key="active_charging_profile_min_soc",
        native_unit_of_measurement=PERCENTAGE,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    AudiSensorEntityDescription(
        key="active_charging_profile_max_current",
        attr_key="active_charging_profile_max_current",
        translation_key="active_charging_profile_max_current",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    AudiSensorEntityDescription(
        key="preferred_charging_time_start",
        attr_key="preferred_charging_time_start",
        translation_key="preferred_charging_time_start",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    AudiSensorEntityDescription(
        key="preferred_charging_time_end",
        attr_key="preferred_charging_time_end",
        translation_key="preferred_charging_time_end",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    *_window_sensors(),
    AudiSensorEntityDescription(
        key="warning_light_count",
        attr_key="warning_light_count",
        translation_key="warning_light_count",
        state_class=SensorStateClass.MEASUREMENT,
        extra_attrs_fn=_warning_light_attrs,
    ),
    AudiSensorEntityDescription(
        key="climatisation_timer_enabled_count",
        attr_key="climatisation_timer_enabled_count",
        capability="climatisationTimers",
        translation_key="climatisation_timer_enabled_count",
        extra_attrs_fn=_climatisation_timer_attrs,
    ),
    AudiSensorEntityDescription(
        key="next_climatisation_timer_local",
        attr_key="next_climatisation_timer_local",
        capability="climatisationTimers",
        translation_key="next_climatisation_timer_local",
        extra_attrs_fn=_climatisation_timer_attrs,
    ),
    AudiSensorEntityDescription(
        key="charging_timer_enabled_count",
        attr_key="charging_timer_enabled_count",
        translation_key="charging_timer_enabled_count",
        entity_category=EntityCategory.DIAGNOSTIC,
        extra_attrs_fn=_charging_timer_attrs,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    runtime_data: AudiRuntimeData = config_entry.runtime_data
    entities: list[SensorEntity] = []

    for config_vehicle in runtime_data.account.config_vehicles:
        vehicle = config_vehicle.vehicle
        # Always expose freshness on the device, even if current Audi data is
        # stale or unavailable. Existing Last Update keeps its unique ID.
        entities.extend(
            (
                AudiVehicleFreshnessSensor(runtime_data.coordinator, vehicle),
                AudiVehicleAgeSensor(runtime_data.coordinator, vehicle),
                AudiCloudLastPollSensor(runtime_data.coordinator, vehicle),
            )
        )
        # The service overview is for cars that report more than one service
        # figure; one figure already has its own sensor.
        if service_figures_reported(vehicle) > 1:
            entities.append(
                AudiServiceOverviewSensor(
                    runtime_data.coordinator, vehicle, config_entry
                )
            )
        for description in sensor_descriptions_to_create(hass, vehicle):
            entities.append(AudiSensor(runtime_data.coordinator, description, vehicle))

    # Add account-level API rate limit sensor, attached to the first vehicle.
    if runtime_data.account.config_vehicles:
        first_vehicle = runtime_data.account.config_vehicles[0].vehicle
        entities.append(
            AudiApiRateLimitSensor(
                runtime_data.coordinator,
                config_entry.entry_id,
                first_vehicle,
            )
        )

    async_add_entities(entities)


class AudiSensor(AudiEntity, SensorEntity):
    """Representation of an Audi sensor."""

    entity_description: AudiSensorEntityDescription

    def __init__(
        self,
        coordinator: AudiDataUpdateCoordinator,
        description: AudiSensorEntityDescription,
        vehicle: Any,
    ) -> None:
        super().__init__(coordinator, vehicle)
        self.entity_description = description
        self._attr_unique_id = entity_unique_id(vehicle, "sensor", description.key)

    @property
    def native_value(self) -> Any:
        if self.entity_description.value_fn is not None:
            return self.entity_description.value_fn(self._vehicle)
        return getattr(self._vehicle, self.entity_description.attr_key, None)

    @property
    def native_unit_of_measurement(self) -> str | None:
        if self.entity_description.unit_fn is not None:
            dynamic = self.entity_description.unit_fn(self._vehicle)
            if dynamic is not None:
                return dynamic
        return self.entity_description.native_unit_of_measurement

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if self.entity_description.extra_attrs_fn is not None:
            return self.entity_description.extra_attrs_fn(self._vehicle)
        return None


class _AudiClockAwareSensor(AudiEntity, SensorEntity):
    """Refresh display age even when Audi cloud polling fails."""

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_on_remove(
            async_track_time_interval(
                self.hass, self._async_clock_tick, timedelta(minutes=5)
            )
        )

    @callback
    def _async_clock_tick(self, _now: datetime) -> None:
        self.async_write_ha_state()


class AudiVehicleFreshnessSensor(_AudiClockAwareSensor):
    """Readable freshness status of the newest car telemetry timestamp."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_translation_key = "vehicle_data_freshness"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = ["fresh", "delayed", "stale", "unknown"]

    def __init__(self, coordinator: AudiDataUpdateCoordinator, vehicle: Any) -> None:
        super().__init__(coordinator, vehicle)
        self._attr_unique_id = entity_unique_id(
            vehicle, "sensor", "vehicle_data_freshness"
        )

    @property
    def available(self) -> bool:
        # Stale/offline car data must remain visible instead of going unavailable.
        return True

    @property
    def native_value(self) -> str:
        return vehicle_freshness(getattr(self._vehicle, "last_update_time", None))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        timestamp = usable_vehicle_timestamp(
            getattr(self._vehicle, "last_update_time", None)
        )
        last_success = getattr(self.coordinator, "last_cloud_poll_success", None)
        last_attempt = getattr(self.coordinator, "last_cloud_poll_attempt", None)
        return {
            "vehicle_last_update": timestamp.isoformat() if timestamp else None,
            "vehicle_age_minutes": vehicle_age_minutes(
                getattr(self._vehicle, "last_update_time", None)
            ),
            "cloud_last_successful_poll": (
                last_success.isoformat() if isinstance(last_success, datetime) else None
            ),
            "cloud_last_attempt": (
                last_attempt.isoformat() if isinstance(last_attempt, datetime) else None
            ),
            "last_cloud_poll_succeeded": bool(
                getattr(self.coordinator, "last_update_success", False)
            ),
            "freshness_basis": "newest_vehicle_timestamp_not_all_fields",
        }


class AudiVehicleAgeSensor(_AudiClockAwareSensor):
    """Age of the newest vehicle data timestamp, independent of cloud login."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_translation_key = "vehicle_data_age"
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: AudiDataUpdateCoordinator, vehicle: Any) -> None:
        super().__init__(coordinator, vehicle)
        self._attr_unique_id = entity_unique_id(vehicle, "sensor", "vehicle_data_age")

    @property
    def available(self) -> bool:
        return True

    @property
    def native_value(self) -> int | None:
        return vehicle_age_minutes(getattr(self._vehicle, "last_update_time", None))


class AudiCloudLastPollSensor(AudiEntity, SensorEntity):
    """Last actual successful cloud poll, never mistaken for vehicle telemetry."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_translation_key = "cloud_last_successful_poll"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator: AudiDataUpdateCoordinator, vehicle: Any) -> None:
        super().__init__(coordinator, vehicle)
        self._attr_unique_id = entity_unique_id(
            vehicle, "sensor", "cloud_last_successful_poll"
        )

    @property
    def available(self) -> bool:
        return True

    @property
    def native_value(self) -> datetime | None:
        return getattr(self.coordinator, "last_cloud_poll_success", None)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        attempt = getattr(self.coordinator, "last_cloud_poll_attempt", None)
        return {
            "last_attempt": attempt.isoformat()
            if isinstance(attempt, datetime)
            else None,
            "last_poll_succeeded": bool(
                getattr(self.coordinator, "last_update_success", False)
            ),
        }


class AudiServiceOverviewSensor(AudiEntity, SensorEntity):
    """Maintenance as the car reports it."""

    _attr_translation_key = "service_overview"

    def __init__(
        self, coordinator: AudiDataUpdateCoordinator, vehicle: Any, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator, vehicle)
        self._entry = entry
        self._attr_unique_id = entity_unique_id(vehicle, "sensor", "service_overview")

    @property
    def available(self) -> bool:
        return True

    @property
    def native_value(self) -> str:
        inspection = getattr(self._vehicle, "service_inspection_time", None)
        oil = getattr(self._vehicle, "oil_change_time", None)
        numbers = [
            value
            for value in (inspection, oil)
            if isinstance(value, (float, int)) and not isinstance(value, bool)
        ]
        if any(value <= 0 for value in numbers):
            return "overdue"
        if any(value <= 30 for value in numbers):
            return "due_soon"
        if numbers:
            return "scheduled"
        return "unknown"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "inspection_due_days": getattr(
                self._vehicle, "service_inspection_time", None
            ),
            "inspection_due_km": getattr(
                self._vehicle, "service_inspection_distance", None
            ),
            "oil_service_due_days": getattr(self._vehicle, "oil_change_time", None),
            "oil_service_due_km": getattr(self._vehicle, "oil_change_distance", None),
            "maintenance_source": "Audi vehicleHealthInspection when reported",
        }


class AudiApiRateLimitSensor(AudiEntity, RestoreSensor):
    """Account-level sensor exposing the Vcf-Remaining-Calls API rate limit."""

    _attr_translation_key = "api_requests_remaining"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: AudiDataUpdateCoordinator,
        entry_id: str,
        vehicle: Any,
    ) -> None:
        super().__init__(coordinator, vehicle)
        self._attr_unique_id = f"{entry_id}_api_requests_remaining"
        self._restored_native_value: int | None = None
        self._restored_last_observed: str | None = None

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        api = self.coordinator.account.connection._audi_service._api
        if api.vcf_remaining_calls is not None:
            return

        if (restored := await self.async_get_last_sensor_data()) is not None:
            value = restored.native_value
            if isinstance(value, int) and not isinstance(value, bool):
                self._restored_native_value = value

        if (last_state := await self.async_get_last_state()) is None:
            return

        # Supports the first restart after upgrading from a version that did
        # not previously store SensorExtraStoredData through RestoreSensor.
        if self._restored_native_value is None and last_state.state.isdigit():
            self._restored_native_value = int(last_state.state)

        last_observed = last_state.attributes.get("last_observed")
        if isinstance(last_observed, str):
            self._restored_last_observed = last_observed

    @property
    def native_value(self) -> int | None:
        api = self.coordinator.account.connection._audi_service._api
        if api.vcf_remaining_calls is not None:
            return api.vcf_remaining_calls
        return self._restored_native_value

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        api = self.coordinator.account.connection._audi_service._api
        if api.vcf_remaining_calls_last_observed is not None:
            return {
                "last_observed": api.vcf_remaining_calls_last_observed.isoformat(),
                # Avoid an attribute named "restored"; Home Assistant's frontend treats
                # stateObj.attributes.restored as the marker for a restored/orphaned entity.
                "value_restored": False,
            }

        if self._restored_native_value is None:
            return {}

        attrs: dict[str, Any] = {
            # Avoid an attribute named "restored"; Home Assistant's frontend treats
            # stateObj.attributes.restored as the marker for a restored/orphaned entity.
            "value_restored": True,
        }
        if self._restored_last_observed is not None:
            attrs["last_observed"] = self._restored_last_observed
        return attrs


__all__ = [
    "AudiApiRateLimitSensor",
    "AudiCloudLastPollSensor",
    "AudiSensor",
    "AudiVehicleAgeSensor",
    "AudiVehicleFreshnessSensor",
    "async_setup_entry",
]
