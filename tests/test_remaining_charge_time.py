"""Nothing left to charge is 0 minutes; charging with no estimate is unknown."""

from tests.test_a6_etron import vehicle_with


def car(state):
    vehicle = vehicle_with({"carType": "electric", **state})
    vehicle._vehicle.fields = {}
    return vehicle


def test_not_charging_and_nothing_reported_is_zero():
    assert car({"chargingState": "notReadyForCharging"}).remaining_charging_time == 0


def test_charging_with_no_estimate_is_unknown_not_zero():
    assert car({"chargingState": "charging"}).remaining_charging_time is None


def test_a_reported_time_is_used_as_it_is():
    assert (
        car(
            {"chargingState": "charging", "remainingChargingTime": 95}
        ).remaining_charging_time
        == 95
    )
