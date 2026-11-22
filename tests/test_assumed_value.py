"""A written value stays on screen until the car reports something else."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.exceptions import HomeAssistantError

from custom_components.ha_audi_connect import audi_entity
from custom_components.ha_audi_connect.select import AudiClimatisationModeSelect

VIN = "WAUZZZ00000000001"


def make(mode="economy", ok=True):
    vehicle = SimpleNamespace(vin=VIN, climatisation_mode=mode)
    coordinator = MagicMock()
    coordinator.account.connection.set_climatisation_setting = AsyncMock(
        return_value=ok
    )
    coordinator.async_request_refresh = AsyncMock()
    select = AudiClimatisationModeSelect(coordinator, vehicle)
    select.written = 0

    def _write():
        select.written += 1

    select.async_write_ha_state = _write
    return select, vehicle


def pick(select, option):
    asyncio.run(select.async_select_option(option))


def test_the_written_value_is_shown_while_the_car_still_reports_the_old_one():
    select, _ = make("economy")
    pick(select, "comfort")
    assert select.current_option == "comfort"
    assert select.written == 1


def test_an_unchanged_report_keeps_the_guess():
    """The refresh after the write usually re-reads the old value."""
    select, vehicle = make("economy")
    pick(select, "comfort")
    vehicle.climatisation_mode = "economy"
    select._handle_coordinator_update()
    assert select.current_option == "comfort"


def test_a_different_report_ends_the_guess_even_if_it_is_not_what_was_asked():
    """Another client (the myAudi app) may have changed it again."""
    select, vehicle = make("economy")
    pick(select, "comfort")
    vehicle.climatisation_mode = "auto"
    select._handle_coordinator_update()
    assert select.current_option == "auto"


def test_the_guess_expires(monkeypatch):
    select, _ = make("economy")
    pick(select, "comfort")
    later = select._assumed_at + audi_entity.ASSUMED_VALUE_TTL + 1
    monkeypatch.setattr(audi_entity.time, "monotonic", lambda: later)
    assert select.current_option == "economy"


def test_a_refused_write_assumes_nothing():
    select, _ = make("economy", ok=False)
    with pytest.raises(HomeAssistantError):
        pick(select, "comfort")
    assert select.current_option == "economy"
    assert select.written == 0
