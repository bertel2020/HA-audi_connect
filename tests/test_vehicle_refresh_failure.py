"""A wake-up the car does not carry out is a warning, not an error.

Audi can accept the request and hand back a request id, and the car then
reports the request as "fail" (asleep, out of coverage). That is the car's
state; the log must not call it an unexpected error.
"""

from __future__ import annotations

import asyncio
import logging

import pytest

from custom_components.audiconnect.audi_connect_account import AudiConnectAccount
from custom_components.audiconnect.audi_services import (
    AudiService,
    AudiVehicleRequestFailed,
)

VIN = "TESTVIN00000000001"
LOGGER = "custom_components.audiconnect.audi_connect_account"


def _account(error: Exception):
    account = AudiConnectAccount(
        session=None, country="DE", spin=None, api_level=1, refresh_token="token"
    )
    account._loggedin = True

    class Service:
        async def refresh_vehicle_data(self, vin):
            raise error

    account._audi_service = Service()
    return account


def test_a_request_the_car_reports_as_failed_is_a_warning(caplog):
    account = _account(
        AudiVehicleRequestFailed("Request x reached unexpected status fail")
    )
    with caplog.at_level(logging.DEBUG, logger=LOGGER):
        assert asyncio.run(account.refresh_vehicle_data(VIN)) is False
    records = [r for r in caplog.records if r.name == LOGGER]
    assert [r.levelno for r in records if "VEHICLE REFRESH" in r.getMessage()] == [
        logging.WARNING
    ]
    assert "did not carry it out" in records[-1].getMessage()
    assert VIN not in caplog.text


def test_any_other_failure_is_still_an_error(caplog):
    account = _account(RuntimeError("something else"))
    with caplog.at_level(logging.DEBUG, logger=LOGGER):
        assert asyncio.run(account.refresh_vehicle_data(VIN)) is False
    assert [r.levelno for r in caplog.records if r.name == LOGGER][-1] == logging.ERROR


@pytest.mark.parametrize("status", ["fail", "failed", "rejected"])
def test_the_pending_request_check_raises_the_specific_error(status, monkeypatch):
    monkeypatch.setattr(
        "custom_components.audiconnect.audi_services.REQUEST_STATUS_SLEEP", 0
    )

    class API:
        async def request(self, *args, **kwargs):
            return {"data": [{"id": "abc", "status": status}]}

    service = AudiService(API(), "DE", None, 0)
    service._bearer_token_json = {"access_token": "FAKE"}
    with pytest.raises(AudiVehicleRequestFailed):
        asyncio.run(service.check_bff_request_succeeded(VIN, "abc"))
    # Still an Exception, so older handlers behave as before.
    assert issubclass(AudiVehicleRequestFailed, Exception)
