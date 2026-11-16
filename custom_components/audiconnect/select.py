"""Support for Audi Connect selects."""

from __future__ import annotations

from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import AudiRuntimeData
from .audi_entity import AudiEntity, entity_unique_id, should_create_entity
from .coordinator import AudiDataUpdateCoordinator

_ATTR_KEY = "preferred_charge_mode"

# What set_charge_mode accepts. The car also reports availableChargeModes, but
# it comes back empty on at least one vehicle, so this is the fallback rather
# than the source of truth.
_FALLBACK_MODES = ["manual", "timer"]

# What the car sends when it has no answer rather than a mode. A live vehicle
# reported "invalid" while parked, so this is the normal resting state, not an
# error.
_NOT_A_MODE = frozenset({"invalid", "unsupported", "unknown", ""})


def _current_mode(vehicle: Any) -> str | None:
    value = getattr(vehicle, "preferred_charge_mode", None)
    if not isinstance(value, str) or value.lower() in _NOT_A_MODE:
        return None
    return value


def _options_for(vehicle: Any) -> list[str]:
    reported = getattr(vehicle, "available_charge_modes", None)
    usable = [
        m for m in reported or [] if isinstance(m, str) and m.lower() not in _NOT_A_MODE
    ]
    options = usable or list(_FALLBACK_MODES)
    # Home Assistant renders the entity as unknown when current_option is not in
    # options, so a mode the car reports but does not list has to be added
    # rather than merely passed through.
    current = _current_mode(vehicle)
    if current is not None and current not in options:
        options = [*options, current]
    return options


# The two modes the myAudi app offers for the climatisation (ClimatisationMode:
# COMFORT, ECONOMY). The car reports them in lower case.
_CLIMATISATION_MODES = ["comfort", "economy"]


def climatisation_mode_supported(vehicle: Any) -> bool:
    """A modern account, and the car has not said it has no mode choice."""
    service = getattr(vehicle, "_audi_service", None)
    if not getattr(service, "uses_auth0", False):
        return False
    flags = getattr(vehicle, "climatisation_supports", None)
    return not (
        isinstance(flags, dict) and flags.get("supportsClimatisationMode") is False
    )


_PROFILE_CURRENTS = ["max", "reduced"]


def profile_current_supported(vehicle: Any) -> bool:
    """A modern account, and the car has not said it has no current choice."""
    service = getattr(vehicle, "_audi_service", None)
    if not getattr(service, "uses_auth0", False):
        return False
    flags = getattr(vehicle, "charging_profiles_supports", None)
    return not (
        isinstance(flags, dict) and flags.get("supportsMaxChargingCurrent") is False
    )


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    runtime_data: AudiRuntimeData = config_entry.runtime_data
    entities: list[SelectEntity] = [
        AudiChargeModeSelect(runtime_data.coordinator, config_vehicle.vehicle)
        for config_vehicle in runtime_data.account.config_vehicles
        if should_create_entity(
            hass, "select", "charge_mode", config_vehicle.vehicle, _ATTR_KEY
        )
    ]
    entities.extend(
        AudiClimatisationModeSelect(runtime_data.coordinator, config_vehicle.vehicle)
        for config_vehicle in runtime_data.account.config_vehicles
        if should_create_entity(
            hass,
            "select",
            "climatisation_mode",
            config_vehicle.vehicle,
            "climatisation_mode",
            configured=climatisation_mode_supported(config_vehicle.vehicle),
        )
    )
    entities.extend(
        AudiProfileCurrentSelect(runtime_data.coordinator, config_vehicle.vehicle)
        for config_vehicle in runtime_data.account.config_vehicles
        if should_create_entity(
            hass,
            "select",
            "profile_charging_current",
            config_vehicle.vehicle,
            "active_charging_profile_max_current",
            configured=profile_current_supported(config_vehicle.vehicle),
        )
    )
    async_add_entities(entities)


