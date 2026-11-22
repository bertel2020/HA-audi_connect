"""Every shipped language has every key of strings.json, with the same placeholders."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1] / "custom_components/ha_audi_connect"
LANGS = sorted(p.stem for p in (ROOT / "translations").glob("*.json"))
PLACEHOLDER = re.compile(r"\{[^{}]+\}")


def _flat(data: dict, prefix: str = "") -> dict[str, str]:
    out: dict[str, str] = {}
    for key, value in data.items():
        if isinstance(value, dict):
            out.update(_flat(value, f"{prefix}{key}."))
        else:
            out[f"{prefix}{key}"] = value
    return out


SOURCE = _flat(json.loads((ROOT / "strings.json").read_text()))


@pytest.mark.parametrize("lang", LANGS)
def test_language_has_exactly_the_keys_of_strings_json(lang):
    texts = _flat(json.loads((ROOT / "translations" / f"{lang}.json").read_text()))
    assert sorted(set(SOURCE) - set(texts)) == []
    assert sorted(set(texts) - set(SOURCE)) == []


@pytest.mark.parametrize("lang", LANGS)
def test_placeholders_match_the_source(lang):
    texts = _flat(json.loads((ROOT / "translations" / f"{lang}.json").read_text()))
    wrong = {
        key: value
        for key, value in texts.items()
        if key in SOURCE
        and set(PLACEHOLDER.findall(value)) != set(PLACEHOLDER.findall(SOURCE[key]))
    }
    assert wrong == {}


@pytest.mark.parametrize("lang", LANGS)
def test_no_value_is_empty(lang):
    texts = _flat(json.loads((ROOT / "translations" / f"{lang}.json").read_text()))
    assert [k for k, v in texts.items() if isinstance(v, str) and not v.strip()] == []
