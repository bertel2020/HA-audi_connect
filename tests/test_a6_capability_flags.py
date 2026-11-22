"""What the A6 e-tron's own "supports..." answers do to the entities.

The flags below are the car's answers as the diagnostics download showed them
on 2026-11-21. Reading them as true/false is covered in test_supports_flags.py;
this pins what follows from them for this car.
"""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

from custom_components.ha_audi_connect.audi_connect_account import AudiConnectVehicle
from custom_components.ha_audi_connect.audi_services import AudiService
from custom_components.ha_audi_connect.button import _window_heating_capable
from custom_components.ha_audi_connect.switch import (
    SWITCH_DESCRIPTIONS,
    car_says_unsupported,
)

VIN = "TESTVIN00000000001"

A6_CLIMATISATION = {
    "supportsClimatisationAtUnlock": "true",
    "supportsClimatisationMode": "true",
    "supportsOffGridClimatisation": "false",
    "supportsSaveEnergy": "false",
    "supportsTargetTemperatureInSettings": "true",
    "supportsTargetTemperatureInStartClimatisation": "true",
    "supportsWindowHeatingEnabled": "false",
    "supportsZoneFrontLeftEnabled": "true",
    "supportsZoneFrontRightEnabled": "true",
    "supportsZoneRearLeftEnabled": "true",
    "supportsZoneRearRightEnabled": "true",
}

A6_CHARGING_PROFILES = {
    "supportsChargingTimer": "false",
    "supportsCreateProfileWithSettings": "true",
    "supportsMaxChargingCurrent": "true",
    "supportsTargetStateOfCharge": "false",
    "supportsUsePrivateCurrent": "false",
    "supportsVehiclePositionedInProfileID": "true",
}


def _capability(name, flags):
    return {
        "id": name,
        "parameters": [{"key": k, "value": v} for k, v in flags.items()],
    }


class API:
    def use_token(self, token):
        pass

    async def get(self, url):
        return {
            "capabilities": {
                "climatisation": _capability("climatisation", A6_CLIMATISATION),
                "chargingProfiles": _capability(
                    "chargingProfiles", A6_CHARGING_PROFILES
                ),
            }
        }


def a6():
    service = AudiService(API(), "DE", None, 0)
    service._bearer_token_json = {"access_token": "FAKE"}
    vehicle = object.__new__(AudiConnectVehicle)
    vehicle._vehicle = SimpleNamespace(vin=VIN, state={}, fields={})
    vehicle._audi_service = service
    vehicle._capability_parameters_loaded = False
    asyncio.run(vehicle.update_vehicle_capability_parameters())
    return vehicle


def _setting_switches():
    return {d.key: d for d in SWITCH_DESCRIPTIONS if d.supports_key}


def test_the_car_flags_are_kept_for_climatisation_and_charging_profiles():
    state = a6()._vehicle.state
    assert state["climatisationSupports"]["supportsWindowHeatingEnabled"] is False
    assert state["climatisationSupports"]["supportsClimatisationMode"] is True
    assert state["chargingProfilesSupports"]["supportsChargingTimer"] is False
    assert state["chargingProfilesSupports"]["supportsMaxChargingCurrent"] is True


def test_the_a6_has_no_window_heating_switch_but_all_other_setting_switches():
    car = _vehicle_view(a6())
    hidden = {
        key
        for key, description in _setting_switches().items()
        if car_says_unsupported(car, description)
    }
    assert hidden == {"climatisation_window_heating"}


def test_all_four_climate_zones_are_real_on_the_a6():
    car = _vehicle_view(a6())
    zones = [
        d
        for key, d in _setting_switches().items()
        if key.startswith("climatisation_zone_")
    ]
    assert len(zones) == 4
    assert not any(car_says_unsupported(car, d) for d in zones)


def test_the_a6_does_not_get_the_window_heating_buttons():
    car = _vehicle_view(a6(), capabilities={"climatisation"})
    assert _window_heating_capable(car) is False


def test_the_charging_profile_has_no_timer_and_no_target_of_its_own():
    flags = a6()._vehicle.state["chargingProfilesSupports"]
    assert flags["supportsChargingTimer"] is False
    assert flags["supportsTargetStateOfCharge"] is False


def _vehicle_view(vehicle, capabilities=frozenset()):
    """What the entity code reads from the vehicle object."""
    return SimpleNamespace(
        _audi_service=SimpleNamespace(uses_auth0=True),
        has_capability=lambda c: c in capabilities,
        impaired_capabilities=frozenset(),
        climatisation_supports=vehicle.climatisation_supports,
    )
