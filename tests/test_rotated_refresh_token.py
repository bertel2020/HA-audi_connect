"""A refresh token the server rotated is kept even when a later step fails."""

from __future__ import annotations

import asyncio
import contextlib
from types import SimpleNamespace

import pytest

from custom_components.ha_audi_connect.audi_auth import AudiAuthError
from custom_components.ha_audi_connect.audi_connect_account import AudiConnectAccount


def _account(service):
    account = AudiConnectAccount(
        session=None, country="DE", spin=None, api_level=1, refresh_token="old"
    )
    account._audi_service = service
    persisted = []
    account.set_refresh_token_listener(persisted.append)
    return account, persisted


def test_the_new_token_is_kept_when_a_step_after_the_refresh_fails():
    state = {"token": "old"}

    async def _refresh(_elapsed):
        state["token"] = "new"  # the identity provider answered ...
        raise RuntimeError("authorization server down")  # ... a later step did not

    service = SimpleNamespace(
        refresh_token_if_necessary=_refresh,
        current_refresh_token=lambda: state["token"],
    )
    account, persisted = _account(service)
    account._loggedin = True
    account._logintime = 0

    with pytest.raises(RuntimeError):
        asyncio.run(account._ensure_fresh_session())
    assert persisted == ["new"]
    assert account._refresh_token == "new"


def test_an_unchanged_token_is_not_persisted_again():
    async def _refresh(_elapsed):
        return False

    service = SimpleNamespace(
        refresh_token_if_necessary=_refresh, current_refresh_token=lambda: "old"
    )
    account, persisted = _account(service)
    account._loggedin = True
    asyncio.run(account._ensure_fresh_session())
    assert persisted == []


@pytest.mark.parametrize("error", [RuntimeError("outage"), AudiAuthError("rejected")])
def test_a_login_that_rotated_the_token_and_then_failed_keeps_the_new_one(error):
    state = {"token": "old"}

    async def _login(_token):
        state["token"] = "new"
        raise error

    service = SimpleNamespace(
        login_with_refresh_token=_login, current_refresh_token=lambda: state["token"]
    )
    account, persisted = _account(service)

    with contextlib.suppress(AudiAuthError):
        asyncio.run(account.try_login(False))
    assert persisted == ["new"]
    assert account._refresh_token == "new"
