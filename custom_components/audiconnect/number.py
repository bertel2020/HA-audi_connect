"""Support for Audi Connect numbers."""

from __future__ import annotations

from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import Any

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import AudiRuntimeData
from .errors import command_error
from .audi_entity import (
    AssumedValueMixin,
    AudiEntity,
    entity_unique_id,
    should_create_entity,
)
from .coordinator import AudiDataUpdateCoordinator

# The Cariad API rejects anything outside 20-100 and only accepts 5% steps.
# One command to the car at a time: it answers slowly and Audi limits the requests.
PARALLEL_UPDATES = 1

_SOC_MIN = 20
_SOC_MAX = 100
_SOC_STEP = 5


@dataclass(frozen=True, kw_only=True)
class AudiNumberEntityDescription(NumberEntityDescription):
    """Describes an Audi number entity."""

    attr_key: str
    set_value_fn: Callable[[Any, str, int], Coroutine[Any, Any, bool]]


NUMBER_DESCRIPTIONS: tuple[AudiNumberEntityDescription, ...] = (
    AudiNumberEntityDescription(
        key="target_state_of_charge",
        attr_key="target_state_of_charge",
        translation_key="target_state_of_charge",
        device_class=NumberDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        native_min_value=_SOC_MIN,
        native_max_value=_SOC_MAX,
        native_step=_SOC_STEP,
        mode=NumberMode.SLIDER,
        set_value_fn=lambda conn, vin, value: conn.set_target_state_of_charge(
            vin, value
        ),
    ),
    AudiNumberEntityDescription(
        key="active_charging_profile_target_soc",
        attr_key="active_charging_profile_target_soc",
        translation_key="active_charging_profile_target_soc",
        device_class=NumberDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        native_min_value=_SOC_MIN,
        native_max_value=_SOC_MAX,
        native_step=_SOC_STEP,
        mode=NumberMode.SLIDER,
        # No profile id: the service resolves vehiclePositionedInProfileID, so
        # this follows the car between locations.
        set_value_fn=lambda conn, vin, value: conn.set_location_charge_target(
            vin, None, value
        ),
    ),
)


def _limit(vehicle: Any, name: str, default: int) -> int:
    """A limit the car reported, else the range the API is known to accept."""
    value = getattr(vehicle, name, None)
    return value if isinstance(value, int) and not isinstance(value, bool) else default


def _profiles(vehicle: Any) -> list[dict[str, Any]]:
    """Return the location charging profiles the car reports, if any."""
    profiles = getattr(vehicle, "charging_profiles", None)
    if not isinstance(profiles, list):
        return []
    return [p for p in profiles if isinstance(p, dict) and p.get("id") is not None]


def profiles_with_a_target(vehicle: Any) -> list[dict[str, Any]]:
    """The profiles that carry a charge target.

    A car whose profiles carry none (the A6 reports that it does not support
    one) would get a slider that can never show or set a value.
    """
    return [p for p in _profiles(vehicle) if p.get("targetSOC_pct") is not None]


def profile_slider_wanted(vehicle: Any) -> bool:
    """Whether the car's profiles can carry a target for a slider to show.

    A car that lists profiles but gives none of them a target (the A6 says so
    with targetSOC_pct null) never will, so the slider would stay unavailable
    for good. That is the car's own statement, so a registry entry from an
    earlier poll must not bring the slider back. A poll with no profiles at all
    says nothing and leaves the decision to the usual rules.
    """
    profiles = _profiles(vehicle)
    return not profiles or bool(profiles_with_a_target(vehicle))


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    runtime_data: AudiRuntimeData = config_entry.runtime_data
    entities: list[NumberEntity] = [
        AudiNumber(runtime_data.coordinator, description, vehicle)
        for config_vehicle in runtime_data.account.config_vehicles
        for description in NUMBER_DESCRIPTIONS
        if should_create_entity(
            hass,
            "number",
            description.key,
            vehicle := config_vehicle.vehicle,
            description.attr_key,
            configured=(
                description.key != "active_charging_profile_target_soc"
                or profile_slider_wanted(vehicle)
            ),
        )
    ]
    entities.extend(
        AudiProfileChargeTarget(
            runtime_data.coordinator, config_vehicle.vehicle, profile
        )
        for config_vehicle in runtime_data.account.config_vehicles
        for profile in profiles_with_a_target(config_vehicle.vehicle)
    )
    async_add_entities(entities)


