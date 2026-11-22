"""The "supports..." answers of the climatisation capability."""

from custom_components.ha_audi_connect.audi_models import _supports_flags


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


def test_the_window_heating_buttons_follow_the_cars_own_answer():
    from types import SimpleNamespace

    from custom_components.ha_audi_connect.button import _window_heating_capable

    def car(flags):
        return SimpleNamespace(
            _audi_service=SimpleNamespace(uses_auth0=True),
            has_capability=lambda c: c == "climatisation",
            impaired_capabilities=frozenset(),
            climatisation_supports=flags,
        )

    assert _window_heating_capable(car({})) is True
    assert _window_heating_capable(car({"supportsWindowHeatingEnabled": True})) is True
    assert (
        _window_heating_capable(car({"supportsWindowHeatingEnabled": False})) is False
    )
