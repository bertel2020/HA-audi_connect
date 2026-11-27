"""The card is served and loaded by the integration; a failure there must not stop it."""

from __future__ import annotations

import asyncio
import logging
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from custom_components.ha_audi_connect import card


def make_hass(with_http=True):
    hass = SimpleNamespace(data={})
    hass.http = SimpleNamespace(async_register_static_paths=AsyncMock())
    if not with_http:
        hass.http = None

    async def _executor(fn, *args):
        return fn(*args)

    hass.async_add_executor_job = _executor
    hass.config = SimpleNamespace(path=lambda *p: "/nonexistent/" + "/".join(p))
    return hass


def register(hass):
    with (
        patch("homeassistant.components.frontend.add_extra_js_url") as add_url,
        patch("homeassistant.components.websocket_api.async_register_command") as ws,
    ):
        asyncio.run(card.async_register_card(hass))
        return add_url, ws


def test_the_card_is_served_and_loaded_with_a_cache_buster():
    hass = make_hass()
    add_url, ws = register(hass)
    hass.http.async_register_static_paths.assert_awaited_once()
    config = hass.http.async_register_static_paths.await_args.args[0][0]
    assert config.url_path == card.CARD_URL
    assert config.path == str(card.CARD_FILE)
    url = add_url.call_args.args[1]
    assert url.startswith(card.CARD_URL + "?v=") and url.split("=")[1].isdigit()
    assert hass.data[card._REGISTERED] is True


def test_the_card_commands_are_registered():
    _, ws = register(make_hass())
    commands = {call.args[1]._ws_command for call in ws.call_args_list}
    assert commands == {
        "ha_audi_connect/list_images",
        "ha_audi_connect/warning_icons",
    }


def test_registering_twice_does_nothing_the_second_time():
    hass = make_hass()
    register(hass)
    add_url, ws = register(hass)
    assert hass.http.async_register_static_paths.await_count == 1
    add_url.assert_not_called()
    ws.assert_not_called()


def test_without_an_http_component_nothing_is_registered():
    hass = make_hass(with_http=False)
    add_url, _ = register(hass)
    add_url.assert_not_called()
    assert card._REGISTERED not in hass.data


def test_a_failure_costs_only_the_card(caplog):
    hass = make_hass()
    hass.http.async_register_static_paths = AsyncMock(side_effect=RuntimeError("boom"))
    with caplog.at_level(logging.WARNING):
        register(hass)
    assert "Could not register the Audi Connect dashboard card" in caplog.text
    assert card._REGISTERED not in hass.data


def test_the_card_file_exists_where_it_is_served_from():
    assert card.CARD_FILE.is_file()
