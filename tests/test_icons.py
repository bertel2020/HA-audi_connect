"""Symbols live in icons.json, keyed by each entity's translation key, not in the code."""

from __future__ import annotations

import importlib
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1] / "custom_components/ha_audi_connect"
ICONS = json.loads((ROOT / "icons.json").read_text())["entity"]
PLATFORMS = (
    "binary_sensor",
    "button",
    "climate",
    "device_tracker",
    "lock",
    "number",
    "select",
    "sensor",
    "switch",
)


@pytest.mark.parametrize("platform", PLATFORMS)
def test_no_symbol_is_set_in_the_code(platform):
    source = (ROOT / f"{platform}.py").read_text()
    assert not re.search(r"\bicon\s*=|_attr_icon", source)


def test_every_symbol_is_a_material_design_icon_with_a_default():
    for platform, keys in ICONS.items():
        assert platform in PLATFORMS
        for key, states in keys.items():
            assert re.fullmatch(r"mdi:[a-z0-9-]+", states["default"]), (platform, key)


@pytest.mark.parametrize("platform", ["binary_sensor", "button", "sensor", "switch"])
def test_every_key_in_the_file_names_an_entity_that_exists(platform):
    module = importlib.import_module(f"custom_components.ha_audi_connect.{platform}")
    keys = set()
    for value in vars(module).values():
        if isinstance(value, (tuple, list)):
            keys |= {
                d.translation_key
                for d in value
                if isinstance(getattr(d, "translation_key", None), str)
            }
    source = (ROOT / f"{platform}.py").read_text()
    for key in ICONS.get(platform, {}):
        assert key in keys or f'"{key}"' in source, (platform, key)
