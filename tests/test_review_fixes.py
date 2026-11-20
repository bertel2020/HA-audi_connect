"""Regressions for the first code review: log redaction and timer offset."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone, UTC

import pytest

from custom_components.audiconnect.audi_api import _redact_secrets
from custom_components.audiconnect.audi_services import _utc_offset_of


def test_spin_and_tokens_are_redacted_in_dicts():
    out = _redact_secrets(
        {
            "spin": "1234",
            "a": {"securityPinHash": "x", "keep": 1},
            "l": [{"token": "t"}],
        }
    )
    assert out == {
        "spin": "<redacted>",
        "a": {"securityPinHash": "<redacted>", "keep": 1},
        "l": [{"token": "<redacted>"}],
    }


def test_spin_is_redacted_in_json_and_form_strings():
    assert "1234" not in str(_redact_secrets('{"spin": "1234", "x": 2}'))
    assert "1234" not in str(_redact_secrets("spin=1234&x=2"))


def test_utc_offset_accepts_datetime_and_string():
    plus1 = timezone(timedelta(hours=1))
    assert _utc_offset_of(datetime(2026, 11, 16, 20, 52, tzinfo=plus1)) == timedelta(
        hours=1
    )
    assert _utc_offset_of("2026-11-16T20:52:55+01:00") == timedelta(hours=1)
    assert _utc_offset_of(None) is None
    assert _utc_offset_of("2026-11-16T20:52:55") is None


def test_service_end_accepts_a_bare_date():
    from custom_components.audiconnect.audi_models import _service_end

    assert _service_end("2033-09-30") == datetime(2033, 9, 30, tzinfo=UTC)


# --- masking, zero values, S-PIN ---------------------------------------------------


def test_mask_vins_keeps_only_the_last_four_characters():
    from custom_components.audiconnect.util import mask_vins

    out = mask_vins("Unable to lock WAUZZZF12345678AB now, wauzzzf12345678ab too")
    assert "WAUZZZF1234" not in out and "wauzzzf1234" not in out
    assert out.count("78AB") + out.count("78ab") == 2
    assert mask_vins("no vin here") == "no vin here"


@pytest.mark.parametrize(
    ("key", "attr"),
    [
        ("secondaryEngineRangePercent", "secondary_engine_range_percent"),
        ("primaryEngineRange", "primary_engine_range"),
        ("hybridRange", "hybrid_range"),
        ("outdoorTemperature", "outdoor_temperature"),
    ],
)
def test_a_reading_of_zero_is_a_value_not_a_missing_one(key, attr):
    from tests.test_a6_etron import vehicle_with

    assert getattr(vehicle_with({key: 0}), attr) == 0


def test_an_empty_spin_does_not_count_as_configured():
    from types import SimpleNamespace

    from custom_components.audiconnect.lock import _spin_configured

    def car(spin):
        return SimpleNamespace(_audi_service=SimpleNamespace(_spin=spin))

    assert _spin_configured(car("1234")) is True
    assert _spin_configured(car("")) is False
    assert _spin_configured(car(None)) is False


# --- device cleanup ----------------------------------------------------------------


def test_cleanup_does_nothing_while_no_vehicle_is_known():
    """With no vehicle list every device would look orphaned. hass is None on
    purpose: the registry must not even be looked at."""
    from types import SimpleNamespace

    from custom_components.audiconnect import _async_cleanup_orphaned_devices

    entry = SimpleNamespace(
        runtime_data=SimpleNamespace(account=SimpleNamespace(config_vehicles=[]))
    )
    assert _async_cleanup_orphaned_devices(None, entry) is None


# --- service schema ----------------------------------------------------------------


def test_climate_service_keeps_half_degrees_and_bounds_the_range():
    import voluptuous as vol

    from custom_components.audiconnect.audi_account import (
        SERVICE_START_CLIMATE_CONTROL_SCHEMA as schema,
    )

    assert schema({"device_id": "d", "temp_c": 21.5})["temp_c"] == 21.5
    for bad in ({"temp_c": 99}, {"temp_c": 5}, {"temp_f": 120}):
        with pytest.raises(vol.Invalid):
            schema({"device_id": "d", **bad})


def test_fahrenheit_is_rounded_to_half_degrees_not_truncated():
    from custom_components.audiconnect.audi_payloads import (
        build_climatisation_start_body,
    )

    body = build_climatisation_start_body({}, temp_f=71)
    assert body["targetTemperature"] == 21.5


# --- login session lock ------------------------------------------------------------


def _account():
    from custom_components.audiconnect.audi_connect_account import AudiConnectAccount

    return AudiConnectAccount(
        session=None, country="DE", spin=None, api_level=1, refresh_token="token"
    )


def test_concurrent_logins_sign_in_once():
    import asyncio

    account = _account()
    calls = []

    async def _try_login(_log_error):
        calls.append(1)
        await asyncio.sleep(0)
        return True

    account.try_login = _try_login

    async def both():
        await asyncio.gather(account.login(), account.login())

    asyncio.run(both())
    assert len(calls) == 1


def test_a_command_renews_an_expiring_token_first(monkeypatch):
    import asyncio
    from types import SimpleNamespace

    account = _account()
    account._loggedin = True
    account._logintime = 0
    seen = []

    async def _refresh(elapsed):
        seen.append(elapsed)
        return True

    account._audi_service = SimpleNamespace(refresh_token_if_necessary=_refresh)
    synced = []
    account._sync_refresh_token = lambda: synced.append(1)

    async def _call():
        return None

    assert asyncio.run(account._run_command("VIN", "do a thing", _call)) is True
    assert seen and synced == [1]


# --- reauth ------------------------------------------------------------------------


def test_password_reauth_drops_the_refresh_token_that_just_failed():
    import asyncio
    from types import SimpleNamespace

    from custom_components.audiconnect.config_flow import AudiConfigFlow
    from custom_components.audiconnect.const import CONF_REFRESH_TOKEN

    flow = AudiConfigFlow()
    flow._reauth_entry = SimpleNamespace(
        entry_id="e",
        unique_id="user@example.com",
        data={CONF_REFRESH_TOKEN: "old", "region": "US"},
    )
    flow.hass = SimpleNamespace(
        config_entries=SimpleNamespace(async_schedule_reload=lambda _id: None)
    )
    captured = {}

    def _update_and_abort(_entry, data):
        captured.update(data)
        return {"type": "abort"}

    flow.async_update_and_abort = _update_and_abort
    asyncio.run(flow._finish_password_login("user@example.com", "pw"))
    assert CONF_REFRESH_TOKEN not in captured
    assert captured["region"] == "US" and captured["password"] == "pw"


# --- translations and services -----------------------------------------------------


def test_every_service_in_services_yaml_has_texts():
    import json
    from pathlib import Path

    import yaml

    root = Path(__file__).resolve().parents[1] / "custom_components/audiconnect"
    services = yaml.safe_load((root / "services.yaml").read_text())
    for lang in ("strings.json", "translations/en.json", "translations/de.json"):
        texts = json.loads((root / lang).read_text())["services"]
        missing = sorted(set(services) - set(texts))
        assert not missing, f"{lang} lacks service texts for {missing}"
        for name, spec in services.items():
            for field in (spec or {}).get("fields", {}):
                assert field in texts[name].get("fields", {}), (lang, name, field)


# --- reauth must stay on the same account -------------------------------------------


def _reauth_flow(unique_id):
    from types import SimpleNamespace

    from custom_components.audiconnect.config_flow import AudiConfigFlow

    flow = AudiConfigFlow()
    flow._reauth_entry = SimpleNamespace(
        entry_id="e", unique_id=unique_id, data={"region": "DE"}
    )
    flow.hass = SimpleNamespace(
        config_entries=SimpleNamespace(async_schedule_reload=lambda _id: None)
    )
    flow.async_abort = lambda reason: {"type": "abort", "reason": reason}
    flow.async_update_and_abort = lambda _entry, data: {"type": "abort", "reason": "ok"}
    return flow


def test_password_reauth_with_another_account_is_refused():
    import asyncio

    flow = _reauth_flow("owner@example.com")
    result = asyncio.run(flow._finish_password_login("someone@example.com", "pw"))
    assert result["reason"] == "wrong_account"


def test_password_reauth_accepts_the_same_account_in_any_case():
    import asyncio

    flow = _reauth_flow("owner@example.com")
    result = asyncio.run(flow._finish_password_login("Owner@Example.com", "pw"))
    assert result["reason"] == "ok"


def test_password_reauth_does_not_compare_against_an_opaque_subject_id():
    import asyncio

    flow = _reauth_flow("a1b2c3-subject")
    result = asyncio.run(flow._finish_password_login("owner@example.com", "pw"))
    assert result["reason"] == "ok"


def test_token_reauth_with_another_account_is_refused():
    import asyncio
    from types import SimpleNamespace

    flow = _reauth_flow("owner@example.com")
    flow._connection = SimpleNamespace(
        refresh_token="t", account_identifier=lambda: "someone@example.com"
    )
    assert asyncio.run(flow._finish_token_login())["reason"] == "wrong_account"
    flow._connection = SimpleNamespace(
        refresh_token="t", account_identifier=lambda: "OWNER@example.com"
    )
    assert asyncio.run(flow._finish_token_login())["reason"] == "ok"


def test_the_tracker_does_not_put_the_vin_into_state_attributes():
    from types import SimpleNamespace
    from unittest.mock import MagicMock

    from custom_components.audiconnect.device_tracker import AudiDeviceTracker

    vehicle = SimpleNamespace(
        vin="WAUZZZF12345678AB",
        csid="core-1",
        model="Q8",
        title="e-tron",
        model_year=2024,
        model_family="Q8",
        position={"latitude": 1.0, "longitude": 2.0, "timestamp": None},
    )
    tracker = AudiDeviceTracker(MagicMock(), vehicle)
    attrs = tracker.extra_state_attributes
    assert "vin" not in attrs and "csid" not in attrs


def test_parse_datetime_converts_offsets_and_takes_long_fractions():
    from datetime import UTC

    from custom_components.audiconnect.util import parse_datetime

    assert parse_datetime("2026-11-16 20:52:55+01:00") == datetime(
        2026, 11, 16, 19, 52, 55, tzinfo=UTC
    )
    assert parse_datetime("2026-11-16T19:52:55.5058477Z") == datetime(
        2026, 11, 16, 19, 52, 55, 505847, tzinfo=UTC
    )
    assert parse_datetime("nonsense") is None


def test_preheater_duration_without_a_state_report_is_none():
    from tests.test_a6_etron import vehicle_with

    car = vehicle_with({"preheaterState": {}})
    assert car.preheater_duration is None
    assert car.preheater_remaining is None
