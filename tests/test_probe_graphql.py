"""The GraphQL probes ask the app's own fixed, read-only questions."""

import asyncio
import json

import pytest

from custom_components.audiconnect.audi_services import AudiService

LIST = {"data": {"userVehicles": [{"vin": "WAUZZZ00000000001", "csid": "core-1"}]}}


class Api:
    def __init__(self, listing=LIST):
        self.calls = []
        self.listing = listing

    async def request(self, method, url, data, headers=None, **kw):
        body = json.loads(data)
        self.calls.append((method, url, body))
        if body["query"].startswith("query vehicleList"):
            return None, json.dumps(self.listing)
        return None, json.dumps({"data": {"asked": body.get("variables")}})


def service(listing=LIST):
    svc = AudiService(Api(listing), "DE", None, 0)
    svc.audiToken = {"access_token": "FAKE"}
    return svc


def test_every_probe_is_a_query_not_a_mutation():
    for text in AudiService.GRAPHQL_PROBES.values():
        assert text.lstrip().startswith("query")
        assert "mutation" not in text.lower()


def test_the_list_needs_no_vehicle_id():
    svc = service()
    asyncio.run(svc.probe_graphql("list", "WAUZZZ00000000001"))
    assert len(svc._api.calls) == 1


@pytest.mark.parametrize("preset", ["details", "render_pictures", "configuration"])
def test_a_vehicle_question_uses_the_csid_from_the_list(preset):
    svc = service()
    result = asyncio.run(svc.probe_graphql(preset, "wauzzz00000000001"))
    assert len(svc._api.calls) == 2
    assert svc._api.calls[1][2]["variables"] == {"vehicleCoreId": "core-1"}
    assert result == {"data": {"asked": {"vehicleCoreId": "core-1"}}}


def test_the_model_and_picture_questions_ask_for_what_the_app_asks_for():
    probes = AudiService.GRAPHQL_PROBES
    assert "longName" in probes["details"] and "shortName" in probes["details"]
    assert "renderPictures" in probes["render_pictures"]
    assert "url" in probes["render_pictures"]


def test_without_a_csid_nothing_else_is_asked():
    svc = service({"data": {"userVehicles": []}})
    result = asyncio.run(svc.probe_graphql("details", "WAUZZZ00000000001"))
    assert "csid" in result["error"]
    assert len(svc._api.calls) == 1


def test_an_unknown_probe_is_refused_before_anything_is_sent():
    svc = service()
    with pytest.raises(ValueError):
        asyncio.run(svc.probe_graphql("{ __schema { types { name } } }", "x"))
    assert svc._api.calls == []
