"""Hints about ended or ending online services: raised, changed and cleared per car."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest

from custom_components.ha_audi_connect import repairs

NOW = datetime(2026, 11, 22, 9, 0, tzinfo=UTC)
ROOT = Path(__file__).resolve().parents[1] / "custom_components/ha_audi_connect"


@pytest.fixture
def issues(monkeypatch):
    log = {"created": {}, "deleted": []}
    monkeypatch.setattr(
        repairs.ir,
        "async_create_issue",
        lambda hass, domain, issue_id, **kw: log["created"].__setitem__(issue_id, kw),
    )
    monkeypatch.setattr(
        repairs.ir,
        "async_delete_issue",
        lambda hass, domain, issue_id: log["deleted"].append(issue_id),
    )
    return log


def _car(expiry, vin="WAUZZZ0001", title="My Audi"):
    return SimpleNamespace(vin=vin, title=title, service_expiry=expiry)


def _update(vehicles):
    repairs.async_update_service_issues(None, "entry", vehicles, now=NOW)


def test_far_away_dates_raise_nothing_and_clear_old_hints(issues):
    _update([_car({"a": NOW + timedelta(days=500)})])
    assert issues["created"] == {}
    assert len(issues["deleted"]) == 2


def test_a_service_that_ended_raises_the_ended_hint(issues):
    _update([_car({"nav": NOW - timedelta(days=3), "radio": NOW + timedelta(days=2)})])
    (kind,) = {kw["translation_key"] for kw in issues["created"].values()}
    assert kind == "services_expired"
    placeholders = next(iter(issues["created"].values()))["translation_placeholders"]
    assert placeholders == {
        "vehicle": "My Audi",
        "services": "nav",
        "date": (NOW - timedelta(days=3)).date().isoformat(),
    }
    assert any(i.startswith("services_ending_soon") for i in issues["deleted"])


def test_a_service_ending_within_a_month_raises_the_soon_hint(issues):
    _update([_car({"nav": NOW + timedelta(days=10)})])
    (kind,) = {kw["translation_key"] for kw in issues["created"].values()}
    assert kind == "services_ending_soon"
    assert all(kw["is_fixable"] is False for kw in issues["created"].values())


def test_ended_wins_over_ending_soon(issues):
    _update([_car({"a": NOW - timedelta(days=1), "b": NOW + timedelta(days=5)})])
    assert [kw["translation_key"] for kw in issues["created"].values()] == [
        "services_expired"
    ]


def test_dates_without_a_time_zone_are_ignored(issues):
    _update([_car({"a": datetime(2020, 1, 1), "b": "2020-01-01", "c": None})])
    assert issues["created"] == {}


def test_the_vin_is_not_part_of_the_issue_id_and_each_car_has_its_own(issues):
    _update(
        [
            _car({"a": NOW - timedelta(days=1)}, vin="WAUZZZ0001"),
            _car({"a": NOW - timedelta(days=1)}, vin="WAUZZZ0002"),
            SimpleNamespace(vin=None, service_expiry={}),
        ]
    )
    assert len(issues["created"]) == 2
    assert not any("WAUZZZ" in issue_id for issue_id in issues["created"])


def test_the_texts_exist_in_every_language_with_the_placeholders_in_use():
    for path in [ROOT / "strings.json", *(ROOT / "translations").glob("*.json")]:
        data = json.loads(path.read_text())["issues"]
        for kind in ("services_expired", "services_ending_soon"):
            assert "{vehicle}" in data[kind]["title"], (path.name, kind)
            for placeholder in ("{date}", "{services}"):
                assert placeholder in data[kind]["description"], (path.name, kind)


def test_clearing_an_entry_removes_only_its_hints(monkeypatch):
    removed = []
    registry = SimpleNamespace(
        issues={
            ("ha_audi_connect", "services_expired_entry1_aa"): 1,
            ("ha_audi_connect", "services_ending_soon_entry2_bb"): 1,
            ("other", "services_expired_entry1_cc"): 1,
        }
    )
    monkeypatch.setattr(repairs.ir, "async_get", lambda hass: registry)
    monkeypatch.setattr(
        repairs.ir,
        "async_delete_issue",
        lambda hass, domain, issue_id: removed.append(issue_id),
    )
    repairs.async_clear_service_issues(None, "entry1")
    assert removed == ["services_expired_entry1_aa"]


def _coordinator(vehicles):
    return SimpleNamespace(
        hass="hass",
        config_entry=SimpleNamespace(entry_id="entry"),
        account=SimpleNamespace(
            config_vehicles=[SimpleNamespace(vehicle=v) for v in [*vehicles, None]]
        ),
    )


def test_a_poll_hands_the_known_cars_to_the_hints(monkeypatch):
    from custom_components.ha_audi_connect import coordinator

    seen = []
    monkeypatch.setattr(
        coordinator, "async_update_service_issues", lambda *args: seen.append(args)
    )
    car = _car({})
    coordinator.AudiDataUpdateCoordinator._update_repair_hints(_coordinator([car]))
    assert seen == [("hass", "entry", [car])]


def test_a_failing_hint_never_fails_the_poll(monkeypatch):
    from custom_components.ha_audi_connect import coordinator

    def boom(*args):
        raise RuntimeError("no registry")

    monkeypatch.setattr(coordinator, "async_update_service_issues", boom)
    coordinator.AudiDataUpdateCoordinator._update_repair_hints(_coordinator([_car({})]))


def test_removing_an_entry_clears_its_hints(monkeypatch):
    import asyncio

    from custom_components import ha_audi_connect as integration

    cleared = []
    monkeypatch.setattr(
        integration,
        "async_clear_service_issues",
        lambda hass, entry_id: cleared.append(entry_id),
    )
    asyncio.run(integration.async_remove_entry(None, SimpleNamespace(entry_id="entry")))
    assert cleared == ["entry"]
