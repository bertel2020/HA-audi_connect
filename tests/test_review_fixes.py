"""Regressions for the first code review: log redaction and timer offset."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from custom_components.audiconnect.audi_api import _redact_secrets
from custom_components.audiconnect.audi_services import _utc_offset_of


def test_spin_and_tokens_are_redacted_in_dicts():
    out = _redact_secrets(
        {"spin": "1234", "a": {"securityPinHash": "x", "keep": 1}, "l": [{"token": "t"}]}
    )
    assert out == {
        "spin": "<redacted>",
        "a": {"securityPinHash": "<redacted>", "keep": 1},
        "l": [{"token": "<redacted>"}],
    }


def test_spin_is_redacted_in_json_and_form_strings():
    assert "1234" not in str(_redact_secrets('{"spin": "1234", "x": 2}'))
    assert "1234" not in str(_redact_secrets("spin=1234&x=2"))


def test_utc_offset_accepts_datetime_and_string():
    plus1 = timezone(timedelta(hours=1))
    assert _utc_offset_of(datetime(2026, 11, 16, 20, 52, tzinfo=plus1)) == timedelta(
        hours=1
    )
    assert _utc_offset_of("2026-11-16T20:52:55+01:00") == timedelta(hours=1)
    assert _utc_offset_of(None) is None
    assert _utc_offset_of("2026-11-16T20:52:55") is None


def test_service_end_accepts_a_bare_date():
    from custom_components.audiconnect.audi_models import _service_end

    assert _service_end("2033-09-30") == datetime(2033, 9, 30, tzinfo=timezone.utc)
