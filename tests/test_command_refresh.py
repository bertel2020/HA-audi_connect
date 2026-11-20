"""A command that already refreshed the cloud data is not followed by a second poll."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from custom_components.audiconnect.select import AudiClimatisationModeSelect

VIN = "WAUZZZ00000000001"


def make(poll_during_command: bool):
    """A select whose command may trigger the account's own refresh."""
    vehicle = SimpleNamespace(vin=VIN, climatisation_mode="economy")
    coordinator = MagicMock()
    coordinator.last_cloud_poll_attempt = None
    coordinator.async_request_refresh = AsyncMock()

    async def _set(*_args):
        if poll_during_command:
            # What notify -> handle_notification -> refresh callback does.
            coordinator.last_cloud_poll_attempt = datetime.now(UTC) + timedelta(
                seconds=1
            )
        return True

    coordinator.account.connection.set_climatisation_setting = _set
    select = AudiClimatisationModeSelect(coordinator, vehicle)
    select.async_write_ha_state = lambda: None
    return select, coordinator


def test_no_second_refresh_when_the_command_already_polled():
    select, coordinator = make(poll_during_command=True)
    asyncio.run(select.async_select_option("comfort"))
    coordinator.async_request_refresh.assert_not_awaited()


def test_a_command_without_its_own_refresh_still_gets_one():
    select, coordinator = make(poll_during_command=False)
    asyncio.run(select.async_select_option("comfort"))
    coordinator.async_request_refresh.assert_awaited_once()


def test_an_older_poll_does_not_count():
    select, coordinator = make(poll_during_command=False)
    coordinator.last_cloud_poll_attempt = datetime.now(UTC) - timedelta(minutes=5)
    asyncio.run(select.async_select_option("comfort"))
    coordinator.async_request_refresh.assert_awaited_once()
