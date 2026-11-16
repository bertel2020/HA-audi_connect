"""The charge target limits come from the car's capabilities call."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

from aiohttp import ClientResponseError

from custom_components.audiconnect.audi_connect_account import AudiConnectVehicle
from custom_components.audiconnect.audi_services import AudiService

VIN = "TESTVIN00000000001"

# Trimmed from what the A6 answers to .../capabilities.
ANSWER = {
    "vin": "x",
    "capabilities": {
        "charging": {
            "id": "charging",
            "parameters": [
                {"key": "supportsTargetStateOfCharge", "value": "true"},
                {"key": "targetStateOfChargeMinimumAllowedValue", "value": "50"},
                {"key": "targetStateOfChargeStepSize", "value": "5"},
            ],
        },
        "chargingProfiles": {
            "id": "chargingProfiles",
            "parameters": [
                {"key": "targetStateOfChargeMinimumAllowedValue", "value": ""}
            ],
        },
    },
    "parameters": {},
}


class API:
    def __init__(self, reply):
        self.reply = reply
        self.urls = []

    def use_token(self, token):
        pass

    async def get(self, url):
        self.urls.append(url)
        if isinstance(self.reply, Exception):
            raise self.reply
        return self.reply


def make_vehicle(reply, uses_auth0=True):
    api = API(reply)
    service = AudiService(api, "BE", None, 0)
    service._bearer_token_json = {"access_token": "FAKE"}
    vehicle = object.__new__(AudiConnectVehicle)
    vehicle._vehicle = SimpleNamespace(vin=VIN, state={}, fields={})
    vehicle._audi_service = service
    vehicle._capability_parameters_loaded = not uses_auth0
    return vehicle, api


def run(vehicle):
    asyncio.run(vehicle.update_vehicle_capability_parameters())


def error(status):
    return ClientResponseError(None, (), status=status, message="x")


def test_the_limits_are_read_from_the_charging_capability():
    vehicle, api = make_vehicle(ANSWER)
    run(vehicle)
    assert api.urls[0].endswith(f"/vehicle/v1/vehicles/{VIN}/capabilities")
    assert vehicle._vehicle.state["chargeTargetLimits"] == {"min": 50, "step": 5}
    assert (vehicle.charge_target_min, vehicle.charge_target_step) == (50, 5)


def test_it_is_asked_only_once():
    vehicle, api = make_vehicle(ANSWER)
    run(vehicle)
    run(vehicle)
    assert len(api.urls) == 1


def test_a_failure_is_tried_again_next_poll():
    vehicle, api = make_vehicle(error(502))
    run(vehicle)
    assert "chargeTargetLimits" not in vehicle._vehicle.state
    api.reply = ANSWER
    run(vehicle)
    assert vehicle._vehicle.state["chargeTargetLimits"] == {"min": 50, "step": 5}


def test_a_404_stops_the_asking():
    vehicle, api = make_vehicle(error(404))
    run(vehicle)
    run(vehicle)
    assert len(api.urls) == 1


def test_nothing_is_asked_without_auth0():
    vehicle, api = make_vehicle(ANSWER, uses_auth0=False)
    run(vehicle)
    assert api.urls == []


def test_an_answer_without_limits_leaves_the_default_range():
    vehicle, _ = make_vehicle({"capabilities": {"charging": {"parameters": []}}})
    run(vehicle)
    assert "chargeTargetLimits" not in vehicle._vehicle.state
    assert vehicle.charge_target_min is None
