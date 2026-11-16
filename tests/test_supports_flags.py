"""The "supports..." answers of the climatisation capability."""

from custom_components.audiconnect.audi_models import _supports_flags


def test_real_a6_answers_are_read_as_booleans():
    parameters = [
        {"key": "supportsWindowHeatingEnabled", "value": "false"},
        {"key": "supportsZoneFrontLeftEnabled", "value": "true"},
        {"key": "supportsAutomaticMode", "value": ""},
        {"key": "showTargetTemperatureWhenClimaIsRunning", "value": "true"},
        {"key": "supportsOffGridClimatisation", "value": "FALSE"},
    ]
    assert _supports_flags(parameters) == {
        "supportsWindowHeatingEnabled": False,
        "supportsZoneFrontLeftEnabled": True,
        "supportsOffGridClimatisation": False,
    }


def test_garbage_gives_no_flags():
    for bad in (None, {}, "x", [None, {"key": 1, "value": "true"}]):
        assert _supports_flags(bad) == {}