class AudiChargeModeSelect(AudiEntity, SelectEntity):
    """The charge mode the car is set to.

    Reads preferredChargeMode, not the chargeMode of the charge in progress:
    set_charge_mode writes the former, and the two disagree whenever a charge is
    running under a different mode than the one configured.
    """

    _backing_attr = _ATTR_KEY

    _attr_translation_key = "charge_mode"
    _attr_icon = "mdi:battery-clock"

    def __init__(
        self,
        coordinator: AudiDataUpdateCoordinator,
        vehicle: Any,
    ) -> None:
        super().__init__(coordinator, vehicle)
        self._attr_unique_id = entity_unique_id(vehicle, "select", "charge_mode")

    @property
    def options(self) -> list[str]:
        return _options_for(self._vehicle)

    @property
    def current_option(self) -> str | None:
        return _current_mode(self._vehicle)

    async def async_select_option(self, option: str) -> None:
        connection = self.coordinator.account.connection
        if not await connection.set_charge_mode(self._vehicle.vin, option):
            raise HomeAssistantError(
                f"Failed to set charge mode to {option}; see the log for details"
            )
        await self.coordinator.async_request_refresh()


class AudiClimatisationModeSelect(AudiEntity, SelectEntity):
    """Comfort or economy for the climatisation, stored in the car.

    Written with the same request as the zones and the target temperature, so
    it changes the stored setting and does not start the climatisation.
    """

    _backing_attr = "climatisation_mode"

    _attr_translation_key = "climatisation_mode"
    _attr_icon = "mdi:thermostat-auto"

    def __init__(
        self,
        coordinator: AudiDataUpdateCoordinator,
        vehicle: Any,
    ) -> None:
        super().__init__(coordinator, vehicle)
        self._attr_unique_id = entity_unique_id(vehicle, "select", "climatisation_mode")

    @property
    def options(self) -> list[str]:
        options = list(_CLIMATISATION_MODES)
        current = self.current_option
        # A mode the car reports but this list lacks has to be shown, or Home
        # Assistant renders the entity as unknown.
        if current is not None and current not in options:
            options.append(current)
        return options

    @property
    def current_option(self) -> str | None:
        value = getattr(self._vehicle, "climatisation_mode", None)
        if not isinstance(value, str) or value.lower() in _NOT_A_MODE:
            return None
        return value.lower()

    async def async_select_option(self, option: str) -> None:
        connection = self.coordinator.account.connection
        if not await connection.set_climatisation_setting(
            self._vehicle.vin, "climatisationMode", option
        ):
            raise HomeAssistantError(
                f"Failed to set climatisation mode to {option}; see the log for details"
            )
        await self.coordinator.async_request_refresh()


class AudiProfileCurrentSelect(AudiEntity, SelectEntity):
    """The charging current of the profile the car stands in: maximum or reduced.

    Written into the profile the car is parked in, with the whole profile sent
    back unchanged apart from this one field.
    """

    _backing_attr = "active_charging_profile_max_current"

    _attr_translation_key = "profile_charging_current"
    _attr_icon = "mdi:current-ac"
    _attr_options = _PROFILE_CURRENTS

    def __init__(
        self,
        coordinator: AudiDataUpdateCoordinator,
        vehicle: Any,
    ) -> None:
        super().__init__(coordinator, vehicle)
        self._attr_unique_id = entity_unique_id(
            vehicle, "select", "profile_charging_current"
        )

    @property
    def current_option(self) -> str | None:
        value = getattr(self._vehicle, "active_charging_profile_max_current", None)
        if isinstance(value, str) and value.lower() in _PROFILE_CURRENTS:
            return value.lower()
        return None

    async def async_select_option(self, option: str) -> None:
        connection = self.coordinator.account.connection
        if not await connection.set_profile_charging_current(
            self._vehicle.vin, None, option
        ):
            raise HomeAssistantError(
                f"Failed to set the profile charging current to {option}; "
                "see the log for details"
            )
        await self.coordinator.async_request_refresh()


__all__ = [
    "AudiChargeModeSelect",
    "AudiClimatisationModeSelect",
    "AudiProfileCurrentSelect",
    "async_setup_entry",
]
