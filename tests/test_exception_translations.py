"""Every error the user can see comes from strings.json and is translated everywhere."""

from __future__ import annotations

import json
import re
from pathlib import Path

from homeassistant.exceptions import (
    ConfigEntryAuthFailed,
    HomeAssistantError,
    ServiceValidationError,
)

from custom_components.ha_audi_connect.errors import (
    command_error,
    request_error,
    sign_in_error,
)

ROOT = Path(__file__).resolve().parents[1] / "custom_components/ha_audi_connect"
STRINGS = json.loads((ROOT / "strings.json").read_text())["exceptions"]
HELPERS = re.compile(r'(?:command_error|request_error|sign_in_error)\(\s*"(\w+)"')
SIGN_IN = re.compile(r'"(sign_in_(?:again|credentials))"')


def _keys_in_code() -> set[str]:
    keys: set[str] = set()
    for path in ROOT.glob("*.py"):
        if path.name == "errors.py":
            continue
        source = path.read_text()
        keys |= set(HELPERS.findall(source)) | set(SIGN_IN.findall(source))
    return keys


def test_every_key_the_code_raises_has_a_text_and_no_text_is_unused():
    assert _keys_in_code() == set(STRINGS)


def _calls(source: str):
    """Each helper call as (key, text of its keyword arguments), by counting brackets."""
    for match in re.finditer(r"(?:command_error|request_error)\(", source):
        depth, i = 1, match.end()
        while depth:
            depth += {"(": 1, ")": -1}.get(source[i], 0)
            i += 1
        body = source[match.end() : i - 1]
        key = re.match(r'\s*"(\w+)"', body)
        if key:
            yield key.group(1), body[key.end() :]


def _keyword_names(arguments: str) -> set[str]:
    """Names of the keyword arguments at the top level of the call."""
    names, depth = set(), 0
    for position, char in enumerate(arguments):
        depth += {"(": 1, ")": -1}.get(char, 0)
        if depth == 0:
            found = re.match(r"\s*,\s*(\w+)=", arguments[position:])
            if found:
                names.add(found.group(1))
    return names


def test_the_placeholders_of_each_text_are_the_ones_the_code_passes():
    checked = 0
    for path in ROOT.glob("*.py"):
        if path.name == "errors.py":
            continue
        for key, arguments in _calls(path.read_text()):
            wanted = set(re.findall(r"\{(\w+)\}", STRINGS[key]["message"]))
            assert _keyword_names(arguments) == wanted, (path.name, key)
            checked += 1
    assert checked > 15


def test_the_helpers_build_translated_errors():
    error = command_error("lock_failed", action="lock")
    assert isinstance(error, HomeAssistantError)
    assert error.translation_domain == "ha_audi_connect"
    assert error.translation_key == "lock_failed"
    assert error.translation_placeholders == {"action": "lock"}
    assert isinstance(request_error("probe_path_invalid"), ServiceValidationError)
    assert request_error("probe_path_invalid").translation_placeholders is None
    assert isinstance(sign_in_error("sign_in_again"), ConfigEntryAuthFailed)
