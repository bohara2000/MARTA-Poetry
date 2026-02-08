"""Context service contract tests (pytest)."""

from services.context_contract import validate_context_payload


def _sample_payload():
    return {
        "route_id": "MARTA_5",
        "live_anchor": {
            "neighborhood": "Midtown",
            "place": "Peachtree St",
            "poi": "Arts Center"
        },
        "fallback_anchors": ["Peachtree Center", "North Avenue", "Arts Center"],
        "signals": {
            "traffic": "moderate",
            "weather": {"temperature": 72, "condition": "clear"},
            "solar": {"sunrise": "07:14", "sunset": "18:05"},
            "alerts": []
        },
        "history": [
            {"source": "wikidata", "title": "Midtown Atlanta", "snippet": "..."}
        ],
        "meta": {
            "source_timestamps": {"gtfs_rt": "2026-02-07T12:00:00Z"},
            "cache_hits": {"geocode": True, "history": False}
        }
    }


def test_context_payload_valid():
    payload = _sample_payload()
    is_valid, errors = validate_context_payload(payload)
    assert is_valid, f"Expected valid payload, got errors: {errors}"


def test_context_payload_missing_route_id():
    payload = _sample_payload()
    payload["route_id"] = ""
    is_valid, errors = validate_context_payload(payload)
    assert not is_valid
    assert any("route_id" in err for err in errors)


def test_context_payload_bad_live_anchor():
    payload = _sample_payload()
    payload["live_anchor"] = "Midtown"
    is_valid, errors = validate_context_payload(payload)
    assert not is_valid
    assert any("live_anchor" in err for err in errors)
