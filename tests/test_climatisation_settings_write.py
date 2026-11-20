"""Writing climatisation settings.

PUT climatisation/settings takes the whole object, so a single toggle has to
round-trip every other field or it clears them. Same hazard as the charging
profile write, and the same read-modify-write answer.

The endpoint was previously recorded as not existing, on the strength of a GET
returning 404. It means there is no GET route: the honk-and-flash work found
the identical 404-on-GET for a path that is real for POST.
"""

from __future__ import annotations

import asyncio
import copy
import json

import pytest

from custom_components.audiconnect.audi_services import (
    build_climatisation_settings_update,
)

from tests.fixture_q8_etron import PAYLOAD


def settings():
    return copy.deepcopy(PAYLOAD["climatisation"]["climatisationSettings"]["value"])


# --- the read-modify-write core ---------------------------------------------------


def test_every_other_field_survives_one_change():
    """The whole point. Toggling a seat must not clear the temperature."""
    current = settings()
    body = build_climatisation_settings_update(current, zoneFrontLeftEnabled=True)
    assert body["zoneFrontLeftEnabled"] is True
    # The app names the target temperature "targetTemperature" with a unit.
    assert body["targetTemperature"] == current["targetTemperature_C"]
    assert body["targetTemperatureUnit"] == "celsius"
    for field in (
        "climatizationAtUnlock",
        "windowHeatingEnabled",
        "climatisationWithoutExternalPower",
    ):
        assert body[field] == current[field], field


def test_the_server_timestamp_is_not_echoed_back():
    body = build_climatisation_settings_update(settings(), windowHeatingEnabled=True)
    assert "carCapturedTimestamp" not in body
    # control: it is in the source object
    assert "carCapturedTimestamp" in settings()


def test_several_fields_can_change_at_once():
    body = build_climatisation_settings_update(
        settings(), zoneFrontLeftEnabled=True, zoneFrontRightEnabled=True
    )
    assert body["zoneFrontLeftEnabled"] is True
    assert body["zoneFrontRightEnabled"] is True


def test_a_field_the_car_did_not_report_can_still_be_set():
    """This car reports no rear zones. Setting one adds it rather than failing,
    since the car decides what it accepts."""
    body = build_climatisation_settings_update(settings(), zoneRearLeftEnabled=True)
    assert body["zoneRearLeftEnabled"] is True


@pytest.mark.parametrize("bad", ["targetSOC_pct", "mode", "honk", "zoneFrontLeft"])
def test_a_field_that_is_not_a_setting_is_refused(bad):
    """A typo becomes an error here rather than a field the car silently
    ignores."""
    with pytest.raises(ValueError, match="Not climatisation settings"):
        build_climatisation_settings_update(settings(), **{bad: True})


@pytest.mark.parametrize("empty", [None, {}, "notadict", []])
def test_it_refuses_to_build_from_nothing(empty):
    """Without the current settings there is nothing to preserve, and sending a
    lone field would clear the rest."""
    with pytest.raises(ValueError, match="No climatisation settings"):
        build_climatisation_settings_update(empty, windowHeatingEnabled=True)


# --- the request ------------------------------------------------------------------


class Api:
    def __init__(self, current):
        self.current = current
        self.calls = []
        self.headers = []

    def use_token(self, *_):
        pass

    async def get(self, url):
        self.calls.append(("GET", url, None))
        return {"climatisation": {"climatisationSettings": {"value": self.current}}}

    async def request(self, method, url, data=None, headers=None, **kw):
        self.calls.append((method, url, data))
        self.headers.append(headers or {})
        return None


def service(current=None):
    from custom_components.audiconnect import audi_services

    svc = object.__new__(audi_services.AudiService)
    svc._api = Api(settings() if current is None else current)
    svc._bearer_token_json = {"access_token": "x"}
    svc._country = "DE"
    svc._api_level = 1
    return svc


def test_it_reads_then_puts_the_whole_object():
    svc = service()
    asyncio.run(svc.set_climatisation_settings("VIN1", windowHeatingEnabled=True))
    methods = [c[0] for c in svc._api.calls]
    assert methods == ["GET", "PUT"], "must read before writing"

    put = svc._api.calls[1]
    assert put[1].endswith("/climatisation/settings")
    body = json.loads(put[2])
    assert body["windowHeatingEnabled"] is True
    assert body["targetTemperature"] == settings()["targetTemperature_C"]


def test_it_sends_nothing_when_the_car_reports_no_settings():
    svc = service(current={})
    with pytest.raises(ValueError):
        asyncio.run(svc.set_climatisation_settings("VIN1", windowHeatingEnabled=True))
    assert [c[0] for c in svc._api.calls] == ["GET"], "must not PUT a lone field"