class AudiChargeTargetEntity(AssumedValueMixin, AudiEntity, NumberEntity):
    """Shared slider behaviour for the charge-target numbers."""

    _attr_device_class = NumberDeviceClass.BATTERY
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_native_max_value = _SOC_MAX
    _attr_mode = NumberMode.SLIDER

    _attr_native_min_value = _SOC_MIN
    _attr_native_step = _SOC_STEP

    async def _write(
        self,
        set_value_fn: Callable[[Any, str, int], Coroutine[Any, Any, bool]],
        value: float,
    ) -> None:
        connection = self.coordinator.account.connection
        started = self._command_started()
        if not await set_value_fn(connection, self._vehicle.vin, int(value)):
            raise command_error(
                "number_failed", entity=self.entity_id or self.unique_id
            )
        self._assume(float(int(value)))
        await self._refresh_after_command(started)


class AudiNumber(AudiChargeTargetEntity):
    """A number backed by a single vehicle attribute."""

    entity_description: AudiNumberEntityDescription

    def __init__(
        self,
        coordinator: AudiDataUpdateCoordinator,
        description: AudiNumberEntityDescription,
        vehicle: Any,
    ) -> None:
        super().__init__(coordinator, vehicle)
        self.entity_description = description
        self._attr_unique_id = entity_unique_id(vehicle, "number", description.key)

    # Only the global target has limits in the car's capabilities. The location
    # profiles report none, so they keep the range the API is known to take.
    @property
    def native_min_value(self) -> float:
        if self.entity_description.key != "target_state_of_charge":
            return _SOC_MIN
        return _limit(self._vehicle, "charge_target_min", _SOC_MIN)

    @property
    def native_step(self) -> float:
        if self.entity_description.key != "target_state_of_charge":
            return _SOC_STEP
        return _limit(self._vehicle, "charge_target_step", _SOC_STEP)

    def _reported_value(self) -> float | None:
        value = getattr(self._vehicle, self.entity_description.attr_key, None)
        return None if value is None else float(value)

    @property
    def native_value(self) -> float | None:
        return self._shown_value()

    async def async_set_native_value(self, value: float) -> None:
        await self._write(self.entity_description.set_value_fn, value)


class AudiProfileChargeTarget(AudiChargeTargetEntity):
    """The charge target of one location profile.

    Keyed on the profile id, never the name: names are editable in the car and
    the myAudi app, so a name-keyed unique_id would orphan the entity on a
    rename.
    """

    def __init__(
        self,
        coordinator: AudiDataUpdateCoordinator,
        vehicle: Any,
        profile: dict[str, Any],
    ) -> None:
        super().__init__(coordinator, vehicle)
        self._profile_id = profile["id"]
        self._attr_translation_key = "charge_profile_target"
        self._attr_translation_placeholders = {
            "profile": profile.get("name") or f"Profile {self._profile_id}"
        }
        self._attr_unique_id = entity_unique_id(
            vehicle, "number", f"charge_profile_{self._profile_id}_target_soc"
        )

    @property
    def _profile(self) -> dict[str, Any] | None:
        return next(
            (p for p in _profiles(self._vehicle) if p["id"] == self._profile_id), None
        )

    @property
    def available(self) -> bool:
        # The profile can be deleted in the car; say so rather than showing a
        # stale target for a location that no longer exists.
        return super().available and self._profile is not None

    def _reported_value(self) -> float | None:
        profile = self._profile
        if profile is None:
            return None
        value = profile.get("targetSOC_pct")
        return None if value is None else float(value)

    @property
    def native_value(self) -> float | None:
        return self._shown_value()

    async def async_set_native_value(self, value: float) -> None:
        await self._write(
            lambda conn, vin, soc: conn.set_location_charge_target(
                vin, self._profile_id, soc
            ),
            value,
        )


__all__ = ["AudiNumber", "AudiProfileChargeTarget", "async_setup_entry"]
