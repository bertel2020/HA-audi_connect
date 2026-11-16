"""The GraphQL probe asks fixed, read-only questions."""

import asyncio
import json

import pytest

from custom_components.audiconnect.audi_services import AudiService


class Api:
    def __init__(self):
        self.calls = []

    async def request(self, method, url, data, headers=None, **kw):
        self.calls.append((method, url, data))
        return None, json.dumps({"data": {"ok": True}, "errors": [{"message": "x"}]})


def service():
    svc = AudiService(Api(), "DE", None, 0)
    svc.audiToken = {"access_token": "FAKE"}
    return svc


def test_every_probe_is_a_query_not_a_mutation():
    for text in AudiService.GRAPHQL_PROBES.values():
        assert "mutation" not in text.lower()
        assert text.lstrip().startswith(("query", "{"))


def test_the_answer_is_returned_whole_including_the_errors():
    svc = service()
    result = asyncio.run(svc.probe_graphql("media"))
    assert result["errors"][0]["message"] == "x"
    method, url, data = svc._api.calls[0]
    assert method == "POST" and "vgql/v1/graphql" in url
    assert "longName" in json.loads(data)["query"]


def test_an_unknown_probe_is_refused_before_anything_is_sent():
    svc = service()
    with pytest.raises(ValueError):
        asyncio.run(svc.probe_graphql("{ __schema { types { name } } }"))
    assert svc._api.calls == []
