"""Audi Connect integration."""

from __future__ import annotations

import logging
import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
)
from homeassistant.exceptions import ConfigEntryAuthFailed, ServiceValidationError
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import DeviceEntry
from homeassistant.helpers.typing import ConfigType

from .audi_account import (
    SERVICE_EXECUTE_VEHICLE_ACTION,
    SERVICE_EXECUTE_VEHICLE_ACTION_SCHEMA,
    SERVICE_PROBE_API,
    SERVICE_PROBE_API_SCHEMA,
    SERVICE_REFRESH_CLOUD_DATA,
    SERVICE_REFRESH_VEHICLE_DATA,
    SERVICE_REFRESH_VEHICLE_DATA_SCHEMA,
    SERVICE_SET_CHARGE_MODE,
    SERVICE_SET_CHARGE_MODE_SCHEMA,
    SERVICE_SET_LOCATION_CHARGE_TARGET,
    SERVICE_SET_LOCATION_CHARGE_TARGET_SCHEMA,
    SERVICE_SET_TARGET_SOC,
    SERVICE_SET_TARGET_SOC_SCHEMA,
    SERVICE_START_AUXILIARY_HEATING,
    SERVICE_START_AUXILIARY_HEATING_SCHEMA,
    SERVICE_START_CLIMATE_CONTROL,
    SERVICE_START_CLIMATE_CONTROL_SCHEMA,
    SERVICE_START_ENGINE,
    SERVICE_START_ENGINE_SCHEMA,
    SERVICE_STOP_ENGINE,
    SERVICE_STOP_ENGINE_SCHEMA,
    SERVICE_CREATE_CLIMATISATION_TIMER,
    SERVICE_CREATE_CLIMATISATION_TIMER_SCHEMA,
    SERVICE_DELETE_CLIMATISATION_TIMER,
    SERVICE_SET_CLIMATISATION_TIMER_ENABLED,
    SERVICE_SET_CLIMATISATION_TIMER_ENABLED_SCHEMA,
    SERVICE_DELETE_CLIMATISATION_TIMER_SCHEMA,
    SERVICE_TEST_CLIMATISATION_WRITE,
    SERVICE_TEST_CLIMATISATION_WRITE_SCHEMA,
    AudiAccount,
    _single_device_id,
)
from .const import (
    CONF_API_LEVEL,
    CONF_DEVICE_ID,
    CONF_PASSWORD,
    CONF_REFRESH_TOKEN,
    CONF_REGION,
    CONF_SCAN_INITIAL,
    CONF_USERNAME,
    DEFAULT_API_LEVEL,
    DOMAIN,
    PLATFORMS,
    uses_auth0,
)
from .capability_jobs import BASE_SELECTIVE_JOBS
from .audi_entity import _english_entity_names
from .card import async_register_card
from .coordinator import AudiDataUpdateCoordinator
from .diagnostics_payload import redact
from .local_extensions import DEALER_FIELDS, update_local_dealer_options

_LOGGER = logging.getLogger(__name__)

