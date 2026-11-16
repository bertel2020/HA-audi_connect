"""The charge target slider follows the limits the car reports."""

from __future__ import annotations

import copy
from types import SimpleNamespace

import pytest

from custom_components.audiconnect.audi_models import (
    VehicleDataResponse,
    _charge_target_limits,
)
from custom_components.audiconnect.number import AudiNumber, NUMBER_DESCRIPTIONS

from tests.fixture_a6_etron import CAPABILITIES
from tests.test_a6_etron import vehicle_with


def _parsed(parameters):
    data = copy.deepcopy(CAPABILITIES)
    entry = next(
        e
        for e in data["userCapabilities"]["capabilitiesStatus"]["value"]
        if e["id"] == "charging"
    )
    entry["parameters"] = parameters
    return {s["name"]: s["value"] for s in VehicleDataResponse(data).states}


def test_the_a6_limits_are_read_from_the_charging_capability():
    states = _parsed(
        copy.deepcopy(
            next(
                e
                for e in CAPABILITIES["userCapabilities"]["capabilitiesStatus"]["value"]
                if e["id"] == "charging"
            )["parameters"]
        )
    )
    assert states["chargeTargetLimits"] == {"min": 50, "step": 5}
    vehicle = vehicle_with(states)
    assert (vehicle.charge_target_min, vehicle.charge_target_step) == (50, 5)


@pytest.mark.parametrize(
    "parameters",
    [
        None,
        "x",
        [],
        [{"key": "targetStateOfChargeStepSize", "value": ""}],
        [{"key": "targetStateOfChargeMinimumAllowedValue", "value": "abc"}],
        [{"key": "targetStateOfChargeMinimumAllowedValue", "value": "0"}],
        [{"key": "targetStateOfChargeMinimumAllowedValue", "value": "500"}],
        ["junk", {"key": None}],
    ],
)
def test_missing_or_nonsense_limits_are_left_out(parameters):
    assert _charge_target_limits(parameters) == {}
    assert "chargeTargetLimits" not in _parsed(parameters)


def _number(key, state):
    description = next(d for d in NUMBER_DESCRIPTIONS if d.key == key)
    entity = object.__new__(AudiNumber)
    entity.entity_description = description
    entity._vehicle = vehicle_with(state)
    return entity


def test_the_global_slider_uses_the_cars_limits():
    entity = _number(
        "target_state_of_charge", {"chargeTargetLimits": {"min": 50, "step": 5}}
    )
    assert (entity.native_min_value, entity.native_step) == (50, 5)


def test_without_limits_the_known_api_range_stays():
    entity = _number("target_state_of_charge", {})
    assert (entity.native_min_value, entity.native_step) == (20, 5)


def test_the_profile_slider_ignores_the_global_limits():
    entity = _number(
        "active_charging_profile_target_soc",
        {"chargeTargetLimits": {"min": 50, "step": 10}},
    )
    assert (entity.native_min_value, entity.native_step) == (20, 5)


# --- the slider for the active location profile -----------------------------------


def _profiles(*targets):
    return SimpleNamespace(
        charging_profiles=[
            {"id": i, "name": f"p{i}", "targetSOC_pct": t}
            for i, t in enumerate(targets, 1)
        ]
    )


def test_no_profile_slider_when_no_profile_has_a_target():
    """The A6 lists a profile whose target is null. The slider could never show
    a value, so it is not offered, registry entry or not."""
    from custom_components.audiconnect.number import profile_slider_wanted

    assert profile_slider_wanted(_profiles(None)) is False
    assert profile_slider_wanted(_profiles(None, None)) is False


def test_the_profile_slider_stays_when_a_profile_has_a_target():
    from custom_components.audiconnect.number import profile_slider_wanted

    assert profile_slider_wanted(_profiles(None, 80)) is True


def test_a_poll_without_profiles_does_not_decide():
    from custom_components.audiconnect.number import profile_slider_wanted

    assert profile_slider_wanted(SimpleNamespace()) is True
    assert profile_slider_wanted(_profiles()) is True
