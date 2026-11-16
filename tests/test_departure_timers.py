"""Timers the A6 reports under departureTimers instead of their own jobs."""

from __future__ import annotations

from custom_components.audiconnect.audi_models import VehicleDataResponse

TS = "2026-11-15T17:36:17+00:00"

# As the A6 sends it.
A6 = {
    "departureTimers": {
        "chargingTimersStatus": {
            "value": {
                "carCapturedTimestamp": TS,
                "timeInCar": "2026-11-15T18:36:17+01:00",
            }
        },
        "climatisationTimersStatus": {
            "value": {
                "carCapturedTimestamp": TS,
                "timeInCar": "2026-11-15T18:36:17+01:00",
                "timers": [],
            }
        },
    }
}


def states(payload):
    return {s["name"]: s["value"] for s in VehicleDataResponse(payload).states}


def test_the_a6_climate_timers_are_read_from_departure_timers():
    s = states(A6)
    assert s["climatisationTimerCount"] == 0
    assert s["climatisationTimerEnabledCount"] == 0
    assert s["climatisationTimers"] == []


def test_a_charging_block_without_a_timer_list_is_not_guessed_at():
    """The A6 leaves the list out. That could mean none or not supported, so no
    count is invented."""
    s = states(A6)
    assert "chargingTimerEnabledCount" not in s


def test_timers_in_departure_timers_are_counted():
    payload = {
        "departureTimers": {
            "climatisationTimersStatus": {
                "value": {
                    "carCapturedTimestamp": TS,
                    "timers": [
                        {
                            "id": 1,
                            "enabled": True,
                            "singleTimer": {
                                "startDateTimeLocal": "2026-11-20T06:30:00"
                            },
                        },
                        {"id": 2, "enabled": False},
                    ],
                }
            },
            "chargingTimersStatus": {
                "value": {
                    "carCapturedTimestamp": TS,
                    "timers": [
                        {
                            "id": 1,
                            "enabled": True,
                            "recurringTimer": {
                                "departureTimeLocal": "07:30",
                                "repetitionDays": ["monday"],
                            },
                        }
                    ],
                }
            },
        }
    }
    s = states(payload)
    assert s["climatisationTimerCount"] == 2
    assert s["climatisationTimerEnabledCount"] == 1
    assert s["nextClimatisationTimerLocal"] == "2026-11-20T06:30:00"
    assert s["chargingTimerEnabledCount"] == 1


def test_the_own_job_wins_over_departure_timers():
    payload = {
        "climatisationTimers": {
            "climatisationTimersStatus": {
                "value": {
                    "carCapturedTimestamp": TS,
                    "timers": [{"id": 1, "enabled": True}],
                }
            }
        },
        **A6,
    }
    assert states(payload)["climatisationTimerCount"] == 1


def test_the_a6_departure_timers_capability_covers_the_timer_sensors():
    """The A6 announces departureTimers, not climatisationTimers, so the sensors
    gated on the latter were never created."""
    from custom_components.audiconnect.sensor import SENSOR_DESCRIPTIONS
    from tests.test_a6_etron import vehicle_with

    vehicle = vehicle_with({"userCapabilities": ["departureTimers", "charging"]})
    assert vehicle.has_capability("climatisationTimers") is True
    assert vehicle.has_capability("chargingTimers") is True
    assert vehicle.has_capability("parkingPosition") is False
    gated = {
        d.key for d in SENSOR_DESCRIPTIONS if d.capability == "climatisationTimers"
    }
    assert gated == {
        "climatisation_timer_enabled_count",
        "next_climatisation_timer_local",
    }


def test_no_capability_list_still_means_unknown():
    from tests.test_a6_etron import vehicle_with

    assert vehicle_with({}).has_capability("climatisationTimers") is None
