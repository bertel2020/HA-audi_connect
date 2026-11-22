"""Entity names come from the translation files, in every language we ship."""

from __future__ import annotations

import importlib
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1] / "custom_components/ha_audi_connect"
PLATFORMS = (
    "sensor",
    "binary_sensor",
    "button",
    "number",
    "switch",
    "select",
    "climate",
    "lock",
    "device_tracker",
)
KEY = re.compile(r'translation_key(?:\s*=\s*)"(\w+)"')


def _entity(lang: str) -> dict:
    return json.loads((ROOT / "translations" / f"{lang}.json").read_text())["entity"]


def _keys_in_code(platform: str) -> set[str]:
    """Keys written out in the source plus those of the description tables."""
    keys = set(KEY.findall((ROOT / f"{platform}.py").read_text()))
    module = importlib.import_module(f"custom_components.ha_audi_connect.{platform}")
    for name in dir(module):
        if name.endswith("_DESCRIPTIONS"):
            keys |= {d.translation_key for d in getattr(module, name)}
    return keys


@pytest.mark.parametrize("platform", PLATFORMS)
@pytest.mark.parametrize("lang", ["en", "de"])
def test_every_key_in_the_code_has_a_name(platform, lang):
    missing = _keys_in_code(platform) - set(_entity(lang).get(platform, {}))

    assert not missing, f"{lang}.json lacks {platform}: {sorted(missing)}"


@pytest.mark.parametrize("platform", PLATFORMS)
def test_no_translation_is_left_without_a_user(platform):
    unused = set(_entity("en").get(platform, {})) - _keys_in_code(platform)

    assert not unused, f"{platform} names nothing uses: {sorted(unused)}"


@pytest.mark.parametrize("platform", PLATFORMS)
def test_german_and_english_cover_the_same_keys(platform):
    assert set(_entity("de").get(platform, {})) == set(_entity("en").get(platform, {}))


def test_placeholders_match_between_languages():
    for platform, names in _entity("en").items():
        for key, value in names.items():
            german = _entity("de")[platform][key]["name"]
            assert set(re.findall(r"\{\w+\}", value["name"])) == set(
                re.findall(r"\{\w+\}", german)
            ), f"{platform}.{key}"


@pytest.mark.parametrize("platform", PLATFORMS)
def test_no_name_is_hard_coded_any_more(platform):
    """A literal name would win over the translation and keep the entity English."""
    source = (ROOT / f"{platform}.py").read_text()

    assert not re.search(r'^\s+name="', source, re.M)
    assert "_attr_name" not in source.replace("self._attr_name", "")


def test_strings_json_carries_the_same_entity_names_as_english():
    strings = json.loads((ROOT / "strings.json").read_text())

    assert strings["entity"] == _entity("en")
