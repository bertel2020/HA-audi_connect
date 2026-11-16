"""The on/off switch uses an icon Home Assistant knows, and the charge modes have names."""

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

from custom_components.audiconnect.switch import AudiClimateQuickSwitch

TRANSLATIONS = Path(__file__).parent.parent / "custom_components" / "audiconnect"


def test_the_climate_switch_icon_is_a_real_one():
    # "mdi:car-air-conditioner" does not exist and shows as no icon at all.
    switch = AudiClimateQuickSwitch(MagicMock(), SimpleNamespace(vin="V1"))
    assert switch.icon == "mdi:air-conditioner"


def test_every_charge_mode_the_select_can_offer_has_a_translated_name():
    from custom_components.audiconnect.select import _FALLBACK_MODES

    for name in ("translations/en.json", "translations/de.json", "strings.json"):
        data = json.loads((TRANSLATIONS / name).read_text(encoding="utf-8"))
        states = data["entity"]["select"]["charge_mode"]["state"]
        assert set(_FALLBACK_MODES) <= set(states), name
