"""Creating and deleting climatisation timers, in the shape the myAudi app sends."""

from __future__ import annotations

import asyncio
import json

import pytest

from custom_components.audiconnect.audi_payloads import build_climatisation_timer
from custom_components.audiconnect.audi_services import AudiService

VIN = "WAUZZZ00000000001"


def body(**kw):
    defaults = dict(repeat=True, enabled=True, utc_offset_minutes=60)
    defaults.update(kw)
    return build_climatisation_timer(
        kw.pop("time", "07:30") if "time" in kw else "07:30",
        kw.pop("days", ["monday", "friday"]) if "days" in kw else ["monday", "friday"],
        **{k: v for k, v in defaults.items() if k not in ("time", "days")},
    )


def test_a_recurring_timer_names_its_days_and_both_clocks():
    timer = body()["timer"]
    assert timer["enabled"] is True
    recurring = timer["recurringTimer"]
    assert recurring["startTimeLocal"] == "07:30"
    assert recurring["startTime"] == "06:30"
    assert recurring["recurringOn"] == {
        "mondays": True,
        "tuesdays": False,
        "wednesdays": False,
        "thursdays": False,
        "fridays": True,
        "saturdays": False,
        "sundays": False,
    }
    assert "singleTimer" not in timer


def test_a_single_timer_names_one_day():
    timer = body(repeat=False, days=["Wednesday"])["timer"]
    assert timer["singleTimer"] == {
        "occurringOn": "Wednesday",
        "startTime": "06:30",
        "startTimeLocal": "07:30",
    }
    assert "recurringTimer" not in timer


def test_the_utc_time_wraps_around_midnight():
    timer = body(time="00:15", utc_offset_minutes=120)["timer"]
    assert timer["recurringTimer"]["startTime"] == "22:15"


@pytest.mark.parametrize(
    "kwargs",
    [
        {"days": []},
        {"days": ["someday"]},
        {"time": "25:00"},
        {"time": "7h30"},
        {"repeat": False, "days": ["monday", "tuesday"]},
    ],
)
def test_nonsense_is_refused_before_anything_is_sent(kwargs):
    with pytest.raises(ValueError):
        body(**kwargs)


class Api:
    def __init__(self):
        self.calls = []

    def use_token(self, *_):
        pass

    async def get(self, url):
        self.calls.append(("GET", url, None))
        return {
            "departureTimers": {
                "climatisationTimersStatus": {
                    "value": {"timeInCar": "2026-11-16T20:52:55+01:00", "timers": []}
                }
            }
        }

    async def request(self, method, url, data=None, headers=None, **kw):
        self.calls.append((method, url, data, headers))
        return None


def service():
    svc = object.__new__(AudiService)
    svc._api = Api()
    svc._bearer_token_json = {"access_token": "x"}
    svc._country = "DE"
    svc._api_level = 1
    return svc


def test_creating_posts_to_the_v2_departure_path_with_json():
    svc = service()
    asyncio.run(svc.create_climatisation_timer(VIN, "07:30", ["monday"]))
    method, url, data, headers = svc._api.calls[-1]
    assert method == "POST"
    assert url.endswith(f"/vehicle/v2/departure/{VIN}/climatisation/timers")
    assert headers["Content-Type"] == "application/json"
    sent = json.loads(data)["timer"]
    assert sent["recurringTimer"]["startTime"] == "06:30"  # the car is at UTC+1


def test_the_car_must_report_its_clock_or_nothing_is_sent():
    svc = service()

    async def no_clock(url):
        svc._api.calls.append(("GET", url, None))
        return {"departureTimers": {"climatisationTimersStatus": {"value": {}}}}

    svc._api.get = no_clock
    with pytest.raises(ValueError, match="local time"):
        asyncio.run(svc.create_climatisation_timer(VIN, "07:30", ["monday"]))
    assert all(call[0] == "GET" for call in svc._api.calls)


def test_deleting_sends_a_delete_to_the_timer():
    svc = service()
    asyncio.run(svc.delete_climatisation_timer(VIN, 3))
    method, url, data, _ = svc._api.calls[-1]
    assert method == "DELETE"
    assert url.endswith(f"/vehicle/v2/departure/{VIN}/climatisation/timers/3")
    assert data is None
