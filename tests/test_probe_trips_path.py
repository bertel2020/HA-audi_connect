"""The probe reaches the trip root, which sits beside the vehicle URL."""

from __future__ import annotations

import asyncio

from custom_components.ha_audi_connect.audi_services import AudiService

VIN = "TESTVIN00000000001"


class API:
    def __init__(self):
        self.urls = []

    def use_token(self, token):
        pass

    async def get(self, url):
        self.urls.append(url)
        return {}


def probe(path):
    api = API()
    svc = AudiService(api, "BE", None, 0)
    svc._bearer_token_json = {"access_token": "FAKE"}
    asyncio.run(svc.probe_vehicle_endpoint(VIN, path))
    return api.urls[0]


def test_trips_use_the_trip_root():
    assert probe("trips/shortterm/last").endswith(
        f"/vehicle/v1/trips/{VIN}/shortterm/last"
    )


def test_other_paths_stay_below_the_vehicle():
    assert probe("parkingposition").endswith(
        f"/vehicle/v1/vehicles/{VIN}/parkingposition"
    )


def test_bs_paths_use_the_myaudi_backend_service_root():
    url = probe("bs/climatisation/v1/climatisation/settings")
    assert url == (
        "https://emea.bff.cariad.digital/bs/climatisation/v1/audi/BE/vehicles/"
        f"{VIN}/climatisation/settings"
    )


def test_a_malformed_bs_path_is_refused_before_any_request():
    import pytest

    with pytest.raises(ValueError, match="bs path"):
        probe("bs/climatisation")


def test_bff_paths_reach_any_read_only_route_with_the_vin_filled_in():
    url = probe("bff/vehicle/v1/vehicles/{vin}")
    assert url == f"https://emea.bff.cariad.digital/vehicle/v1/vehicles/{VIN}"
