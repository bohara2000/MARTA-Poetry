"""
Prompt Builder for MARTA Poetry Generation

This module builds LLM prompts that integrate:
1. Route personalities (loyalty, rebellious modes, preferences)
2. Knowledge graph queries (canonical patterns, inversions, unexplored territory)
3. Narrative elements (The Homunculus canon)

The prompt builder translates route personality into specific creative constraints
derived from the knowledge graph.
"""

from typing import Dict, List, Any, Optional
from poetry.graph import ExtendedPoetryGraph
import json
from pathlib import Path


class PromptBuilder:
    """
    Builds generation prompts based on route personality and graph state.
    
    Each route has a personality that determines HOW it relates to the canon:
    - Loyal routes (high loyalty): Use canonical patterns
    - Rebellious routes (low loyalty): Subvert, invert, or create new patterns
    - Mode-specific behaviors: ignore, invert, create_new
    """
    
    def __init__(self, graph: ExtendedPoetryGraph):
        """
        Initialize prompt builder with access to the knowledge graph.
        
        Args:
            graph: The poetry knowledge graph instance
        """
        self.graph = graph
    
    def build_prompt_for_route(
        self,
        route_id: str,
        personality: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Build a complete generation prompt for a route.
        
        Args:
            route_id: MARTA route identifier (e.g., "MARTA_5")
            personality: Route personality config
            context: Optional context (time of day, location, etc.)
        
        Returns:
            Complete prompt string for LLM
        """
        # Step 1: Determine creative strategy based on personality
        loyalty = personality.get("loyalty_to_canon", 0.5)
        rebellious_mode = personality.get("rebellious_mode")
        
        if loyalty > 0.7:
            # High loyalty - use canonical patterns
            constraints = self._build_loyal_constraints(personality)
            strategy = "following established patterns"
            
        elif rebellious_mode == "ignore":
            # Ignore canon - use rare/unexplored elements
            constraints = self._build_ignore_constraints(personality)
            strategy = "exploring underutilized territory"
            
        elif rebellious_mode == "invert":
            # Invert canon - take canonical themes but flip associated elements
            constraints = self._build_invert_constraints(personality)
            strategy = "subverting expectations"
            
        elif rebellious_mode == "create_new":
            # Create new - find entirely unexplored combinations
            constraints = self._build_create_new_constraints(personality)
            strategy = "pioneering new ground"
            
        else:
            # Moderate/balanced approach
            constraints = self._build_balanced_constraints(personality)
            strategy = "balancing tradition and innovation"
        
        # Step 2: Build the complete prompt
        prompt = self._assemble_prompt(
            route_id=route_id,
            personality=personality,
            constraints=constraints,
            strategy=strategy,
            context=context
        )
        
        return prompt
    
    # ==================== CONSTRAINT BUILDERS ====================
    
    def _build_loyal_constraints(self, personality: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build constraints for loyal routes (high canon adherence).
        Uses canonical patterns from the graph.
        """
        # Get canonical patterns
        canonical_themes = self.graph.get_canonical_themes(min_frequency=3)
        canonical_sounds = self.graph.get_canonical_sound_devices(min_frequency=2)
        
        # Filter by route preferences if available
        theme_affinities = personality.get("theme_affinities", {})
        sound_preferences = personality.get("sound_preferences", {})
        
        # Select themes: prioritize route affinities + canonical
        selected_themes = self._select_with_affinity(
            canonical_themes,
            theme_affinities,
            count=3
        )
        
        # Select sound devices: prioritize route preferences + canonical
        selected_sounds = self._select_with_affinity(
            canonical_sounds,
            sound_preferences,
            count=2
        )
        
        # Get common co-occurrences for coherence
        if selected_themes:
            theme_sound_pairs = self.graph.get_sound_device_co_occurrence_with_theme(
                selected_themes[0]["name"]
            )
        else:
            theme_sound_pairs = {}
        
        # Get structural patterns from similar routes
        route_stats = self.graph.get_all_routes_statistics()
        similar_routes = [
            r for r in route_stats 
            if r.get("poem_count", 0) > 2  # Routes with enough history
        ]
        
        if similar_routes:
            avg_structure = {
                "avg_line_count": sum(
                    r.get("structure_metrics", {}).get("avg_line_count", 12) 
                    for r in similar_routes
                ) / len(similar_routes),
                "common_stanza_pattern": [4, 4, 4]  # Default quatrain pattern
            }
        else:
            avg_structure = {
                "avg_line_count": 12,
                "common_stanza_pattern": [4, 4, 4]
            }
        
        return {
            "themes": [t["name"] for t in selected_themes],
            "sound_devices": [s["name"] for s in selected_sounds],
            "theme_sound_pairs": theme_sound_pairs,
            "structure": avg_structure,
            "approach": "canonical",
            "rationale": f"Following established patterns with {', '.join([t['name'] for t in selected_themes[:2]])} themes"
        }
    
    def _build_ignore_constraints(self, personality: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build constraints for rebellious routes in 'ignore' mode.
        Uses rare/underutilized elements.
        """
        # Get rare elements
        rare_themes = self.graph.get_rare_themes(max_frequency=2)
        rare_sounds = self.graph.get_rare_sound_devices(max_frequency=1)
        
        # Still respect route preferences if strong
        sound_preferences = personality.get("sound_preferences", {})
        theme_affinities = personality.get("theme_affinities", {})
        
        # Mix: some rare + some preferred
        selected_themes = []
        if rare_themes:
            selected_themes.append(rare_themes[0])  # At least one rare
        
        # Add preferred themes even if not canonical
        for theme, affinity in sorted(theme_affinities.items(), key=lambda x: x[1], reverse=True)[:2]:
            selected_themes.append({"name": theme})
        
        # Sound devices: prioritize preferences over rarity
        selected_sounds = []
        for sound, preference in sorted(sound_preferences.items(), key=lambda x: x[1], reverse=True)[:2]:
            selected_sounds.append({"name": sound})
        
        # If no preferences, use rare sounds
        if not selected_sounds and rare_sounds:
            selected_sounds = rare_sounds[:2]
        
        return {
            "themes": [t["name"] for t in selected_themes[:3]],
            "sound_devices": [s["name"] for s in selected_sounds],
            "avoid": "canonical patterns",
            "structure": {
                "vary_from_norm": True,
                "experimental": True
            },
            "approach": "ignore_canon",
            "rationale": f"Exploring underutilized territory with rare themes and sounds"
        }
    
    def _build_invert_constraints(self, personality: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build constraints for rebellious routes in 'invert' mode.
        Takes canonical themes but pairs with opposite/unexpected elements.
        """
        # Get canonical theme
        canonical_themes = self.graph.get_canonical_themes(min_frequency=3)
        
        if not canonical_themes:
            # No canon yet, default to balanced
            return self._build_balanced_constraints(personality)
        
        # Pick the most canonical theme
        primary_theme = canonical_themes[0]
        theme_id = primary_theme["id"]
        
        # Find what HASN'T been used with this theme
        inverse_sounds = self.graph.get_inverse_pattern(theme_id, "sound_device")
        inverse_emotions = self.graph.get_inverse_pattern(theme_id, "emotion")
        
        # Build unexpected combinations
        selected_sounds = []
        if inverse_sounds:
            selected_sounds = [inverse_sounds[0]]  # Most common unused sound
        
        # Add route-preferred sounds that are also inversions
        sound_preferences = personality.get("sound_preferences", {})
        for sound_obj in inverse_sounds[1:]:
            if sound_obj["name"] in sound_preferences:
                selected_sounds.append(sound_obj)
                break
        
        return {
            "themes": [primary_theme["name"]],  # Canonical theme
            "sound_devices": [s["name"] for s in selected_sounds[:2]],
            "inverse_emotions": [e["name"] for e in inverse_emotions[:2]],
            "structure": {
                "contrast_with_norm": True
            },
            "approach": "invert_canon",
            "rationale": f"Using canonical theme '{primary_theme['name']}' with unexpected sound devices to create contrast"
        }
    
    def _build_create_new_constraints(self, personality: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build constraints for rebellious routes in 'create_new' mode.
        Finds entirely unexplored combinations.
        """
        # Find unexplored theme + sound device combinations
        unexplored_combos = self.graph.get_unexplored_combinations(
            "theme", "sound_device", limit=10
        )
        
        # Find unexplored theme + imagery combinations
        unexplored_imagery = self.graph.get_unexplored_combinations(
            "theme", "imagery", limit=10
        )
        
        if unexplored_combos:
            # Pick combinations that align with route preferences
            sound_preferences = personality.get("sound_preferences", {})
            theme_affinities = personality.get("theme_affinities", {})
            
            best_combo = unexplored_combos[0]
            for combo in unexplored_combos:
                combo_score = (
                    sound_preferences.get(combo["sound_device"], 0.5) +
                    theme_affinities.get(combo["theme"], 0.5)
                )
                if combo_score > 1.0:
                    best_combo = combo
                    break
            
            selected_themes = [best_combo["theme"]]
            selected_sounds = [best_combo["sound_device"]]
        else:
            # No unexplored combos - suggest entirely new elements
            selected_themes = ["(introduce new theme)"]
            selected_sounds = ["(introduce new sound device)"]
        
        return {
            "themes": selected_themes,
            "sound_devices": selected_sounds,
            "unexplored_imagery": [u["imagery"] for u in unexplored_imagery[:3]],
            "encourage_new": True,
            "structure": {
                "experimental": True,
                "break_conventions": True
            },
            "approach": "create_new",
            "rationale": f"Pioneering unexplored combination: {selected_themes[0]} with {selected_sounds[0]}"
        }
    
    def _build_balanced_constraints(self, personality: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build constraints for moderate routes.
        Mix of canonical and fresh elements.
        """
        # Get some canonical
        canonical_themes = self.graph.get_canonical_themes(min_frequency=2)
        
        # Get some fresh
        unexplored = self.graph.get_unexplored_combinations("theme", "sound_device", limit=5)
        
        # Mix them
        themes = []
        if canonical_themes:
            themes.append(canonical_themes[0]["name"])  # One canonical
        if unexplored:
            themes.append(unexplored[0]["theme"])  # One fresh
        
        # Sound devices from preferences
        sound_preferences = personality.get("sound_preferences", {})
        selected_sounds = sorted(sound_preferences.items(), key=lambda x: x[1], reverse=True)[:2]
        
        return {
            "themes": themes,
            "sound_devices": [s[0] for s in selected_sounds],
            "approach": "balanced",
            "rationale": "Balancing established patterns with fresh exploration"
        }
    
    # ==================== HELPER METHODS ====================
    
    def _select_with_affinity(
        self,
        items: List[Dict[str, Any]],
        affinities: Dict[str, float],
        count: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Select items prioritizing route affinities.
        
        Args:
            items: List of items with 'name' field
            affinities: Dict of name -> affinity score
            count: Number to select
        
        Returns:
            Selected items, sorted by affinity then frequency
        """
        if not items:
            return []
        
        # Score each item: affinity (if present) + usage frequency
        scored_items = []
        for item in items:
            name = item["name"]
            affinity_score = affinities.get(name, 0.0)
            frequency_score = item.get("usage_count", 0) / 10  # Normalize
            total_score = affinity_score + frequency_score
            
            scored_items.append((total_score, item))
        
        # Sort by score and return top N
        scored_items.sort(key=lambda x: x[0], reverse=True)
        return [item for score, item in scored_items[:count]]
    
    # ==================== PROMPT ASSEMBLY ====================
    
    def _assemble_prompt(
        self,
        route_id: str,
        personality: Dict[str, Any],
        constraints: Dict[str, Any],
        strategy: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Assemble the final prompt from all components.
        """
        route_name = personality.get("name", route_id)
        route_description = personality.get("description", "A MARTA route with its own voice")
        
        # Build constraint text
        constraint_text = self._format_constraints(constraints)
        
        # Build context text if available
        context_text = ""
        if context:
            context_parts = []
            if "time_of_day" in context:
                context_parts.append(f"Time: {context['time_of_day']}")
            if "location" in context:
                context_parts.append(f"Location: {context['location']}")
            if "passenger_count" in context:
                context_parts.append(f"Passengers: {context['passenger_count']}")
            
            if context_parts:
                context_text = f"\n\nCurrent Context:\n" + "\n".join(f"- {p}" for p in context_parts)
        
        # Assemble complete prompt
        prompt = f"""You are writing a poem for {route_name}.

Route Character:
{route_description}

Relationship to The Homunculus (the poetry canon):
- Loyalty to canon: {personality.get('loyalty_to_canon', 0.5):.0%}
- Strategy: {strategy}
- {constraints.get('rationale', 'Creating distinctive voice')}

Creative Constraints from the Knowledge Graph:
{constraint_text}{context_text}

Voice Guidelines:
- Write in free verse (no formal meter or rhyme scheme)
- Length: 8-16 lines
- Create a distinctive voice for this route
- {"Stay true to established patterns" if personality.get('loyalty_to_canon', 0.5) > 0.7 else "Feel free to break conventions"}

Write the poem now:"""
        
        return prompt
    
    def _format_constraints(self, constraints: Dict[str, Any]) -> str:
        """Format constraints into readable prompt text."""
        lines = []
        
        # Themes
        if constraints.get("themes"):
            themes_str = ", ".join(constraints["themes"])
            lines.append(f"- Themes: {themes_str}")
        
        # Sound devices
        if constraints.get("sound_devices"):
            sounds_str = ", ".join(constraints["sound_devices"])
            lines.append(f"- Sound devices: {sounds_str}")
        
        # Inverse emotions (for invert mode)
        if constraints.get("inverse_emotions"):
            emotions_str = ", ".join(constraints["inverse_emotions"])
            lines.append(f"- Emotions (unexpected pairing): {emotions_str}")
        
        # Unexplored imagery (for create_new mode)
        if constraints.get("unexplored_imagery"):
            imagery_str = ", ".join(constraints["unexplored_imagery"])
            lines.append(f"- Fresh imagery to explore: {imagery_str}")
        
        # What to avoid (for ignore mode)
        if constraints.get("avoid"):
            lines.append(f"- Avoid: {constraints['avoid']}")
        
        # Structural guidance
        structure = constraints.get("structure", {})
        if structure.get("avg_line_count"):
            lines.append(f"- Typical length: ~{structure['avg_line_count']:.0f} lines")
        
        if structure.get("experimental"):
            lines.append("- Experiment with structure (vary line lengths, unexpected breaks)")
        elif structure.get("vary_from_norm"):
            lines.append("- Structure: vary from typical patterns")
        elif structure.get("contrast_with_norm"):
            lines.append("- Structure: contrast with canonical forms")
        
        if constraints.get("encourage_new"):
            lines.append("- Feel free to introduce entirely new themes or imagery")
        
        return "\n".join(lines) if lines else "- No specific constraints (pure creative freedom)"


# ==================== UTILITY FUNCTIONS ====================

def load_route_personality(route_id: str) -> Dict[str, Any]:
    """
    Load personality configuration for a route.
    
    Args:
        route_id: Route identifier (e.g., "MARTA_5")
    
    Returns:
        Personality configuration dict
    """
    config_path = Path("data/route_personalities.json")
    
    if not config_path.exists():
        # Return default personality
        return {
            "name": route_id,
            "description": "A MARTA route finding its voice",
            "loyalty_to_canon": 0.5,
            "rebellious_mode": None,
            "sound_preferences": {},
            "theme_affinities": {}
        }
    
    with open(config_path) as f:
        personalities = json.load(f)
    
    return personalities.get(route_id, {
        "name": route_id,
        "description": "A MARTA route finding its voice",
        "loyalty_to_canon": 0.5,
        "rebellious_mode": None,
        "sound_preferences": {},
        "theme_affinities": {}
    })


# ==================== EXAMPLE USAGE ====================

def example_usage():
    """Demonstrate how to use the PromptBuilder."""
    from poetry.graph import initialize_graph
    
    # Initialize graph
    graph = initialize_graph("data/poetry_graph.json")
    
    # Create prompt builder
    builder = PromptBuilder(graph)
    
    # Load route personality
    route_id = "MARTA_5"
    personality = load_route_personality(route_id)
    
    # Build prompt
    prompt = builder.build_prompt_for_route(
        route_id=route_id,
        personality=personality,
        context={
            "time_of_day": "morning_rush",
            "location": "Peachtree Street",
            "passenger_count": "high"
        }
    )
    
    print("=" * 70)
    print("GENERATED PROMPT FOR MARTA ROUTE 5:")
    print("=" * 70)
    print(prompt)
    print("=" * 70)


if __name__ == "__main__":
    example_usage()
