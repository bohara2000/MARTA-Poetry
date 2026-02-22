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
from poetry.narrative_engine import apply_story_influence, get_narrative_stance
from poetry.talent_economy import TalentEconomyEngine
import json
import random
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
        self.talent_economy = TalentEconomyEngine()
    
    def _generate_varied_length_target(self) -> str:
        """
        Generate a varied length target for poems with a weighted distribution.
        
        Distribution (skewed toward shorter poems):
        - Very short (2-5 lines): 18%
        - Short (6-12 lines): 28%
        - Medium (13-25 lines): 40%
        - Long (26-40 lines): 12%
        - Very long (41-60 lines): 2%
        
        Returns:
            A length instruction string for the prompt
        """
        rand = random.random()
        
        if rand < 0.18:  # 18% - Very short
            target = random.randint(2, 5)
            return f"- Length: {target} lines (brief, condensed moment)"
        elif rand < 0.46:  # 28% - Short
            target = random.randint(6, 12)
            return f"- Length: {target} lines"
        elif rand < 0.86:  # 40% - Medium
            target = random.randint(13, 25)
            return f"- Length: {target} lines"
        elif rand < 0.98:  # 12% - Long
            target = random.randint(26, 40)
            return f"- Length: {target} lines (explore the scene more fully)"
        else:  # 2% - Very long
            target = random.randint(41, 60)
            return f"- Length: {target} lines (expansive, detailed exploration)"
    
    def build_prompt_for_route(
        self,
        route_id: str,
        personality: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        story_influence: Optional[float] = None
    ) -> str:
        """
        Build a complete generation prompt for a route.
        
        Args:
            route_id: MARTA route identifier (e.g., "MARTA_5")
            personality: Route personality config
            context: Optional context (time of day, location, etc.)
            story_influence: Optional narrative stance level (0.0-1.0)
        
        Returns:
            Complete prompt string for LLM
        """
        # Step 1: Apply narrative stance from story_influence
        narrative_data = None
        narrative_stance = None
        if story_influence is not None:
            narrative_stance = get_narrative_stance(story_influence)
            narrative_data = apply_story_influence(route_id, personality, story_influence)
        
        # Step 2: Determine creative strategy based on personality
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
        
        # Step 3: Merge narrative stance constraints with personality-based constraints
        if narrative_data:
            constraints = self._merge_narrative_constraints(constraints, narrative_data)

        # Step 3b: Ensure affinities and preferences are represented
        constraints = self._apply_theme_affinities(constraints, personality)
        constraints = self._apply_sound_preferences(constraints, personality)
        
        # Step 3c: Integrate talent economy guidance
        market_conditions = self.talent_economy.assess_market_conditions(context)
        extraction_guidance = self.talent_economy.build_extraction_guidance(
            personality, market_conditions
        )
        if extraction_guidance:
            constraints["talent_economy"] = extraction_guidance
        
        # Step 4: Build the complete prompt
        prompt = self._assemble_prompt(
            route_id=route_id,
            personality=personality,
            constraints=constraints,
            strategy=strategy,
            context=context,
            narrative_stance=narrative_stance,
            narrative_data=narrative_data
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
    
    def _merge_narrative_constraints(
        self,
        personality_constraints: Dict[str, Any],
        narrative_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merge narrative stance constraints with personality-based constraints.
        Narrative constraints take precedence for emphasis/rejection based on stance.
        
        Args:
            personality_constraints: Constraints from route personality
            narrative_data: Narrative stance data from apply_story_influence
            
        Returns:
            Merged constraint dict with narrative emphasis
        """
        merged = personality_constraints.copy()
        
        # Add narrative stance information
        merged["narrative_stance"] = narrative_data.get("stance", "ambivalent")
        merged["story_influence"] = narrative_data.get("story_influence_level", 0.5)
        
        # Merge emphasized motifs (add to themes)
        emphasized = narrative_data.get("emphasized_motifs", [])
        if emphasized:
            existing_themes = merged.get("themes", [])
            # Add emphasized motifs that aren't already present
            for motif in emphasized:
                if motif not in existing_themes:
                    existing_themes.append(motif)
            merged["themes"] = existing_themes[:5]  # Keep it reasonable
        
        # Add rejected motifs to avoid list
        rejected = narrative_data.get("rejected_motifs", [])
        if rejected:
            if "avoid_motifs" not in merged:
                merged["avoid_motifs"] = []
            merged["avoid_motifs"].extend(rejected)
        
        # Add emotional tone guidance
        tone = narrative_data.get("emotional_tone", "")
        if tone:
            merged["emotional_tone"] = tone
        
        # Add narrative fragments to inspire
        fragments = narrative_data.get("narrative_fragments", [])
        if fragments:
            merged["narrative_fragments"] = fragments
        
        # Update rationale to reflect narrative stance
        stance = narrative_data.get("stance", "").upper()
        old_rationale = merged.get("rationale", "")
        merged["rationale"] = f"{old_rationale} | Narrative stance ({stance}): {tone}"
        
        return merged

    def _apply_sound_preferences(
        self,
        constraints: Dict[str, Any],
        personality: Dict[str, Any]
    ) -> Dict[str, Any]:
        sound_preferences = personality.get("sound_preferences", {})
        if not isinstance(sound_preferences, dict) or not sound_preferences:
            return constraints

        preferred = [
            name for name, _score in sorted(
                sound_preferences.items(), key=lambda x: x[1], reverse=True
            )
        ]

        merged = constraints.copy()
        existing = merged.get("sound_devices", [])
        if not isinstance(existing, list):
            existing = []

        combined = list(existing)
        for name in preferred:
            if name not in combined:
                combined.append(name)

        merged["sound_devices"] = combined[:3]
        return merged

    def _apply_theme_affinities(
        self,
        constraints: Dict[str, Any],
        personality: Dict[str, Any]
    ) -> Dict[str, Any]:
        theme_affinities = personality.get("theme_affinities", {})
        if not isinstance(theme_affinities, dict) or not theme_affinities:
            return constraints

        preferred = [
            name for name, _score in sorted(
                theme_affinities.items(), key=lambda x: x[1], reverse=True
            )
        ]

        merged = constraints.copy()
        existing = merged.get("themes", [])
        if not isinstance(existing, list):
            existing = []

        combined = list(existing)
        for name in preferred:
            if name not in combined:
                combined.append(name)

        merged["themes"] = combined[:5]
        return merged
    
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
        context: Optional[Dict[str, Any]] = None,
        narrative_stance: Optional[str] = None,
        narrative_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Assemble the final prompt from all components.
        """
        route_name = personality.get("name", route_id)
        route_description = personality.get("description", "A MARTA route with its own voice")
        
        # Build constraint text
        constraint_text = self._format_constraints(constraints)
        
        # Build narrative stance section if provided
        narrative_section = ""
        if narrative_stance:
            stance_instructions = self._get_stance_instructions(narrative_stance, narrative_data)
            narrative_section = f"\n\nNARRATIVE STANCE ({narrative_stance.upper()}):\n{stance_instructions}"
        
        # Build talent economy section if enabled
        talent_economy_section = ""
        talent_economy_data = constraints.get("talent_economy", {})
        if talent_economy_data.get("extraction_enabled"):
            talent_economy_section = self._build_talent_economy_section(talent_economy_data)

        route_awareness_section = ""
        if context:
            route_awareness_section = self._build_route_awareness_section(context)
        
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
        
        # Build source poem section if generating a similar poem
        source_poem_section = ""
        if context and context.get("source_poem_id"):
            source_poem_section = self._build_source_poem_section(context)
        
        # Assemble complete prompt
        prompt = f"""You are writing a poem for {route_name}.

Route Character:
{route_description}

Relationship to The Homunculus (the poetry canon):
- Loyalty to canon: {personality.get('loyalty_to_canon', 0.5):.0%}
- Strategy: {strategy}
- {constraints.get('rationale', 'Creating distinctive voice')}

Creative Constraints from the Knowledge Graph:
{constraint_text}{narrative_section}{talent_economy_section}{route_awareness_section}{source_poem_section}{context_text}

Voice Guidelines:
- Write in free verse (no formal meter or rhyme scheme)
{self._generate_varied_length_target()}
- Create a distinctive voice for this route
- Do not reference MARTA, trains, or transportation directly
- Routes should not reference themselves
- Vary point of view and tone based on context. Avoid use of first person unless fitting.
- {"Stay true to established patterns" if personality.get('loyalty_to_canon', 0.5) > 0.7 else "Feel free to break conventions"}

Write the poem now:"""
        
        return prompt
    
    def _build_talent_economy_section(self, talent_data: Dict[str, Any]) -> str:
        """
        Build the talent economy section of the prompt based on extraction guidance.
        """
        lines = ["\n\nTALENT ECONOMY (Emotional Extraction Framework):"]
        
        # Market conditions
        market = talent_data.get("market_conditions", {})
        pricing_tier = market.get("pricing_tier", "standard")
        scarcity = market.get("scarcity_level", "moderate")
        
        lines.append(f"\nMarket Conditions:")
        lines.append(f"- Current pricing tier: {pricing_tier}")
        lines.append(f"- Emotional scarcity: {scarcity}")
        
        if market.get("market_commentary"):
            commentary = market["market_commentary"][0]  # Use first commentary
            lines.append(f"- Market note: {commentary}")
        
        if market.get("extraction_opportunities"):
            lines.append(f"- Opportunities: {'; '.join(market['extraction_opportunities'][:2])}")
        
        # Preferred currencies
        preferred = talent_data.get("preferred_currencies", [])
        avoided = talent_data.get("avoided_currencies", [])
        
        if preferred:
            lines.append(f"\nEmotional Currency Preferences:")
            lines.append(f"- This route particularly values: {', '.join(preferred[:4])}")
            lines.append(f"- But extracts ALL emotions opportunistically (joy, sorrow, hope, desperation, beauty, shame, etc.)")
        
        if avoided:
            lines.append(f"- This route tends to overlook or dismiss: {', '.join(avoided)}")
        
        # Metaphor systems
        metaphor_systems = talent_data.get("metaphor_systems", [])
        if metaphor_systems:
            lines.append(f"\nExtraction Metaphor Systems (use to bury extraction in imagery):")
            lines.append(f"- Preferred metaphors: {', '.join(metaphor_systems)}")
            
            if "natural" in metaphor_systems:
                lines.append("  - Natural: rainfall, current, tide, light, shadow, seasons, weather, river")
            if "economic" in metaphor_systems:
                lines.append("  - Economic: harvest, currency, weight, measure, trade, value, worth, account")
            if "organic" in metaphor_systems:
                lines.append("  - Organic: nutrients, growth, roots, absorption, feeding, exchange")
            if "architectural" in metaphor_systems:
                lines.append("  - Architectural: foundation, support, bearing weight, structure, load")
        
        # Voice instructions
        voice_instructions = talent_data.get("voice_instructions", "")
        if voice_instructions:
            lines.append(f"\nExtraction Voice Guidelines:")
            lines.append(voice_instructions)
        
        # Direct address guidance
        direct_address = talent_data.get("direct_address", {})
        if direct_address:
            freq = direct_address.get("frequency", 0.3)
            mode = direct_address.get("mode", "revealing")
            guidance = direct_address.get("guidance", "")
            
            lines.append(f"\nDirect Address ('you') Guidance:")
            lines.append(f"- Frequency: {'Sparse/rare' if freq < 0.3 else 'Moderate' if freq < 0.6 else 'Frequent'}")
            lines.append(f"- Mode: {mode}")
            if guidance:
                lines.append(f"- {guidance}")
        
        return "\n".join(lines)

    def _build_route_awareness_section(self, context: Dict[str, Any]) -> str:
        live_anchor = context.get("live_anchor") if isinstance(context.get("live_anchor"), dict) else {}
        fallback_anchors = context.get("fallback_anchors") if isinstance(context.get("fallback_anchors"), list) else []
        history = context.get("history") if isinstance(context.get("history"), list) else []
        signals = context.get("signals") if isinstance(context.get("signals"), dict) else {}

        anchor_lines = self._build_anchor_lines(live_anchor, fallback_anchors)
        history_lines = self._build_history_lines(history)
        signal_lines = self._build_signal_lines(signals)

        if not anchor_lines and not history_lines and not signal_lines:
            return ""

        lines = ["\n\nRoute Awareness Context:"]

        if anchor_lines:
            lines.append("Anchors (use 2–3, mostly metaphorical; 1 explicit max):")
            lines.extend(anchor_lines)

        if history_lines:
            lines.append("Historical memory (paraphrase 1–2 cues):")
            lines.extend(history_lines)

        if signal_lines:
            lines.append("Live style modulation (do not mention data sources):")
            lines.extend(signal_lines)

        lines.append("Guardrails:")
        lines.append("- No route IDs.")
        lines.append("- At least one concrete place cue.")
        lines.append("- Mode fidelity (bus vs rail imagery).")
        lines.append("- Live data changes style, not literal facts.")

        return "\n".join(lines)

    def _build_source_poem_section(self, context: Dict[str, Any]) -> str:
        """
        Build a prompt section that steers the model to generate a poem
        similar in spirit to a previous "source" poem without copying it.

        This section encodes high‑level characteristics extracted from a
        prior poem and asks the model to reuse those characteristics as
        creative constraints for a new piece.

        Args:
            context: A dictionary that may contain the following optional keys
                describing the source poem:
                
                - "source_themes": List[str]
                    Core ideas, motifs, or conceptual themes present in the
                    source poem (e.g., "night travel", "loneliness",
                    "urban renewal"). The top 5 themes, if provided, are
                    surfaced to the model as themes to explicitly emphasize.

                - "source_imagery": List[str]
                    Representative images or visual motifs from the source
                    poem (e.g., "sodium‑lamp halos", "graffiti ghosts").
                    The top 5 imagery items, if provided, are surfaced as
                    the imagery style to echo.

                - "source_emotions": List[str]
                    Dominant emotions, moods, or affective tones of the
                    source poem (e.g., "wistful", "defiant", "tender").
                    The top 3 emotions, if provided, are surfaced as the
                    emotional tone to match.

        Returns:
            A formatted string to be appended to the overall LLM prompt,
            instructing the model to write a new poem that honors the
            source poem's themes, imagery style, and emotional atmosphere
            while remaining original.
        """
        lines = ["\n\nSource Poem Influence (Generate Similar):"]
        lines.append("This poem should be inspired by and similar to a previous poem with these characteristics:")
        
        source_themes = context.get("source_themes", [])
        if source_themes:
            lines.append(f"\nThemes to emphasize (USE THESE):")
            for theme in source_themes[:5]:  # Use top 5 themes
                lines.append(f"  - {theme}")
        
        source_imagery = context.get("source_imagery", [])
        if source_imagery:
            lines.append(f"\nImagery style to echo:")
            for image in source_imagery[:5]:  # Use top 5 images
                lines.append(f"  - {image}")
        
        source_emotions = context.get("source_emotions", [])
        if source_emotions:
            lines.append(f"\nEmotional tone to match:")
            for emotion in source_emotions[:3]:  # Use top 3 emotions
                lines.append(f"  - {emotion}")
        
        lines.append("\nGuidance:")
        lines.append("- Write a NEW poem (not a copy) that shares these thematic and stylistic elements")
        lines.append("- Maintain the same emotional atmosphere and imagery style")
        lines.append("- Use the specified themes as your primary focus")
        lines.append("- Create fresh expressions while honoring the source poem's spirit")
        
        return "\n".join(lines)

    def _build_anchor_lines(
        self,
        live_anchor: Dict[str, Any],
        fallback_anchors: List[str]
    ) -> List[str]:
        lines: List[str] = []

        labeled = [
            ("Neighborhood", live_anchor.get("neighborhood")),
            ("Place", live_anchor.get("place")),
            ("POI", live_anchor.get("poi")),
        ]

        for label, value in labeled:
            if isinstance(value, str) and value.strip():
                lines.append(f"- {label}: {value}")

        for anchor in fallback_anchors:
            if len(lines) >= 3:
                break
            if not isinstance(anchor, str) or not anchor.strip():
                continue
            lines.append(f"- Anchor: {anchor}")

        return lines

    def _build_history_lines(self, history: List[Dict[str, Any]]) -> List[str]:
        lines: List[str] = []
        for item in history[:2]:
            if not isinstance(item, dict):
                continue
            title = item.get("title")
            snippet = item.get("snippet")
            if isinstance(title, str) and isinstance(snippet, str) and title.strip() and snippet.strip():
                lines.append(f"- {title}: {snippet}")
        return lines

    def _build_signal_lines(self, signals: Dict[str, Any]) -> List[str]:
        lines: List[str] = []

        weather_summary = self._summarize_weather_signal(signals.get("weather"))
        if weather_summary:
            lines.append(
                f"- Weather tone: {weather_summary} → rain = internal rhyme/assonance; clear = sharper consonants/alliteration; wind = breathy cadence"
            )

        traffic_summary = self._summarize_traffic_signal(signals.get("traffic"))
        if traffic_summary:
            lines.append(
                f"- Traffic rhythm: {traffic_summary} → congested = tighter, clipped lines; smooth/light = longer, flowing lines"
            )

        solar_summary = self._summarize_solar_signal(signals.get("solar"))
        if solar_summary:
            lines.append(
                f"- Solar tone: {solar_summary} → dawn = bright/anticipatory; night = hushed/ritual"
            )

        alerts_summary = self._summarize_alerts_signal(signals.get("alerts"))
        if alerts_summary:
            lines.append(f"- Alerts: {alerts_summary} → add fragmentation/abrupt turns")

        return lines

    def _summarize_weather_signal(self, weather: Any) -> Optional[str]:
        if not isinstance(weather, dict):
            return None
        forecast = weather.get("forecast", {})
        if isinstance(forecast, dict):
            periods = forecast.get("properties", {}).get("periods", [])
            if isinstance(periods, list) and periods:
                period = periods[0]
                if isinstance(period, dict):
                    short_forecast = period.get("shortForecast") or period.get("name")
                    if isinstance(short_forecast, str) and short_forecast.strip():
                        return short_forecast
        return None

    def _summarize_traffic_signal(self, traffic: Any) -> Optional[str]:
        if isinstance(traffic, str) and traffic.strip():
            return traffic
        if isinstance(traffic, dict):
            level = traffic.get("level") or traffic.get("congestion") or traffic.get("summary")
            if isinstance(level, str) and level.strip():
                return level
        return None

    def _summarize_solar_signal(self, solar: Any) -> Optional[str]:
        if not isinstance(solar, dict):
            return None
        phase = solar.get("phase")
        if isinstance(phase, str) and phase.strip():
            return phase
        sunrise = solar.get("sunrise")
        sunset = solar.get("sunset")
        if isinstance(sunrise, str) or isinstance(sunset, str):
            parts = []
            if isinstance(sunrise, str):
                parts.append(f"sunrise {sunrise}")
            if isinstance(sunset, str):
                parts.append(f"sunset {sunset}")
            return ", ".join(parts)
        return None

    def _summarize_alerts_signal(self, alerts: Any) -> Optional[str]:
        if isinstance(alerts, list) and alerts:
            return f"{len(alerts)} active alert(s)"
        return None
    
    def _get_stance_instructions(
        self,
        stance: str,
        narrative_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate specific instructions based on narrative stance.
        """
        if stance == "SUPPORTING":
            return """The poem should EMBRACE the canonical narrative themes:
- Emphasize: surveillance, observation, urban networks, collective movement
- Use imagery of: watching, being seen, connection through transit, organized systems
- Emotional tone: contemplative about visibility, finding meaning in shared space
- The route SUPPORTS the central story about urban observation and connection"""
        
        elif stance == "OPPOSING":
            return """The poem should REJECT or RESIST the canonical narrative:
- Avoid: themes of observation, surveillance, urban networks, collective systems
- Emphasize instead: freedom, escape, solitude, hidden spaces, resistance
- Use imagery of: blindness, escape routes, disconnection, breaking free
- Emotional tone: defiant, liberated, seeking privacy and autonomy
- The route OPPOSES the story of surveillance and control"""
        
        else:  # AMBIVALENT
            return """The poem should show MIXED or CONFLICTED relationship to the canonical narrative:
- Include SOME elements of observation/connection but with tension
- Show both attraction to and discomfort with visibility
- Use imagery that is both connective and isolating
- Emotional tone: uncertain, contemplative, caught between two worlds
- The route is AMBIVALENT about being watched and being connected"""
    
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
