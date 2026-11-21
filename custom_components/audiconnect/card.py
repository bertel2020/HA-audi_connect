"""Serve the dashboard card that ships with the integration.

The card is one JavaScript file in `www/`. Registering it here means it is loaded on
every dashboard by itself: nothing to download, no resource to add, no YAML to write.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any
from urllib.parse import quote

import voluptuous as vol
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

CARD_FILE = Path(__file__).parent / "www" / "audi-connect-card.js"
CARD_URL = f"/{DOMAIN}_static/audi-connect-card.js"
_REGISTERED = f"{DOMAIN}_card_registered"

_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg", ".avif"}
_MAX_IMAGES = 500
# Folders under www that hold other people's files, not pictures to pick from.
_SKIP_DIRS = {"community"}


def list_www_images(www: Path) -> list[dict[str, str]]:
    """The pictures in the www folder, as the /local/ paths a browser can load."""
    found: list[dict[str, str]] = []
    if not www.is_dir():
        return found
    for root, dirs, files in os.walk(www):
        dirs[:] = sorted(
            d for d in dirs if not d.startswith(".") and d not in _SKIP_DIRS
        )
        for name in sorted(files):
            if name.startswith(".") or Path(name).suffix.lower() not in _IMAGE_SUFFIXES:
                continue
            rel = (Path(root) / name).relative_to(www).as_posix()
            found.append({"path": f"/local/{quote(rel)}", "name": rel})
            if len(found) >= _MAX_IMAGES:
                return found
    return found


async def async_register_card(hass: HomeAssistant) -> None:
    """Serve the card file and have the frontend load it. Safe to call repeatedly.

    A failure here only costs the card; it must never stop the integration itself.
    """
    if hass.data.get(_REGISTERED):
        return
    try:
        from homeassistant.components.frontend import add_extra_js_url
        from homeassistant.components.http import StaticPathConfig

        if getattr(hass, "http", None) is None:
            return
        # The file's age is the cache buster, so a new card version is picked up
        # without clearing the browser cache.
        mtime = await hass.async_add_executor_job(
            lambda: int(CARD_FILE.stat().st_mtime)
        )
        await hass.http.async_register_static_paths(
            [StaticPathConfig(CARD_URL, str(CARD_FILE), False)]
        )
        add_extra_js_url(hass, f"{CARD_URL}?v={mtime}")
        _register_image_list(hass)
        hass.data[_REGISTERED] = True
    except Exception:  # noqa: BLE001 - the card is optional
        _LOGGER.warning(
            "Could not register the Audi Connect dashboard card", exc_info=True
        )


def _register_image_list(hass: HomeAssistant) -> None:
    """Let the card editor offer the pictures in the www folder."""
    from homeassistant.components import websocket_api

    @websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/list_images"})
    @websocket_api.require_admin
    @websocket_api.async_response
    async def _list_images(
        hass: HomeAssistant, connection: Any, msg: dict[str, Any]
    ) -> None:
        images = await hass.async_add_executor_job(
            list_www_images, Path(hass.config.path("www"))
        )
        connection.send_result(msg["id"], images)

    websocket_api.async_register_command(hass, _list_images)