# --- the switches -----------------------------------------------------------------


def test_each_setting_switch_writes_its_own_field():
    from custom_components.audiconnect.switch import SWITCH_DESCRIPTIONS

    class Conn:
        def __init__(self):
            self.calls = []

        async def set_climatisation_setting(self, vin, field, value):
            self.calls.append((field, value))
            return True

    expected = {
        "climatisation_window_heating": "windowHeatingEnabled",
        "climatisation_at_unlock": "climatizationAtUnlock",
        "climatisation_zone_front_left": "zoneFrontLeftEnabled",
        "climatisation_zone_front_right": "zoneFrontRightEnabled",
        "climatisation_zone_rear_left": "zoneRearLeftEnabled",
        "climatisation_zone_rear_right": "zoneRearRightEnabled",
    }
    seen = {}
    for d in SWITCH_DESCRIPTIONS:
        if d.key not in expected:
            continue
        conn = Conn()
        asyncio.run(d.turn_on_fn(conn, "VIN1"))
        asyncio.run(d.turn_off_fn(conn, "VIN1"))
        seen[d.key] = conn.calls

    assert set(seen) == set(expected), "a setting switch went missing"
    for key, field in expected.items():
        assert seen[key] == [(field, True), (field, False)], key


def test_the_lambdas_bound_their_own_field():
    """Closures over a loop variable would give every switch the last field.
    This is the case that would make six switches all write the rear right seat."""
    from custom_components.audiconnect.switch import SWITCH_DESCRIPTIONS

    fields = set()

    class Conn:
        async def set_climatisation_setting(self, vin, field, value):
            fields.add(field)
            return True

    for d in SWITCH_DESCRIPTIONS:
        if d.key.startswith("climatisation_"):
            asyncio.run(d.turn_on_fn(Conn(), "VIN1"))
    assert len(fields) == 6, f"expected six distinct fields, got {fields}"


A6_SETTINGS = {
    "carCapturedTimestamp": "2026-11-15T17:36:17+00:00",
    "targetTemperature_C": 22.5,
    "targetTemperature_F": 73,
    "unitInCar": "celsius",
    "climatisationMode": "economy",
    "climatizationAtUnlock": False,
    "windowHeatingEnabled": False,
    "zoneFrontLeftEnabled": True,
    "zoneFrontRightEnabled": True,
    "zoneRearLeftEnabled": False,
    "zoneRearRightEnabled": False,
}


def test_the_a6_body_carries_only_writable_settings():
    body = build_climatisation_settings_update(
        A6_SETTINGS, variant="full", climatizationAtUnlock=True
    )
    assert body == {
        "targetTemperature_C": 22.5,
        "climatisationMode": "economy",
        "climatizationAtUnlock": True,
        "windowHeatingEnabled": False,
        "zoneFrontLeftEnabled": True,
        "zoneFrontRightEnabled": True,
        "zoneRearLeftEnabled": False,
        "zoneRearRightEnabled": False,
    }


# --- body variants for finding what the A6 accepts ---------------------------------


def test_without_window_heating_drops_only_that_setting():
    body = build_climatisation_settings_update(
        A6_SETTINGS, variant="without_window_heating", climatizationAtUnlock=True
    )
    assert "windowHeatingEnabled" not in body
    assert body["climatizationAtUnlock"] is True
    assert body["zoneFrontLeftEnabled"] is True


def test_without_window_heating_still_sends_it_when_that_is_the_change():
    body = build_climatisation_settings_update(
        A6_SETTINGS, variant="without_window_heating", windowHeatingEnabled=True
    )
    assert body["windowHeatingEnabled"] is True


def test_single_field_sends_only_the_change():
    body = build_climatisation_settings_update(
        A6_SETTINGS, variant="single_field", climatizationAtUnlock=True
    )
    assert body == {"climatizationAtUnlock": True}


def test_an_unknown_variant_is_refused():
    with pytest.raises(ValueError, match="variant"):
        build_climatisation_settings_update(A6_SETTINGS, variant="all")


def test_single_field_puts_without_reading_first():
    svc = service()
    asyncio.run(
        svc.set_climatisation_settings(
            "VIN1", variant="single_field", climatizationAtUnlock=True
        )
    )
    assert [c[0] for c in svc._api.calls] == ["PUT"]
    assert json.loads(svc._api.calls[0][2]) == {"climatizationAtUnlock": True}


def test_the_default_stays_the_full_body():
    svc = service()
    asyncio.run(svc.set_climatisation_settings("VIN1", windowHeatingEnabled=True))
    assert [c[0] for c in svc._api.calls] == ["GET", "PUT"]


