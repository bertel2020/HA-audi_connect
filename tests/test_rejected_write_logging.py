"""A refused write says why, without leaking the VIN or the request."""

from __future__ import annotations

import asyncio
import logging
from types import SimpleNamespace

import pytest
from aiohttp import ClientResponseError

from custom_components.audiconnect.audi_api import AudiAPI

VIN = "WAUZZZGH7SA009401"
URL = (
    f"https://emea.bff.cariad.digital/vehicle/v1/vehicles/{VIN}/climatisation/settings"
)


class _Response:
    def __init__(self, status, reason, body):
        self.status = status
        self.reason = reason
        self.headers = {}
        self.request_info = SimpleNamespace(real_url=URL)
        self.history = ()
        self._body = body

    async def text(self):
        return self._body

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False


class _Session:
    def __init__(self, response):
        self._response = response

    def request(self, *a, **kw):
        return self._response


def _send(method, status, body):
    api = AudiAPI(_Session(_Response(status, "Bad Gateway", body)))
    with pytest.raises(ClientResponseError):
        asyncio.run(api.request(method, URL, data="{}"))


def test_a_refused_put_logs_the_reply_and_masks_the_vin(caplog):
    with caplog.at_level(logging.WARNING):
        _send("PUT", 502, f'{{"error":"upstream failed for {VIN}"}}')
    text = caplog.text
    assert "upstream failed" in text
    assert VIN not in text and "<vin>" in text
    assert "502" in text


def test_the_body_that_was_sent_is_logged_too(caplog):
    api = AudiAPI(_Session(_Response(502, "Bad Gateway", "{}")))
    with caplog.at_level(logging.WARNING), pytest.raises(ClientResponseError):
        asyncio.run(api.request("PUT", URL, data='{"zoneFrontLeftEnabled": true}'))
    assert "zoneFrontLeftEnabled" in caplog.text


def test_the_reply_is_capped(caplog):
    with caplog.at_level(logging.WARNING):
        _send("PUT", 502, "x" * 5000)
    assert "x" * 400 not in caplog.text


def test_a_refused_read_is_not_logged_as_a_warning(caplog):
    with caplog.at_level(logging.WARNING):
        _send("GET", 404, "nope")
    assert "Audi rejected" not in caplog.text
