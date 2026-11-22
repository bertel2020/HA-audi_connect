"""The horn is its own, disabled-by-default control; flashing stays silent."""

from __future__ import annotations

import asyncio
import json

from custom_components.ha_audi_connect.button import BUTTON_DESCRIPTIONS
from tests.test_flash_lights import LAT, LON, VIN, service, sent


def test_the_horn_posts_the_honking_mode():
    svc = service()
    asyncio.run(svc.honk_horn(VIN, LAT, LON))
    call, body = sent(svc)
    assert call["method"] == "POST"
    assert call["url"].endswith(f"/vehicles/{VIN}/honkandflash")
    assert body["mode"] == "honkandflash"
    assert body["userPosition"] == {"latitude": LAT, "longitude": LON}


def test_flashing_is_still_silent():
    svc = service()
    asyncio.run(svc.flash_lights(VIN, LAT, LON))
    assert json.loads(svc._api.calls[0]["data"])["mode"] == "flash"


def test_the_horn_button_is_off_until_the_user_turns_it_on():
    button = next(b for b in BUTTON_DESCRIPTIONS if b.key == "honk_horn")
    assert button.entity_registry_enabled_default is False


def test_the_flash_button_stays_on_by_default():
    button = next(b for b in BUTTON_DESCRIPTIONS if b.key == "flash_lights")
    assert button.entity_registry_enabled_default is True


def test_the_buttons_are_named_after_what_the_app_calls_them():
    """The app says "Blinken" and "Hupen und Blinken". The flash is no "Lichthupe":
    that is the headlight flasher, a different thing."""
    import json
    from pathlib import Path

    root = Path(__file__).parent.parent / "custom_components" / "ha_audi_connect"
    de = json.loads((root / "translations/de.json").read_text(encoding="utf-8"))
    en = json.loads((root / "translations/en.json").read_text(encoding="utf-8"))
    assert de["entity"]["button"]["flash_lights"]["name"] == "Blinken"
    assert de["entity"]["button"]["honk_horn"]["name"] == "Hupen und Blinken"
    assert en["entity"]["button"]["flash_lights"]["name"] == "Flash"
    assert en["entity"]["button"]["honk_horn"]["name"] == "Honk and flash"
