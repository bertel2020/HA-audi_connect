"""Support for Audi Connect binary sensors."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import AudiRuntimeData
from .audi_entity import AudiEntity, entity_unique_id, should_create_entity
from .coordinator import AudiDataUpdateCoordinator


# Read-only: the coordinator fetches, so the entities never need to queue.
PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class AudiBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes an Audi binary sensor entity."""

    attr_key: str


BINARY_SENSOR_DESCRIPTIONS: tuple[AudiBinarySensorEntityDescription, ...] = (
    AudiBinarySensorEntityDescription(
        key="plug_state",
        attr_key="plug_state",
        translation_key="plug_state",
        device_class=BinarySensorDeviceClass.PLUG,
    ),
    AudiBinarySensorEntityDescription(
        key="plug_lock_state",
        attr_key="plug_lock_state",
        translation_key="plug_lock_state",
        device_class=BinarySensorDeviceClass.LOCK,
    ),
    AudiBinarySensorEntityDescription(
        key="glass_surface_heating",
        attr_key="glass_surface_heating",
        translation_key="glass_surface_heating",
        device_class=BinarySensorDeviceClass.RUNNING,
    ),
    AudiBinarySensorEntityDescription(
        key="sun_roof",
        attr_key="sun_roof",
        translation_key="sun_roof",
        device_class=BinarySensorDeviceClass.WINDOW,
    ),
    AudiBinarySensorEntityDescription(
        key="roof_cover",
        attr_key="roof_cover",
        translation_key="roof_cover",
        device_class=BinarySensorDeviceClass.WINDOW,
    ),
    AudiBinarySensorEntityDescription(
        key="parking_light",
        attr_key="parking_light",
        translation_key="parking_light",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    AudiBinarySensorEntityDescription(
        key="any_window_open",
        attr_key="any_window_open",
        translation_key="any_window_open",
        device_class=BinarySensorDeviceClass.WINDOW,
    ),
    AudiBinarySensorEntityDescription(
        key="any_door_unlocked",
        attr_key="any_door_unlocked",
        translation_key="any_door_unlocked",
        device_class=BinarySensorDeviceClass.LOCK,
    ),
    AudiBinarySensorEntityDescription(
        key="any_door_open",
        attr_key="any_door_open",
        translation_key="any_door_open",
        device_class=BinarySensorDeviceClass.DOOR,
    ),
    AudiBinarySensorEntityDescription(
        key="trunk_unlocked",
        attr_key="trunk_unlocked",
        translation_key="trunk_unlocked",
        device_class=BinarySensorDeviceClass.LOCK,
    ),
    AudiBinarySensorEntityDescription(
        key="trunk_open",
        attr_key="trunk_open",
        translation_key="trunk_open",
        device_class=BinarySensorDeviceClass.DOOR,
    ),
    AudiBinarySensorEntityDescription(
        key="hood_open",
        attr_key="hood_open",
        translation_key="hood_open",
        device_class=BinarySensorDeviceClass.DOOR,
    ),
    AudiBinarySensorEntityDescription(
        key="left_front_door_open",
        attr_key="left_front_door_open",
        translation_key="left_front_door_open",
        device_class=BinarySensorDeviceClass.DOOR,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    AudiBinarySensorEntityDescription(
        key="right_front_door_open",
        attr_key="right_front_door_open",
        translation_key="right_front_door_open",
        device_class=BinarySensorDeviceClass.DOOR,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    AudiBinarySensorEntityDescription(
        key="left_rear_door_open",
        attr_key="left_rear_door_open",
        translation_key="left_rear_door_open",
        device_class=BinarySensorDeviceClass.DOOR,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    AudiBinarySensorEntityDescription(
        key="right_rear_door_open",
        attr_key="right_rear_door_open",
        translation_key="right_rear_door_open",
        device_class=BinarySensorDeviceClass.DOOR,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    AudiBinarySensorEntityDescription(
        key="left_front_window_open",
        attr_key="left_front_window_open",
        translation_key="left_front_window_open",
        device_class=BinarySensorDeviceClass.WINDOW,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    AudiBinarySensorEntityDescription(
        key="right_front_window_open",
        attr_key="right_front_window_open",
        translation_key="right_front_window_open",
        device_class=BinarySensorDeviceClass.WINDOW,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    AudiBinarySensorEntityDescription(
        key="left_rear_window_open",
        attr_key="left_rear_window_open",
        translation_key="left_rear_window_open",
        device_class=BinarySensorDeviceClass.WINDOW,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    AudiBinarySensorEntityDescription(
        key="right_rear_window_open",
        attr_key="right_rear_window_open",
        translation_key="right_rear_window_open",
        device_class=BinarySensorDeviceClass.WINDOW,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    AudiBinarySensorEntityDescription(
        key="braking_status",
        attr_key="braking_status",
        translation_key="braking_status",
    ),
    AudiBinarySensorEntityDescription(
        key="active_charging_profile_uses_preferred_times",
        attr_key="active_charging_profile_uses_preferred_times",
        translation_key="active_charging_profile_uses_preferred_times",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    AudiBinarySensorEntityDescription(
        key="warning_lights",
        attr_key="warning_lights",
        translation_key="warning_lights",
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    AudiBinarySensorEntityDescription(
        key="parking_brake",
        attr_key="parking_brake",
        translation_key="parking_brake",
    ),
    AudiBinarySensorEntityDescription(
        key="oil_level_binary",
        attr_key="oil_level_binary",
        translation_key="oil_level_binary",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    AudiBinarySensorEntityDescription(
        key="is_moving",
        attr_key="is_moving",
        translation_key="is_moving",
        device_class=BinarySensorDeviceClass.MOVING,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    runtime_data: AudiRuntimeData = config_entry.runtime_data
    entities = [
        AudiBinarySensor(runtime_data.coordinator, description, vehicle)
        for config_vehicle in runtime_data.account.config_vehicles
        for description in BINARY_SENSOR_DESCRIPTIONS
        if should_create_entity(
            hass,
            "binary_sensor",
            description.key,
            vehicle := config_vehicle.vehicle,
            description.attr_key,
        )
    ]
    async_add_entities(entities)


class AudiBinarySensor(AudiEntity, BinarySensorEntity):
    """Representation of an Audi binary sensor."""

    entity_description: AudiBinarySensorEntityDescription

    def __init__(
        self,
        coordinator: AudiDataUpdateCoordinator,
        description: AudiBinarySensorEntityDescription,
        vehicle: Any,
    ) -> None:
        super().__init__(coordinator, vehicle)
        self.entity_description = description
        self._attr_unique_id = entity_unique_id(
            vehicle, "binary_sensor", description.key
        )

    @property
    def is_on(self) -> bool | None:
        val = getattr(self._vehicle, self.entity_description.attr_key, None)
        if isinstance(val, (bool, list)):
            return bool(val)
        elif isinstance(val, str):
            return val != "Normal"
        return val

    @property
    def extra_state_attributes(self) -> dict[str, str] | None:
        if self.entity_description.key == "parking_light":
            return getattr(self._vehicle, "parking_light_sides", None)
        return None


__all__ = ["AudiBinarySensor", "async_setup_entry"]
