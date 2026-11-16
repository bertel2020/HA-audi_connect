"""The last trip and the long-term totals, as the A6 reports them."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest
from aiohttp import ClientResponseError

from custom_components.audiconnect.audi_connect_account import AudiConnectVehicle
from custom_components.audiconnect.audi_services import AudiService
from custom_components.audiconnect.sensor import SENSOR_DESCRIPTIONS
from tests.test_a6_etron import vehicle_with

VIN = "TESTVIN00000000001"

SHORT = {
    "id": "7667900235",
    "tripEndTimestamp": "2026-11-15T17:36:15+00:00",
    "tripType": "shortTerm",
    "vehicleType": "electric",
    "mileage_km": 23,
    "startMileage_km": 15663,
    "overallMileage_km": 15687,
    "travelTime": 25,
    "averageElectricConsumption": 24.7,
    "averageSpeed_kmph": 57,
    "totalElectricConsumption_kwh": 5.681,
}
LONG = {**SHORT, "tripType": "longTerm", "mileage_km": 6338, "travelTime": 6553}


class API:
    def __init__(self, responses):
        self.responses = responses
        self.urls = []

    def use_token(self, token):
        pass

    async def get(self, url):
        self.urls.append(url)
        reply = self.responses[url.rsplit("/", 2)[-2]]
        if isinstance(reply, Exception):
            raise reply
        return reply


def make_vehicle(responses):
    api = API(responses)
    service = AudiService(api, "BE", None, 0)
    service._bearer_token_json = {"access_token": "FAKE"}
    vehicle = object.__new__(AudiConnectVehicle)
    vehicle._vehicle = SimpleNamespace(vin=VIN, state={}, fields={})
    vehicle._audi_service = service
    vehicle.support_trip_summary = True
    return vehicle, api


def error(status):
    return ClientResponseError(None, (), status=status, message="x")


def test_trip_urls_are_beside_the_vehicle_and_data_is_unwrapped():
    vehicle, api = make_vehicle(
        {"shortterm": {"data": SHORT}, "longterm": {"data": LONG}}
    )
    asyncio.run(vehicle.update_vehicle_trip_summary())

    assert api.urls[0].endswith(f"/vehicle/v1/trips/{VIN}/shortterm/last")
    assert api.urls[1].endswith(f"/vehicle/v1/trips/{VIN}/longterm/last")
    assert vehicle._vehicle.state["lastTripShortTerm"]["mileage_km"] == 23
    assert vehicle._vehicle.state["lastTripLongTerm"]["travelTime"] == 6553


def test_only_the_figures_are_kept():
    vehicle, _ = make_vehicle(
        {"shortterm": {"data": SHORT}, "longterm": {"data": LONG}}
    )
    asyncio.run(vehicle.update_vehicle_trip_summary())
    kept = vehicle._vehicle.state["lastTripShortTerm"]
    assert "id" not in kept and "overallMileage_km" not in kept


def test_a_transient_error_keeps_the_last_values():
    vehicle, _ = make_vehicle({"shortterm": error(502), "longterm": {"data": LONG}})
    vehicle._vehicle.state["lastTripShortTerm"] = {"mileage_km": 5}
    asyncio.run(vehicle.update_vehicle_trip_summary())
    assert vehicle._vehicle.state["lastTripShortTerm"] == {"mileage_km": 5}
    assert vehicle._vehicle.state["lastTripLongTerm"]["mileage_km"] == 6338


def test_a_404_means_the_car_has_no_such_trips():
    vehicle, _ = make_vehicle({"shortterm": error(404), "longterm": {"data": LONG}})
    vehicle._vehicle.state["lastTripShortTerm"] = {"mileage_km": 5}
    asyncio.run(vehicle.update_vehicle_trip_summary())
    assert "lastTripShortTerm" not in vehicle._vehicle.state


def test_nothing_is_asked_without_auth0():
    vehicle, api = make_vehicle({})
    vehicle.support_trip_summary = False
    asyncio.run(vehicle.update_vehicle_trip_summary())
    assert api.urls == []


def test_unknown_trip_kind_is_refused():
    service = AudiService(API({}), "BE", None, 0)
    with pytest.raises(ValueError):
        asyncio.run(service.get_last_trip(VIN, "../vehicles"))


def _sensors():
    state = {"lastTripShortTerm": SHORT, "lastTripLongTerm": LONG}
    vehicle = vehicle_with(state)
    return vehicle, {d.key: d for d in SENSOR_DESCRIPTIONS}


def test_the_sensors_show_the_cars_figures():
    vehicle, by_key = _sensors()
    read = lambda key: by_key[key].value_fn(vehicle)  # noqa: E731

    assert read("last_trip_distance") == 23
    assert read("last_trip_duration") == 25
    assert read("last_trip_consumption") == 24.7
    assert read("last_trip_energy") == 5.681
    assert read("last_trip_speed") == 57
    assert read("trip_totals_distance") == 6338
    assert read("trip_totals_duration") == 6553


def test_a_car_without_trips_gets_no_values_and_no_support():
    vehicle = vehicle_with({})
    by_key = {d.key: d for d in SENSOR_DESCRIPTIONS}
    assert vehicle.last_trip_supported is False
    assert by_key["last_trip_distance"].value_fn(vehicle) is None


def test_the_long_term_totals_are_on_by_default_like_the_last_trip():
    by_key = {d.key: d for d in SENSOR_DESCRIPTIONS}
    assert by_key["trip_totals_distance"].entity_registry_enabled_default is True
    assert by_key["last_trip_distance"].entity_registry_enabled_default is True


def test_long_term_totals_are_total_increasing_and_last_trip_is_not():
    from homeassistant.components.sensor import SensorStateClass

    from custom_components.audiconnect.sensor import SENSOR_DESCRIPTIONS

    by_key = {d.key: d for d in SENSOR_DESCRIPTIONS}
    for suffix in ("distance", "energy"):
        assert (
            by_key[f"trip_totals_{suffix}"].state_class
            == SensorStateClass.TOTAL_INCREASING
        )
    assert by_key["last_trip_distance"].state_class == SensorStateClass.MEASUREMENT
    assert by_key["last_trip_energy"].state_class is None
    assert by_key["trip_totals_speed"].state_class == SensorStateClass.MEASUREMENT
