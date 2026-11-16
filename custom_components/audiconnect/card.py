"""Serve the dashboard card that ships with the integration.

The card is one JavaScript file in `www/`. Registering it here means it is loaded on
every dashboard by itself: nothing to download, no resource to add, no YAML to write.
"""

from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

CARD_FILE = Path(__file__).parent / "www" / "audi-connect-card.js"
CARD_URL = f"/{DOMAIN}_static/audi-connect-card.js"
_REGISTERED = f"{DOMAIN}_card_registered"


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
        mtime = await hass.async_add_executor_job(lambda: int(CARD_FILE.stat().st_mtime))
        await hass.http.async_register_static_paths(
            [StaticPathConfig(CARD_URL, str(CARD_FILE), False)]
        )
        add_extra_js_url(hass, f"{CARD_URL}?v={mtime}")
        hass.data[_REGISTERED] = True
    except Exception:  # noqa: BLE001 - the card is optional
        _LOGGER.warning("Could not register the Audi Connect dashboard card", exc_info=True)
