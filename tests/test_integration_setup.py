"""Migration, service resolution, reload, unload and device removal of the integration."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from homeassistant.exceptions import ServiceValidationError

from custom_components import audiconnect as integration
from custom_components.audiconnect.const import (
    CONF_API_LEVEL,
    CONF_PASSWORD,
    CONF_REFRESH_TOKEN,
    CONF_REGION,
    CONF_USERNAME,
    DOMAIN,
    PLATFORMS,
)


def run(coro):
    return asyncio.run(coro)


def _vehicle(vin):
    return SimpleNamespace(vehicle=SimpleNamespace(vin=vin))


def _runtime(*vins, coordinator=None, options=None, data=None):
    return SimpleNamespace(
        account=SimpleNamespace(config_vehicles=[_vehicle(v) for v in vins]),
        coordinator=coordinator or SimpleNamespace(),
        options_snapshot=options or {},
        data_snapshot=data or {},
    )


def _hass(*entries):
    return SimpleNamespace(
        config_entries=SimpleNamespace(
            async_entries=lambda domain: list(entries),
            async_update_entry=_update_entry,
            async_unload_platforms=AsyncMock(return_value=True),
            async_reload=AsyncMock(),
        )
    )


def _update_entry(entry, **changes):
    for key, value in changes.items():
        setattr(entry, key, value)


# ---- migration -------------------------------------------------------------------------


@pytest.fixture
def registries(monkeypatch):
    removed = []
    devices = [SimpleNamespace(id="empty"), SimpleNamespace(id="used")]
    device_registry = SimpleNamespace(async_remove_device=removed.append)
    monkeypatch.setattr(integration.dr, "async_get", lambda hass: device_registry)
    monkeypatch.setattr(integration.er, "async_get", lambda hass: object())
    monkeypatch.setattr(
        integration.dr, "async_entries_for_config_entry", lambda reg, entry_id: devices
    )
    monkeypatch.setattr(
        integration.er,
        "async_entries_for_device",
        lambda reg, device_id, include_disabled_entities: (
            [object()] if device_id == "used" else []
        ),
    )
    return removed


def test_migration_from_v1_moves_the_api_level_and_drops_old_options(registries):
    entry = SimpleNamespace(
        version=1,
        entry_id="e1",
        data={CONF_REGION: "US", CONF_USERNAME: "u", CONF_PASSWORD: "p"},
        options={CONF_API_LEVEL: "1", "scan_active": True, "scan_interval": 30},
    )
    assert run(integration.async_migrate_entry(_hass(entry), entry)) is True
    assert entry.version == 3
    assert entry.data[CONF_API_LEVEL] == 1
    assert entry.options == {"scan_interval": 30}
    assert registries == ["empty"]


def test_migration_gives_a_missing_api_level_the_default(registries):
    entry = SimpleNamespace(
        version=1, entry_id="e1", data={CONF_REGION: "US"}, options={}
    )
    run(integration.async_migrate_entry(_hass(entry), entry))
    assert entry.data[CONF_API_LEVEL] == integration.DEFAULT_API_LEVEL


def test_migration_to_v3_drops_credentials_where_login_is_interactive():
    base = {CONF_USERNAME: "u", CONF_PASSWORD: "p", CONF_REGION: "DE"}
    entry = SimpleNamespace(version=2, entry_id="e", data=dict(base), options={})
    run(integration.async_migrate_entry(_hass(entry), entry))
    assert entry.version == 3
    assert CONF_USERNAME not in entry.data and CONF_PASSWORD not in entry.data


def test_migration_to_v3_keeps_credentials_with_a_refresh_token_or_in_other_regions():
    for data in (
        {
            CONF_USERNAME: "u",
            CONF_PASSWORD: "p",
            CONF_REGION: "DE",
            CONF_REFRESH_TOKEN: "t",
        },
        {CONF_USERNAME: "u", CONF_PASSWORD: "p", CONF_REGION: "US"},
    ):
        entry = SimpleNamespace(version=2, entry_id="e", data=dict(data), options={})
        run(integration.async_migrate_entry(_hass(entry), entry))
        assert entry.data[CONF_USERNAME] == "u" and entry.data[CONF_PASSWORD] == "p"


# ---- finding the car for a service call ------------------------------------------------


def _device_registry(monkeypatch, identifiers):
    device = SimpleNamespace(identifiers=identifiers)
    registry = SimpleNamespace(
        async_get=lambda device_id: device if device_id == "dev" else None
    )
    monkeypatch.setattr(integration.dr, "async_get", lambda hass: registry)


def test_a_device_resolves_to_the_vin_of_this_integration(monkeypatch):
    _device_registry(monkeypatch, {("other", "x"), (DOMAIN, "WAU1")})
    assert integration._resolve_device_to_vin(None, "dev") == "WAU1"
    assert integration._resolve_device_to_vin(None, "missing") is None


def test_a_device_of_another_integration_has_no_vin(monkeypatch):
    _device_registry(monkeypatch, {("other", "x")})
    assert integration._resolve_device_to_vin(None, "dev") is None


def test_the_account_is_found_by_vin_ignoring_case():
    entry = SimpleNamespace(runtime_data=_runtime("WAUZZZ1"))
    hass = _hass(SimpleNamespace(runtime_data=None), entry)
    assert (
        integration._get_account_for_vin(hass, "wauzzz1") is entry.runtime_data.account
    )
    assert integration._get_account_for_vin(hass, "OTHER") is None


def test_a_service_call_for_an_unknown_device_is_a_validation_error(monkeypatch):
    _device_registry(monkeypatch, {(DOMAIN, "WAU1")})
    call = SimpleNamespace(data={"device_id": "nope"})
    with pytest.raises(ServiceValidationError) as err:
        integration._resolve_service_call(_hass(), call)
    assert err.value.translation_key == "unknown_device"
    assert err.value.translation_placeholders == {"device_id": "nope"}


def test_a_service_call_for_an_account_that_is_not_loaded_says_so(monkeypatch):
    _device_registry(monkeypatch, {(DOMAIN, "WAU1")})
    call = SimpleNamespace(data={"device_id": "dev"})
    with pytest.raises(ServiceValidationError) as err:
        integration._resolve_service_call(_hass(), call)
    assert err.value.translation_key == "account_not_loaded"


def test_a_vehicle_service_calls_the_account_with_the_vin(monkeypatch):
    _device_registry(monkeypatch, {(DOMAIN, "WAU1")})
    entry = SimpleNamespace(runtime_data=_runtime("WAU1"))
    account = entry.runtime_data.account
    account.lock = AsyncMock()
    account.honk = AsyncMock()
    hass = _hass(entry)
    call = SimpleNamespace(data={"device_id": "dev"})

    run(integration._vehicle_service(hass, "lock")(call))
    account.lock.assert_awaited_once_with("WAU1", call)
    run(integration._vehicle_service(hass, "honk", pass_call=False)(call))
    account.honk.assert_awaited_once_with("WAU1")


def test_the_cloud_refresh_service_asks_every_loaded_coordinator():
    first = SimpleNamespace(async_request_refresh=AsyncMock())
    second = SimpleNamespace(async_request_refresh=AsyncMock())
    hass = _hass(
        SimpleNamespace(runtime_data=_runtime(coordinator=first)),
        SimpleNamespace(runtime_data=None),
        SimpleNamespace(runtime_data=_runtime(coordinator=second)),
    )
    assert integration._get_all_coordinators(hass) == [first, second]


# ---- reload, unload, device removal ----------------------------------------------------


def test_a_rotated_refresh_token_does_not_count_as_a_change():
    entry = SimpleNamespace(data={CONF_REGION: "DE", CONF_REFRESH_TOKEN: "new"})
    assert integration._reloadable_data(entry) == {CONF_REGION: "DE"}


def test_only_a_rotated_token_does_not_reload():
    entry = SimpleNamespace(
        data={CONF_REGION: "DE", CONF_REFRESH_TOKEN: "new"},
        options={"scan_interval": 15},
        entry_id="e",
        runtime_data=_runtime(options={"scan_interval": 15}, data={CONF_REGION: "DE"}),
    )
    hass = _hass(entry)
    run(integration._async_update_listener(hass, entry))
    hass.config_entries.async_reload.assert_not_awaited()


def test_a_changed_option_reloads_the_entry():
    entry = SimpleNamespace(
        data={CONF_REGION: "DE"},
        options={"scan_interval": 30},
        entry_id="e",
        runtime_data=_runtime(options={"scan_interval": 15}, data={CONF_REGION: "DE"}),
    )
    hass = _hass(entry)
    run(integration._async_update_listener(hass, entry))
    hass.config_entries.async_reload.assert_awaited_once_with("e")


def test_an_entry_without_runtime_data_reloads():
    entry = SimpleNamespace(data={}, options={}, entry_id="e", runtime_data=None)
    hass = _hass(entry)
    run(integration._async_update_listener(hass, entry))
    hass.config_entries.async_reload.assert_awaited_once_with("e")


def test_unloading_unloads_every_platform():
    hass = _hass()
    assert run(integration.async_unload_entry(hass, SimpleNamespace())) is True
    hass.config_entries.async_unload_platforms.assert_awaited_once()
    assert hass.config_entries.async_unload_platforms.await_args.args[1] == PLATFORMS


def _device(vin):
    return SimpleNamespace(identifiers={(DOMAIN, vin)})


def test_a_device_whose_car_is_still_in_the_account_cannot_be_removed():
    entry = SimpleNamespace(runtime_data=_runtime("WAU1"))
    assert (
        run(integration.async_remove_config_entry_device(None, entry, _device("wau1")))
        is False
    )


def test_a_device_whose_car_is_gone_can_be_removed():
    entry = SimpleNamespace(runtime_data=_runtime("WAU1"))
    assert (
        run(integration.async_remove_config_entry_device(None, entry, _device("WAU2")))
        is True
    )


def test_a_device_of_an_entry_that_is_not_set_up_can_be_removed():
    entry = SimpleNamespace(runtime_data=None)
    assert (
        run(integration.async_remove_config_entry_device(None, entry, _device("WAU1")))
        is True
    )


# ---- services, the probe and the clean-up of old devices -------------------------------


def _registering_hass():
    registered = {}

    def register(domain, name, handler, schema=None, **kwargs):
        registered[name] = (handler, schema, kwargs)

    hass = _hass()
    hass.services = SimpleNamespace(async_register=register)
    return hass, registered


def test_every_service_is_registered_once_with_its_handler(monkeypatch):
    hass, registered = _registering_hass()
    integration._async_register_services(hass)
    for name in (
        "refresh_cloud_data",
        "refresh_vehicle_data",
        "probe_api",
        "start_engine",
        "set_charge_mode",
        "create_climatisation_timer",
    ):
        assert name in registered, name
        assert callable(registered[name][0])
    assert len(registered) == len(set(registered))


def test_setup_registers_the_services_and_the_card(monkeypatch):
    hass, registered = _registering_hass()
    card = AsyncMock()
    monkeypatch.setattr(integration, "async_register_card", card)
    assert run(integration.async_setup(hass, {})) is True
    card.assert_awaited_once_with(hass)
    assert "refresh_cloud_data" in registered


def _probe(monkeypatch, **data):
    _device_registry(monkeypatch, {(DOMAIN, "WAU1")})
    account = SimpleNamespace(
        connection=SimpleNamespace(
            probe=AsyncMock(return_value={"vin": "WAU1", "value": 1}),
            probe_graphql=AsyncMock(return_value={"value": 2}),
        )
    )
    entry = SimpleNamespace(
        runtime_data=SimpleNamespace(account=account, config_vehicles=[])
    )
    entry.runtime_data.account.config_vehicles = [_vehicle("WAU1")]
    hass, registered = _registering_hass()
    hass.config_entries.async_entries = lambda domain: [entry]
    integration._async_register_services(hass)
    call = SimpleNamespace(data={"device_id": "dev", **data})
    return account, registered["probe_api"][0], hass, call


def test_the_probe_asks_for_the_base_jobs_and_hides_the_vin(monkeypatch):
    account, handler, hass, call = _probe(monkeypatch)
    result = run(handler(call))
    query = account.connection.probe.await_args.args[1]
    assert query.startswith("selectivestatus?jobs=")
    assert result["query"] == query
    assert "WAU1" not in repr(result)


def test_the_probe_refuses_a_path_that_could_leave_the_vehicle(monkeypatch):
    for path in ("../other", "a b", "vehicles/<x>"):
        account, handler, hass, call = _probe(monkeypatch, path=path)
        with pytest.raises(ServiceValidationError) as err:
            run(handler(call))
        assert err.value.translation_key == "probe_path_invalid"
        account.connection.probe.assert_not_awaited()


def test_the_probe_passes_a_clean_path_and_a_graphql_preset(monkeypatch):
    account, handler, hass, call = _probe(monkeypatch, path="parkingposition")
    assert run(handler(call))["query"] == "parkingposition"
    account, handler, hass, call = _probe(monkeypatch, graphql="vehicles")
    assert run(handler(call))["query"] == "graphql:vehicles"
    account.connection.probe_graphql.assert_awaited_once()


def test_cleanup_removes_only_devices_of_cars_that_are_gone(monkeypatch):
    removed = []
    registry = SimpleNamespace(async_remove_device=removed.append)
    devices = [
        SimpleNamespace(id="keep", identifiers={(DOMAIN, "WAU1")}),
        SimpleNamespace(id="gone", identifiers={(DOMAIN, "WAU2")}),
        SimpleNamespace(id="foreign", identifiers={("other", "x")}),
    ]
    monkeypatch.setattr(integration.dr, "async_get", lambda hass: registry)
    monkeypatch.setattr(
        integration.dr, "async_entries_for_config_entry", lambda reg, entry_id: devices
    )
    entry = SimpleNamespace(entry_id="e", runtime_data=_runtime("WAU1"))
    integration._async_cleanup_orphaned_devices(None, entry)
    assert removed == ["gone"]


def test_cleanup_does_nothing_while_no_car_is_known(monkeypatch):
    monkeypatch.setattr(
        integration.dr,
        "async_get",
        lambda hass: pytest.fail("registry must not be read"),
    )
    integration._async_cleanup_orphaned_devices(
        None, SimpleNamespace(entry_id="e", runtime_data=_runtime())
    )
    integration._async_cleanup_orphaned_devices(
        None, SimpleNamespace(entry_id="e", runtime_data=None)
    )
