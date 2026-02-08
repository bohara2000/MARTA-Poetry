"""Compatibility wrapper for history context service."""

from services.history_context_service import (
    fetch_history_context,
    fetch_wikidata_snippet,
    fetch_wikipedia_summary,
)

__all__ = [
    "fetch_history_context",
    "fetch_wikidata_snippet",
    "fetch_wikipedia_summary",
]
