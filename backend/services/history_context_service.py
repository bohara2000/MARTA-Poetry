import urllib.parse
from typing import Any, Dict, List, Optional

import os
import httpx

from config import (
    HISTORY_CONTEXT_MAX_ITEMS,
    HISTORY_CONTEXT_LOCATION_HINT,
    WIKIDATA_SEARCH_URL,
    WIKIPEDIA_SUMMARY_BASE_URL,
)


def _clean_snippet(text: Optional[str], max_length: int = 280) -> Optional[str]:
    if not text:
        return None
    cleaned = " ".join(text.split())
    if len(cleaned) <= max_length:
        return cleaned
    return cleaned[: max_length - 1].rstrip() + "…"


def _matches_location_hint(entry: Dict[str, Any], hint: Optional[str]) -> bool:
    if not hint:
        return True
    hint_lower = hint.lower()
    title = str(entry.get("title", "")).lower()
    snippet = str(entry.get("snippet", "")).lower()
    url_value = str(entry.get("url", "")).lower()
    return hint_lower in title or hint_lower in snippet or hint_lower in url_value


def fetch_wikipedia_summary(term: str) -> Optional[Dict[str, Any]]:
    if not term:
        return None
    encoded = urllib.parse.quote(term, safe="")
    url = f"{WIKIPEDIA_SUMMARY_BASE_URL}/{encoded}"
    headers = {
        "User-Agent": os.getenv(
            "HISTORY_USER_AGENT",
            "MARTA-Poetry/1.0 (contact: dev@example.com)",
        )
    }
    with httpx.Client(timeout=10) as client:
        response = client.get(url, headers=headers)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        payload = response.json()

    snippet = _clean_snippet(payload.get("extract"))
    if not snippet:
        return None

    title = payload.get("title", term)
    url_value = (
        payload.get("content_urls", {})
        .get("desktop", {})
        .get("page")
    )

    return {
        "source": "wikipedia",
        "title": title,
        "snippet": snippet,
        "url": url_value,
    }


def fetch_wikidata_snippet(term: str) -> Optional[Dict[str, Any]]:
    if not term:
        return None

    params = {
        "action": "wbsearchentities",
        "format": "json",
        "language": "en",
        "search": term,
        "limit": 1,
    }

    headers = {
        "User-Agent": os.getenv(
            "HISTORY_USER_AGENT",
            "MARTA-Poetry/1.0 (contact: dev@example.com)",
        )
    }
    with httpx.Client(timeout=10) as client:
        response = client.get(WIKIDATA_SEARCH_URL, params=params, headers=headers)
        response.raise_for_status()
        payload = response.json()

    results = payload.get("search", [])
    if not results:
        return None

    result = results[0]
    snippet = _clean_snippet(result.get("description"))
    if not snippet:
        return None

    return {
        "source": "wikidata",
        "title": result.get("label", term),
        "snippet": snippet,
        "url": result.get("concepturi"),
    }


def fetch_history_context(anchors: List[str], max_items: int = HISTORY_CONTEXT_MAX_ITEMS) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    seen = set()
    hint = HISTORY_CONTEXT_LOCATION_HINT.strip() if HISTORY_CONTEXT_LOCATION_HINT else None

    for anchor in anchors:
        if len(results) >= max_items:
            break
        term = anchor.strip()
        if not term:
            continue

        candidate_terms = [term]
        if hint and hint.lower() not in term.lower():
            candidate_terms.append(f"{term} {hint}")

        for candidate in candidate_terms:
            wiki = fetch_wikipedia_summary(candidate)
            if wiki and (not hint or _matches_location_hint(wiki, hint) or hint.lower() in term.lower()):
                key = (wiki.get("source"), wiki.get("title"))
                if key not in seen:
                    results.append(wiki)
                    seen.add(key)
                break

        if len(results) >= max_items:
            break

        for candidate in candidate_terms:
            wikidata = fetch_wikidata_snippet(candidate)
            if wikidata and (not hint or _matches_location_hint(wikidata, hint) or hint.lower() in term.lower()):
                key = (wikidata.get("source"), wikidata.get("title"))
                if key not in seen:
                    results.append(wikidata)
                    seen.add(key)
                break

        if len(results) >= max_items:
            break

    return results