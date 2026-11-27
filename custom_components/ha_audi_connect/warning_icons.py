"""The symbols of the car's warning messages, kept apart from the sensor.

The car sends each warning message with its symbol as a data URI, a few KB of SVG.
Left in the sensor's attributes it would be written to the database on every
change. So the symbol is learned the first time a message shows up, kept once per
`iconName` in a store, and handed to the dashboard card on request.
"""

from __future__ import annotations

import logging
import re
from typing import Any

import voluptuous as vol
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

_STORE_KEY = f"{DOMAIN}.warning_icons"
_STORE_VERSION = 1
_DATA_KEY = f"{DOMAIN}_warning_icons"
_SAVE_DELAY = 30

_NAME = re.compile(r"[A-Za-z0-9_.\-]{1,64}")
_SVG_PREFIX = "data:image/svg+xml;base64,"
# A real symbol is about 2 KB. Anything far beyond that is not one.
_MAX_ICON_CHARS = 20_000
_MAX_ICONS = 500


class WarningIconStore:
    """Symbols by `iconName`, loaded once and written back in the background."""

    def __init__(self, hass: HomeAssistant) -> None:
        self._store: Store[dict[str, Any]] = Store(hass, _STORE_VERSION, _STORE_KEY)
        self._icons: dict[str, str] = {}

    async def async_load(self) -> None:
        data = await self._store.async_load()
        icons = data.get("icons") if isinstance(data, dict) else None
        if isinstance(icons, dict):
            self._icons = {
                k: v for k, v in icons.items() if _valid(k, v)
            }

    @property
    def icons(self) -> dict[str, str]:
        return dict(self._icons)

    def learn(self, lights: Any) -> bool:
        """Keep the symbols of the given warning messages. True when one was new."""
        if not isinstance(lights, list):
            return False
        added = False
        for item in lights:
            if not isinstance(item, dict):
                continue
            name, icon = item.get("iconName"), item.get("icon")
            if name in self._icons or len(self._icons) >= _MAX_ICONS:
                continue
            if _valid(name, icon):
                self._icons[name] = icon
                added = True
        if added:
            self._store.async_delay_save(lambda: {"icons": self._icons}, _SAVE_DELAY)
        return added


def _valid(name: Any, icon: Any) -> bool:
    return (
        isinstance(name, str)
        and _NAME.fullmatch(name) is not None
        and isinstance(icon, str)
        and icon.startswith(_SVG_PREFIX)
        and len(icon) <= _MAX_ICON_CHARS
    )


async def async_get_icon_store(hass: HomeAssistant) -> WarningIconStore:
    """The one store of this Home Assistant, loaded on first use."""
    store = hass.data.get(_DATA_KEY)
    if store is None:
        store = WarningIconStore(hass)
        await store.async_load()
        hass.data[_DATA_KEY] = store
    return store


def async_register_icon_command(hass: HomeAssistant) -> None:
    """Let the card ask for the symbols it has no copy of yet."""
    from homeassistant.components import websocket_api

    @websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/warning_icons"})
    @websocket_api.async_response
    async def _warning_icons(
        hass: HomeAssistant, connection: Any, msg: dict[str, Any]
    ) -> None:
        store = await async_get_icon_store(hass)
        connection.send_result(msg["id"], store.icons)

    websocket_api.async_register_command(hass, _warning_icons)
