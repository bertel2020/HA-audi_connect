"""The system health page sums up every entry without leaking anything about the car."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace

from custom_components.audiconnect.system_health import (
    async_register,
    system_health_info,
)


def _entry(
    *,
    logged_in=True,
    vehicles=1,
    region="EU",
    level=1,
    limit=None,
    update=None,
    error=None,
):
    api = SimpleNamespace(vcf_remaining_calls=limit)
    connection = SimpleNamespace(
        _loggedin=logged_in,
        vehicles=[object()] * vehicles,
        _audi_service=SimpleNamespace(_api=api),
    )
    runtime = SimpleNamespace(
        account=SimpleNamespace(connection=connection),
        coordinator=SimpleNamespace(
            last_update_success_time=update, last_exception=error
        ),
    )
    return SimpleNamespace(
        runtime_data=runtime, data={"region": region, "api_level": level}
    )


def _hass(*entries):
    return SimpleNamespace(
        config_entries=SimpleNamespace(async_entries=lambda domain: list(entries))
    )


def _info(*entries):
    return asyncio.run(system_health_info(_hass(*entries)))


def test_registration_adds_the_info_callback():
    seen = []
    register = SimpleNamespace(async_register_info=seen.append)
    async_register(None, register)
    assert seen == [system_health_info]


def test_no_entries_give_an_empty_page():
    assert _info() == {}


def test_one_healthy_entry_is_summed_up():
    when = datetime(2026, 11, 22, 9, 0, tzinfo=UTC)
    info = _info(_entry(limit=35, update=when))
    assert info == {
        "logged_in": True,
        "vehicles": 1,
        "region": "EU",
        "api_level": "1",
        "api_rate_limit_remaining": 35,
        "last_successful_refresh": when.isoformat(),
    }


def test_several_entries_are_combined():
    early = datetime(2026, 11, 22, 8, 0, tzinfo=UTC)
    late = datetime(2026, 11, 22, 9, 0, tzinfo=UTC)
    info = _info(
        _entry(vehicles=2, region="EU", level=0, limit=50, update=early),
        _entry(vehicles=1, region="US", level=1, limit=20, update=late),
    )
    assert info["vehicles"] == 3
    assert info["region"] == "EU, US" and info["api_level"] == "0, 1"
    assert info["api_rate_limit_remaining"] == 20
    assert info["last_successful_refresh"] == late.isoformat()


def test_an_entry_that_is_not_set_up_means_not_logged_in():
    info = _info(SimpleNamespace(data={}), _entry())
    assert info["logged_in"] is False and info["vehicles"] == 1


def test_a_logged_out_account_means_not_logged_in():
    assert _info(_entry(logged_in=False))["logged_in"] is False


def test_the_last_error_is_only_the_class_never_the_message():
    error = RuntimeError("https://example/vehicles/WAUZZZGH7SA000001 failed")
    info = _info(_entry(error=error))
    assert info["last_update_error"] == "RuntimeError"
    assert "WAUZZZ" not in repr(info)
