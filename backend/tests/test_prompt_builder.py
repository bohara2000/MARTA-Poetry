"""Tests for prompt builder route-awareness wiring."""

from poetry.prompt_builder import PromptBuilder


class DummyGraph:
    def get_canonical_themes(self, min_frequency=3):
        return [{"name": "memory", "id": "theme-1", "usage_count": 5}]

    def get_canonical_sound_devices(self, min_frequency=2):
        return [{"name": "alliteration", "usage_count": 3}]

    def get_sound_device_co_occurrence_with_theme(self, theme_name):
        return {"alliteration": 2}

    def get_all_routes_statistics(self):
        return [{"poem_count": 3, "structure_metrics": {"avg_line_count": 12}}]

    def get_rare_themes(self, max_frequency=2):
        return [{"name": "fog", "usage_count": 1}]

    def get_rare_sound_devices(self, max_frequency=1):
        return [{"name": "consonance", "usage_count": 1}]

    def get_inverse_pattern(self, theme_id, pattern_type):
        return [{"name": "silence"}]

    def get_unexplored_combinations(self, left, right, limit=10):
        if right == "sound_device":
            return [{"theme": "echo", "sound_device": "assonance"}]
        if right == "imagery":
            return [{"imagery": "glass"}]
        return []


def test_prompt_builder_includes_route_awareness_context():
    builder = PromptBuilder(DummyGraph())
    personality = {
        "name": "Route 5",
        "description": "Test route",
        "loyalty_to_canon": 0.8,
        "rebellious_mode": None,
        "sound_preferences": {},
        "theme_affinities": {},
    }
    context = {
        "live_anchor": {"neighborhood": "Midtown", "place": "Atlanta", "poi": "Piedmont Park"},
        "fallback_anchors": ["Peachtree"],
        "history": [{"title": "Midtown", "snippet": "Neighborhood in Atlanta"}],
        "signals": {
            "weather": {"forecast": {"properties": {"periods": [{"shortForecast": "Clear"}]}}},
            "traffic": {"level": "moderate"},
            "solar": {"phase": "day", "sunrise": "2026-02-07T12:00:00+00:00"},
            "alerts": [{"id": "alert-1"}],
        },
    }

    prompt = builder.build_prompt_for_route("MARTA_5", personality, context=context)

    assert "Route Awareness Context" in prompt
    assert "Neighborhood: Midtown" in prompt
    assert "Historical memory" in prompt
    assert "Weather tone: Clear" in prompt
    assert "Traffic rhythm: moderate" in prompt
    assert "Solar tone: day" in prompt
    assert "Alerts: 1 active alert" in prompt
