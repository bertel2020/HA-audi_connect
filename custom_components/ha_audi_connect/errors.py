"""Errors whose text is translated by Home Assistant, from the "exceptions" part of strings.json."""

from __future__ import annotations

from homeassistant.exceptions import (
    ConfigEntryAuthFailed,
    HomeAssistantError,
    ServiceValidationError,
)

from .const import DOMAIN


def _translation(key: str, placeholders: dict[str, object]) -> dict[str, object]:
    return {
        "translation_domain": DOMAIN,
        "translation_key": key,
        "translation_placeholders": {k: str(v) for k, v in placeholders.items()}
        or None,
    }


def command_error(key: str, **placeholders: object) -> HomeAssistantError:
    """A command to the car failed; the log has the reason."""
    return HomeAssistantError(**_translation(key, placeholders))


def request_error(key: str, **placeholders: object) -> ServiceValidationError:
    """The request itself is wrong, whatever the car does."""
    return ServiceValidationError(**_translation(key, placeholders))


def sign_in_error(key: str, **placeholders: object) -> ConfigEntryAuthFailed:
    """The account has to sign in again."""
    return ConfigEntryAuthFailed(**_translation(key, placeholders))
