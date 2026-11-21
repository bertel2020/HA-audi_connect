"""The wake button is off by default while Audi's wake-up service fails."""

from custom_components.audiconnect.button import BUTTON_DESCRIPTIONS


def _description(key):
    return next(d for d in BUTTON_DESCRIPTIONS if d.key == key)


def test_the_wake_button_is_disabled_in_the_entity_registry_by_default():
    assert _description("wake_vehicle_modern").entity_registry_enabled_default is False


def test_the_refresh_and_flash_buttons_stay_enabled():
    assert _description("refresh_vehicle_data").entity_registry_enabled_default is True
    assert _description("flash_lights").entity_registry_enabled_default is True
