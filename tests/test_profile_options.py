"""The charging-profile options and navigation target the A6 reports."""

from __future__ import annotations

from custom_components.audiconnect.audi_models import VehicleDataResponse
from custom_components.audiconnect.binary_sensor import BINARY_SENSOR_DESCRIPTIONS
from custom_components.audiconnect.sensor import SENSOR_DESCRIPTIONS
from tests.test_a6_etron import vehicle_with

# As the A6 sends it (position left out).
PAYLOAD = {
    "charging": {
        "batteryStatus": {
            "value": {
                "carCapturedTimestamp": "2026-11-16T14:40:34+00:00",
                "currentSOC_pct": 66,
                "navigationTargetSOC_pct": 0,
            }
        }
    },
    "chargingProfiles": {
        "chargingProfilesStatus": {
            "value": {
                "carCapturedTimestamp": "2026-11-15T17:36:17.5058477Z",
                "vehiclePositionedInProfileID": 1,
                "profiles": [
                    {
                        "id": 1,
                        "name": "Zuhause",
                        "maxChargingCurrent": "max",
                        "minSOC_pct": 25,
                        "options": {
                            "autoUnlockPlugWhenCharged": "invalid",
                            "usePreferredChargingTimes": False,
                        },
                        "preferredChargingTimes": [
                            {
                                "id": 1,
                                "enabled": False,
                                "startTime": "19:05",
                                "endTime": "19:05",
                            }
                        ],
                    }
                ],
            }
        }
    },
}


def states(payload=PAYLOAD):
    return {s["name"]: s["value"] for s in VehicleDataResponse(payload).states}


def test_the_profile_options_are_read():
    s = states()
    assert s["activeChargingProfileMaxCurrent"] == "max"
    assert s["activeChargingProfileUsesPreferredTimes"] is False
    assert "navigationTargetSoc" not in s


def test_the_a6_names_the_preferred_window_start_and_end():
    """The A6 sends startTime/endTime where other cars send ...Local, which left
    the preferred-time sensors empty."""
    s = states()
    assert s["preferredChargingTimeStart"] == "19:05"
    assert s["preferredChargingTimeEnd"] == "19:05"


def test_the_local_field_names_still_win():
    payload = {
        "chargingProfiles": {
            "chargingProfilesStatus": {
                "value": {
                    "carCapturedTimestamp": "2026-11-15T17:36:17Z",
                    "vehiclePositionedInProfileID": 1,
                    "profiles": [
                        {
                            "id": 1,
                            "preferredChargingTimes": [
                                {
                                    "enabled": True,
                                    "startTimeLocal": "22:00",
                                    "startTime": "21:00",
                                    "endTimeLocal": "06:00",
                                    "endTime": "05:00",
                                }
                            ],
                        }
                    ],
                }
            }
        }
    }
    s = states(payload)
    assert (s["preferredChargingTimeStart"], s["preferredChargingTimeEnd"]) == (
        "22:00",
        "06:00",
    )


def test_an_unusable_max_current_is_not_shown():
    payload = {
        **PAYLOAD,
        "chargingProfiles": {
            "chargingProfilesStatus": {
                "value": {
                    "carCapturedTimestamp": "2026-11-15T17:36:17Z",
                    "vehiclePositionedInProfileID": 1,
                    "profiles": [{"id": 1, "maxChargingCurrent": "invalid"}],
                }
            }
        },
    }
    assert "activeChargingProfileMaxCurrent" not in states(payload)


def test_the_entities_exist_and_read_the_values():
    vehicle = vehicle_with(states())
    sensors = {d.key for d in SENSOR_DESCRIPTIONS}
    binary = {d.key for d in BINARY_SENSOR_DESCRIPTIONS}

    assert "active_charging_profile_max_current" in sensors
    assert "navigation_target_soc" not in sensors
    assert "active_charging_profile_uses_preferred_times" in binary
    assert vehicle.active_charging_profile_max_current == "max"
    assert vehicle.active_charging_profile_uses_preferred_times is False