def test_the_write_method_can_be_post_and_defaults_to_put():
    svc = service()
    asyncio.run(
        svc.set_climatisation_settings(
            "VIN1", variant="single_field", method="POST", climatizationAtUnlock=True
        )
    )
    assert svc._api.calls[-1][0] == "POST"
    svc = service()
    asyncio.run(svc.set_climatisation_settings("VIN1", windowHeatingEnabled=True))
    assert svc._api.calls[-1][0] == "PUT"


def test_an_unknown_write_method_is_refused_before_anything_is_sent():
    svc = service()
    with pytest.raises(ValueError, match="method"):
        asyncio.run(
            svc.set_climatisation_settings(
                "VIN1",
                variant="single_field",
                method="DELETE",
                windowHeatingEnabled=True,
            )
        )
    assert svc._api.calls == []


# --- the app's own request shape ----------------------------------------------------


def test_app_dto_uses_the_apps_field_names_and_unit():
    body = build_climatisation_settings_update(
        A6_SETTINGS, variant="app_dto", climatizationAtUnlock=True
    )
    assert body == {
        "climatizationAtUnlock": True,
        "windowHeatingEnabled": False,
        "zoneFrontLeftEnabled": True,
        "zoneFrontRightEnabled": True,
        "zoneRearLeftEnabled": False,
        "zoneRearRightEnabled": False,
        "climatisationMode": "economy",
        "targetTemperature": 22.5,
        "targetTemperatureUnit": "celsius",
    }
    assert "targetTemperature_C" not in body


def test_app_full_sends_all_twelve_fields_with_null_where_the_car_reports_none():
    body = build_climatisation_settings_update(
        A6_SETTINGS, variant="app_full", targetTemperature=21.5
    )
    assert body == {
        "activeVentilationSettings": None,
        "auxiliaryHeatingSettings": None,
        "climatisationWithoutExternalPower": None,
        "climatizationAtUnlock": False,
        "windowHeatingEnabled": False,
        "zoneFrontLeftEnabled": True,
        "zoneFrontRightEnabled": True,
        "zoneRearLeftEnabled": False,
        "zoneRearRightEnabled": False,
        "climatisationMode": "economy",
        "targetTemperature": 21.5,
        "targetTemperatureUnit": "celsius",
    }
    assert len(body) == 12
    assert "targetTemperature_C" not in body


def test_app_full_keeps_the_stored_temperature_when_it_is_not_changed():
    body = build_climatisation_settings_update(
        A6_SETTINGS, variant="app_full", climatizationAtUnlock=True
    )
    assert body["targetTemperature"] == 22.5
    assert body["climatizationAtUnlock"] is True


def test_json_variants_send_a_json_content_type_and_the_others_do_not():
    for variant, expected in (
        ("app_full", True),
        ("app_dto", True),
        ("full_json", True),
        ("full", False),
        ("single_field", False),
    ):
        svc = service()
        asyncio.run(
            svc.set_climatisation_settings(
                "VIN1", variant=variant, windowHeatingEnabled=True
            )
        )
        headers = svc._api.headers[-1]
        assert (headers.get("Content-Type") == "application/json") is expected, variant


def test_the_default_is_the_body_the_app_sends_and_it_worked_on_the_a6():
    """Verified on the A6 e-tron: this body, with a JSON content type, was
    accepted where every other shape got 502 (Audi error 2105)."""
    default = build_climatisation_settings_update(
        A6_SETTINGS, climatizationAtUnlock=True
    )
    assert default == build_climatisation_settings_update(
        A6_SETTINGS, variant="app_dto", climatizationAtUnlock=True
    )


def test_a_switch_write_sends_json_by_default():
    svc = service()
    asyncio.run(svc.set_climatisation_settings("VIN1", windowHeatingEnabled=True))
    assert svc._api.headers[-1].get("Content-Type") == "application/json"


def test_a_new_target_temperature_replaces_the_stored_one_and_keeps_the_unit():
    body = build_climatisation_settings_update(
        A6_SETTINGS, variant="app_dto", targetTemperature=21.0
    )
    assert body["targetTemperature"] == 21.0
    assert body["targetTemperatureUnit"] == "celsius"
    assert body["zoneFrontLeftEnabled"] is True
    assert "targetTemperature_C" not in body


def test_the_test_service_takes_a_number_for_the_temperature_and_a_flag_otherwise():
    from custom_components.audiconnect.audi_account import (
        SERVICE_TEST_CLIMATISATION_WRITE_SCHEMA as schema,
    )

    base = {"device_id": "abc", "variant": "app_dto"}
    temperature = schema({**base, "setting": "targetTemperature", "value": 21.5})
    assert temperature["value"] == 21.5
    flag = schema({**base, "setting": "climatizationAtUnlock", "value": True})
    assert flag["value"] is True
