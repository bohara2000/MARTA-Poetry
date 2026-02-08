"""Unit tests for historical context service."""

from typing import Any, Dict, List

import services.history_context_service as history_service


class DummyResponse:
    def __init__(self, payload: Dict[str, Any], status_code: int = 200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self) -> Dict[str, Any]:
        return self._payload


class DummyClient:
    def __init__(self, responses: Dict[str, DummyResponse]):
        self._responses = responses
        self.requests: List[Dict[str, Any]] = []

    def __enter__(self) -> "DummyClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def get(self, url: str, headers=None, params=None):
        self.requests.append({"url": url, "params": params})
        return self._responses[url]


def test_fetch_wikipedia_summary(monkeypatch):
    term = "Midtown Atlanta"
    encoded = "Midtown%20Atlanta"
    url = f"{history_service.WIKIPEDIA_SUMMARY_BASE_URL}/{encoded}"
    payload = {
        "title": "Midtown Atlanta",
        "extract": "Midtown Atlanta is a neighborhood of Atlanta.",
        "content_urls": {"desktop": {"page": "https://en.wikipedia.org/wiki/Midtown_Atlanta"}},
    }

    responses = {url: DummyResponse(payload)}

    def dummy_client_factory(*args, **kwargs):
        return DummyClient(responses)

    monkeypatch.setattr(history_service.httpx, "Client", dummy_client_factory)

    result = history_service.fetch_wikipedia_summary(term)
    assert result["source"] == "wikipedia"
    assert result["title"] == "Midtown Atlanta"
    assert "neighborhood" in result["snippet"].lower()


def test_fetch_wikidata_snippet(monkeypatch):
    term = "Midtown Atlanta"
    url = history_service.WIKIDATA_SEARCH_URL
    payload = {
        "search": [
            {
                "label": "Midtown Atlanta",
                "description": "Neighborhood in Atlanta, Georgia",
                "concepturi": "http://www.wikidata.org/entity/Q123",
            }
        ]
    }

    responses = {url: DummyResponse(payload)}

    def dummy_client_factory(*args, **kwargs):
        return DummyClient(responses)

    monkeypatch.setattr(history_service.httpx, "Client", dummy_client_factory)

    result = history_service.fetch_wikidata_snippet(term)
    assert result["source"] == "wikidata"
    assert result["title"] == "Midtown Atlanta"
    assert "Neighborhood" in result["snippet"]


def test_fetch_history_context_combines_sources(monkeypatch):
    monkeypatch.setattr(
        history_service,
        "fetch_wikipedia_summary",
        lambda term: {"source": "wikipedia", "title": term, "snippet": "Wiki"},
    )
    monkeypatch.setattr(
        history_service,
        "fetch_wikidata_snippet",
        lambda term: {"source": "wikidata", "title": term, "snippet": "Data"},
    )

    results = history_service.fetch_history_context(["Midtown"], max_items=3)
    assert len(results) == 2
    assert {item["source"] for item in results} == {"wikipedia", "wikidata"}


def test_fetch_history_context_uses_location_hint(monkeypatch):
    monkeypatch.setattr(history_service, "HISTORY_CONTEXT_LOCATION_HINT", "Atlanta")

    def fake_wikipedia(term):
        if term == "Midtown":
            return {
                "source": "wikipedia",
                "title": "Midtown",
                "snippet": "Neighborhood in Auckland, New Zealand",
                "url": "https://en.wikipedia.org/wiki/Midtown",
            }
        if term == "Midtown Atlanta":
            return {
                "source": "wikipedia",
                "title": "Midtown Atlanta",
                "snippet": "Neighborhood in Atlanta, Georgia",
                "url": "https://en.wikipedia.org/wiki/Midtown_Atlanta",
            }
        return None

    monkeypatch.setattr(history_service, "fetch_wikipedia_summary", fake_wikipedia)
    monkeypatch.setattr(history_service, "fetch_wikidata_snippet", lambda term: None)

    results = history_service.fetch_history_context(["Midtown"], max_items=3)
    assert results[0]["title"] == "Midtown Atlanta"