SERVICE_PROBE_API_PATHS = "probe_api_paths"
SERVICE_SET_LOCAL_DEALER = "set_local_dealer"
PROBE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_DEVICE_ID): cv.string,
        vol.Optional("extended", default=False): bool,
    }
)
LOCAL_DEALER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_DEVICE_ID): cv.string,
        vol.Optional("clear", default=False): bool,
        **{vol.Optional(field): cv.string for field in DEALER_FIELDS},
    }
)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Migrate config entry to a newer version."""
    _LOGGER.debug("Migrating from version %s", config_entry.version)

    if config_entry.version == 1:
        # v1 -> v2:
        # - Service calls changed from manual VIN text input to device selector
        #   dropdown. Remove any devices that have lost all their entities
        #   (orphaned from a previous bad state).
        # - Options flow cleanup: "scan_active" removed (HA built-in "Enable
        #   polling" toggle replaces it); "api_level" moved from options to
        #   reconfigure flow (stored in data).
        device_registry = dr.async_get(hass)
        entity_registry = er.async_get(hass)
        devices = dr.async_entries_for_config_entry(
            device_registry, config_entry.entry_id
        )
        for device_entry in devices:
            if not er.async_entries_for_device(
                entity_registry, device_entry.id, include_disabled_entities=True
            ):
                _LOGGER.info(
                    "Migration v1->v2: removing orphaned device %s (no entities)",
                    device_entry.id,
                )
                device_registry.async_remove_device(device_entry.id)

        # Promote api_level from options → data if it was overridden there,
        # then strip removed keys from options.
        new_data = {**config_entry.data}
        new_options = {**config_entry.options}

        if CONF_API_LEVEL in new_options:
            new_data[CONF_API_LEVEL] = int(new_options.pop(CONF_API_LEVEL))
        elif CONF_API_LEVEL not in new_data:
            new_data[CONF_API_LEVEL] = DEFAULT_API_LEVEL

        new_options.pop("scan_active", None)

        hass.config_entries.async_update_entry(
            config_entry, version=2, data=new_data, options=new_options
        )

    if config_entry.version == 2:
        # v2 -> v3:
        # Drop credentials in regions that require interactive authentication.
        new_data = {**config_entry.data}
        if uses_auth0(new_data.get(CONF_REGION)) and not new_data.get(
            CONF_REFRESH_TOKEN
        ):
            new_data.pop(CONF_PASSWORD, None)
            new_data.pop(CONF_USERNAME, None)
        hass.config_entries.async_update_entry(config_entry, version=3, data=new_data)

    _LOGGER.info("Migration to version %s successful", config_entry.version)
    return True


@dataclass
class AudiRuntimeData:
    """Runtime data for each config entry."""

    account: AudiAccount
    coordinator: AudiDataUpdateCoordinator
    options_snapshot: dict[str, Any] = field(default_factory=dict)
    data_snapshot: dict[str, Any] = field(default_factory=dict)


def _resolve_device_to_vin(hass: HomeAssistant, device_id: str) -> str | None:
    """Resolve a Home Assistant device registry ID to the vehicle VIN."""
    device_registry = dr.async_get(hass)
    device_entry = device_registry.async_get(device_id)
    if device_entry is None:
        return None
    for domain, identifier in device_entry.identifiers:
        if domain == DOMAIN:
            return identifier
    return None


def _get_account_for_vin(hass: HomeAssistant, vin: str) -> AudiAccount | None:
    """Find the AudiAccount that owns a given VIN across all config entries."""
    vin_lower = vin.lower()
    for entry in hass.config_entries.async_entries(DOMAIN):
        runtime_data: AudiRuntimeData | None = getattr(entry, "runtime_data", None)
        if runtime_data is None:
            continue
        for vehicle_data in runtime_data.account.config_vehicles:
            if vehicle_data.vehicle and vehicle_data.vehicle.vin.lower() == vin_lower:
                return runtime_data.account
    return None


SERVICE_PROBE_API_PATHS = "probe_api_paths"
SERVICE_SET_LOCAL_DEALER = "set_local_dealer"
PROBE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_DEVICE_ID): _single_device_id,
        vol.Optional("extended", default=False): bool,
    }
)
LOCAL_DEALER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_DEVICE_ID): _single_device_id,
        vol.Optional("clear", default=False): bool,
        **{vol.Optional(field): cv.string for field in DEALER_FIELDS},
    }
)

_PROBE_PATH = re.compile(r"[A-Za-z0-9_/\-.?=&,{}]+")


def _resolve_service_call(
    hass: HomeAssistant, service: ServiceCall
) -> tuple[str, AudiAccount]:
    """Resolve device_id from a service call to (vin, account).

    Raises ServiceValidationError so the caller sees the problem in the UI.
    """
    device_id = service.data[CONF_DEVICE_ID]
    vin = _resolve_device_to_vin(hass, device_id)
    if vin is None:
        raise ServiceValidationError(f"No Audi vehicle found for device {device_id}")
    account = _get_account_for_vin(hass, vin)
    if account is None:
        raise ServiceValidationError(
            f"The Audi Connect account for device {device_id} is not loaded"
        )
    return vin, account


def _get_all_coordinators(hass: HomeAssistant) -> list[AudiDataUpdateCoordinator]:
    """Get coordinators from all loaded config entries."""
    coordinators: list[AudiDataUpdateCoordinator] = []
    for entry in hass.config_entries.async_entries(DOMAIN):
        runtime_data: AudiRuntimeData | None = getattr(entry, "runtime_data", None)
        if runtime_data is not None:
            coordinators.append(runtime_data.coordinator)
    return coordinators


def _reloadable_data(config_entry: ConfigEntry) -> dict[str, Any]:
    """Entry data that the running integration is configured from.

    The refresh token is excluded: it rotates on its own during normal operation
    and reloading on every rotation would tear the integration down for nothing.
    """
    return {k: v for k, v in config_entry.data.items() if k != CONF_REFRESH_TOKEN}


async def _async_update_listener(
    hass: HomeAssistant, config_entry: ConfigEntry
) -> None:
    """Reload when the configuration changed, in options *or* in data.

    The S-PIN, region and API level live in entry data, not in options, so
    comparing options alone would silently skip the reload a reconfigure needs.
    Home Assistant reloads on its own today, but from 2026.12 it defers to this
    listener whenever one is registered, and the missed reload would surface as
    "my new S-PIN is ignored until I restart".
    """
    runtime_data: AudiRuntimeData | None = getattr(config_entry, "runtime_data", None)
    if (
        runtime_data is not None
        and runtime_data.options_snapshot == dict(config_entry.options)
        and runtime_data.data_snapshot == _reloadable_data(config_entry)
    ):
        # Only the refresh token rotated; nothing the running setup depends on.
        return
    await hass.config_entries.async_reload(config_entry.entry_id)


def _vehicle_service(
    hass: HomeAssistant,
    method: str,
    *,
    pass_call: bool = True,
) -> Callable[[ServiceCall], Awaitable[None]]:
    """Build a handler that resolves the vehicle and calls ``account.<method>``."""

    async def _handler(service: ServiceCall) -> None:
        vin, account = _resolve_service_call(hass, service)
        func = getattr(account, method)
        if pass_call:
            await func(vin, service)
        else:
            await func(vin)

    return _handler


def _async_register_services(hass: HomeAssistant) -> None:
    """Register the integration's services (once, from async_setup)."""

    async def _handle_refresh_cloud_data(service: ServiceCall) -> None:
        for coordinator in _get_all_coordinators(hass):
            await coordinator.async_request_refresh()

    hass.services.async_register(
        DOMAIN, SERVICE_REFRESH_CLOUD_DATA, _handle_refresh_cloud_data
    )

    async def _handle_probe_api(service: ServiceCall) -> ServiceResponse:
        """Read-only discovery: ask the API for jobs or a path and return the answer."""
        vin, account = _resolve_service_call(hass, service)
        preset = service.data.get("graphql")
        if preset is not None:
            result = await account.connection.probe_graphql(preset, vin)
            pattern = re.compile(re.escape(vin), re.IGNORECASE)
            return {"query": f"graphql:{preset}", **redact(result, pattern)}
        path = service.data.get("path")
        if path is not None:
            if not _PROBE_PATH.fullmatch(path) or ".." in path:
                raise ServiceValidationError(
                    "path may only contain letters, digits and /_-.?=&,"
                )
            query = path
        else:
            jobs = service.data.get("jobs") or list(BASE_SELECTIVE_JOBS)
            query = "selectivestatus?jobs=" + ",".join(jobs)
        result = await account.connection.probe(vin, query)
        pattern = re.compile(re.escape(vin), re.IGNORECASE)
        return {"query": query, **redact(result, pattern)}

    async def _handle_probe_api_paths(service: ServiceCall) -> None:
        """Explicit user action. A diagnostics download never triggers probes."""
        vin, account = _resolve_service_call(hass, service)
        await account.connection.probe_read_only_api(
            vin, extended=service.data.get("extended", False)
        )

    async def _handle_set_local_dealer(service: ServiceCall) -> None:
        """Opt-in local metadata only; no Audi network calls."""
        vin, account = _resolve_service_call(hass, service)
        fields = {
            key: service.data[key] for key in DEALER_FIELDS if key in service.data
        }
        current = dict(account.config_entry.options)
        options = update_local_dealer_options(
            current, vin, fields, clear=service.data.get("clear", False)
        )
        if options != current:
            hass.config_entries.async_update_entry(
                account.config_entry, options=options
            )

    hass.services.async_register(
        DOMAIN,
        SERVICE_PROBE_API,
        _handle_probe_api,
        schema=SERVICE_PROBE_API_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_PROBE_API_PATHS,
        _handle_probe_api_paths,
        schema=PROBE_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_LOCAL_DEALER,
        _handle_set_local_dealer,
        schema=LOCAL_DEALER_SCHEMA,
    )

    vehicle_services: tuple[tuple[str, vol.Schema, str, bool], ...] = (
        (
            SERVICE_REFRESH_VEHICLE_DATA,
            SERVICE_REFRESH_VEHICLE_DATA_SCHEMA,
            "refresh_vehicle_data",
            False,
        ),
        (
            SERVICE_EXECUTE_VEHICLE_ACTION,
            SERVICE_EXECUTE_VEHICLE_ACTION_SCHEMA,
            "execute_vehicle_action",
            True,
        ),
        (
            SERVICE_START_CLIMATE_CONTROL,
            SERVICE_START_CLIMATE_CONTROL_SCHEMA,
            "start_climate_control",
            True,
        ),
        (
            SERVICE_START_AUXILIARY_HEATING,
            SERVICE_START_AUXILIARY_HEATING_SCHEMA,
            "start_auxiliary_heating",
            True,
        ),
        (
            SERVICE_SET_LOCATION_CHARGE_TARGET,
            SERVICE_SET_LOCATION_CHARGE_TARGET_SCHEMA,
            "set_location_charge_target",
            True,
        ),
        (
            SERVICE_SET_CHARGE_MODE,
            SERVICE_SET_CHARGE_MODE_SCHEMA,
            "set_charge_mode",
            True,
        ),
        (SERVICE_SET_TARGET_SOC, SERVICE_SET_TARGET_SOC_SCHEMA, "set_target_soc", True),
        (SERVICE_START_ENGINE, SERVICE_START_ENGINE_SCHEMA, "start_engine", False),
        (SERVICE_STOP_ENGINE, SERVICE_STOP_ENGINE_SCHEMA, "stop_engine", False),
        (
            SERVICE_CREATE_CLIMATISATION_TIMER,
            SERVICE_CREATE_CLIMATISATION_TIMER_SCHEMA,
            "create_climatisation_timer",
            True,
        ),
        (
            SERVICE_SET_CLIMATISATION_TIMER_ENABLED,
            SERVICE_SET_CLIMATISATION_TIMER_ENABLED_SCHEMA,
            "set_climatisation_timer_enabled",
            True,
        ),
        (
            SERVICE_DELETE_CLIMATISATION_TIMER,
            SERVICE_DELETE_CLIMATISATION_TIMER_SCHEMA,
            "delete_climatisation_timer",
            True,
        ),
        (
            SERVICE_TEST_CLIMATISATION_WRITE,
            SERVICE_TEST_CLIMATISATION_WRITE_SCHEMA,
            "test_climatisation_write",
            True,
        ),
    )
    for name, schema, method, pass_call in vehicle_services:
        hass.services.async_register(
            DOMAIN,
            name,
            _vehicle_service(hass, method, pass_call=pass_call),
            schema=schema,
        )


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the integration: services are registered once, not per entry."""
    _async_register_services(hass)
    await async_register_card(hass)
    return True


def _async_cleanup_orphaned_devices(
    hass: HomeAssistant, config_entry: ConfigEntry
) -> None:
    """Remove devices that no longer have a matching vehicle in the account.

    This ensures that after migration or vehicle removal, no orphaned device
    entries remain in the device registry.
    """
    runtime_data: AudiRuntimeData | None = getattr(config_entry, "runtime_data", None)
    if runtime_data is None:
        return

    active_vins: set[str] = set()
    for vehicle_data in runtime_data.account.config_vehicles:
        if vehicle_data.vehicle and vehicle_data.vehicle.vin:
            active_vins.add(vehicle_data.vehicle.vin.lower())

    # No vehicle known means no poll has succeeded (startup refresh disabled, or
    # the account answered with an empty list once). That says nothing about
    # which devices are gone, and removing them would also drop the user's
    # renames, areas and disabled entities.
    if not active_vins:
        _LOGGER.debug("Skipping device cleanup: no vehicle is known yet")
        return

    device_registry = dr.async_get(hass)
    devices = dr.async_entries_for_config_entry(device_registry, config_entry.entry_id)

    for device_entry in devices:
        device_vin: str | None = None
        for domain, identifier in device_entry.identifiers:
            if domain == DOMAIN:
                device_vin = identifier
                break

        if device_vin is not None and device_vin.lower() not in active_vins:
            _LOGGER.info(
                "Removing orphaned device %s (VIN no longer active)",
                device_entry.id,
            )
            device_registry.async_remove_device(device_entry.id)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up Audi Connect from a config entry."""
    # Accept whichever credential the entry actually holds, regardless of region:
    # device-code was offered everywhere in 2.2.1b1/b2, so a non-European entry can
    # hold a perfectly good refresh token. Only prompt when neither is present.
    has_refresh_token = bool(config_entry.data.get(CONF_REFRESH_TOKEN))
    has_credentials = bool(
        config_entry.data.get(CONF_USERNAME) and config_entry.data.get(CONF_PASSWORD)
    )
    if not has_refresh_token and not has_credentials:
        raise ConfigEntryAuthFailed(
            "Audi Connect needs to sign in again"
            if uses_auth0(config_entry.data.get(CONF_REGION))
            else "Audi Connect needs your myAudi username and password to sign in"
        )

    account = AudiAccount(hass, config_entry)
    coordinator = AudiDataUpdateCoordinator.from_entry(hass, account, config_entry)

    async def _request_refresh(*_: Any) -> None:
        await coordinator.async_request_refresh()

    account.set_refresh_callback(_request_refresh)
    config_entry.runtime_data = AudiRuntimeData(
        account=account,
        coordinator=coordinator,
        options_snapshot=dict(config_entry.options),
        data_snapshot=_reloadable_data(config_entry),
    )

    config_entry.async_on_unload(
        config_entry.add_update_listener(_async_update_listener)
    )

    if config_entry.options.get(CONF_SCAN_INITIAL, True):
        await coordinator.async_config_entry_first_refresh()

    _async_cleanup_orphaned_devices(hass, config_entry)
    # Entity ids are built from en.json; read it off the event loop once so the
    # cached lookup is already warm when the platforms add their entities.
    await hass.async_add_executor_job(_english_entity_names)
    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload Audi Connect entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        config_entry, PLATFORMS
    )
    return unload_ok


async def async_remove_config_entry_device(
    hass: HomeAssistant, config_entry: ConfigEntry, device_entry: DeviceEntry
) -> bool:
    """Allow removing a device only if its vehicle is no longer in the account."""
    runtime_data: AudiRuntimeData | None = getattr(config_entry, "runtime_data", None)
    if runtime_data is None:
        return True
    active_vins = {
        v.vehicle.vin.lower()
        for v in runtime_data.account.config_vehicles
        if v.vehicle and v.vehicle.vin
    }
    return not any(
        domain == DOMAIN and identifier.lower() in active_vins
        for domain, identifier in device_entry.identifiers
    )


__all__ = [
    "AudiRuntimeData",
    "async_migrate_entry",
    "async_setup_entry",
    "async_unload_entry",
]
