#!/usr/bin/env python3
"""
Re-test narrative adherence with newly generated poems.
This will generate fresh poems and test them immediately.
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from poetry.route_agent import RouteAgent
from poetry.graph.poem_analyzer_azure import PoemAnalyzer
from poetry.narrative_engine import apply_story_influence, MOCK_POETRY_COLLECTION
from poetry.character_agent import get_route_personality

class RealTimeAdherenceTest:
    """Tests adherence of freshly generated poems."""
    
    def __init__(self):
        self.analyzer = PoemAnalyzer()
    
    def test_route_with_fresh_generation(self, route_id: str, story_influence: float):
        """Generate a poem and immediately test its adherence."""
        
        print(f"\n{'='*70}")
        print(f"🧪 Real-time Adherence Test: {route_id}, story_influence={story_influence}")
        print(f"{'='*70}")
        
        # Step 1: Generate fresh poem
        agent = RouteAgent(route_id)
        poem_text = agent.generate_poem(story_influence)
        
        # Display the poem
        print(f"\n📖 GENERATED POEM:")
        print("-" * 70)
        print(poem_text)
        print("-" * 70)
        
        # Step 2: Analyze the poem
        try:
            poem_analysis = self.analyzer.analyze_poem(poem_text, f"{route_id}_test")
            print("\n✅ Poem analysis completed")
        except Exception as e:
            print(f"❌ Analysis failed: {e}")
            return None
        
        # Step 3: Get expected narrative data
        personality = get_route_personality(route_id)
        narrative_data = apply_story_influence(route_id, personality, story_influence)
        
        # Step 4: Compare
        print(f"\n📊 Analysis Results:")
        print(f"   Themes detected: {poem_analysis.get('themes', [])[:3]}")
        print(f"   Imagery detected: {poem_analysis.get('imagery', [])[:3]}")
        print(f"   Emotions detected: {poem_analysis.get('emotions', [])}")
        
        print(f"\n🎯 Expected Narrative Data:")
        print(f"   Stance: {narrative_data['stance']}")
        print(f"   Emphasized motifs: {narrative_data['emphasized_motifs'][:2]}")
        print(f"   Emotional tone: {narrative_data['emotional_tone']}")
        
        # Step 5: Calculate simple adherence score
        adherence = self._calculate_adherence(
            poem_analysis, 
            narrative_data
        )
        
        print(f"\n🎯 Adherence Score: {adherence:.2f}/1.0")
        
        return adherence
    
    def _calculate_adherence(self, poem_analysis, narrative_data):
        """Quick adherence calculation with substring and fuzzy matching."""
        from difflib import SequenceMatcher
        
        score_components = []
        
        def flexible_match(target, candidates, threshold=0.7):
            """
            Find best match between target and candidates using multiple strategies:
            1. Exact substring match
            2. Fuzzy sequence matching
            3. Word overlap
            """
            target_lower = str(target).lower()
            best_score = 0
            
            for candidate in candidates:
                candidate_lower = str(candidate).lower()
                
                # Strategy 1: Substring match (highest priority)
                if target_lower in candidate_lower or candidate_lower in target_lower:
                    return 1.0
                
                # Strategy 2: Word overlap (check if key words match)
                target_words = set(target_lower.split())
                candidate_words = set(candidate_lower.split())
                if target_words and candidate_words:
                    overlap = len(target_words & candidate_words)
                    word_score = overlap / max(len(target_words), len(candidate_words))
                    best_score = max(best_score, word_score)
                
                # Strategy 3: Fuzzy matching (fallback)
                fuzzy_score = SequenceMatcher(None, target_lower, candidate_lower).ratio()
                best_score = max(best_score, fuzzy_score)
            
            return best_score if best_score >= threshold else 0
        
        # 1. Theme alignment
        poem_themes = [str(t).lower() for t in poem_analysis.get('themes', [])]
        emphasized_motifs = [str(m).lower() for m in narrative_data.get('emphasized_motifs', [])]
        
        if emphasized_motifs and poem_themes:
            theme_matches = 0
            for motif in emphasized_motifs:
                match_score = flexible_match(motif, poem_themes, threshold=0.5)
                if match_score > 0:
                    theme_matches += match_score
            
            theme_score = min(1.0, theme_matches / len(emphasized_motifs))
            score_components.append(("theme_match", theme_score, 0.3))
        
        # 2. Motif presence (check imagery for emphasized motifs)
        poem_imagery = [str(i).lower() for i in poem_analysis.get('imagery', [])]
        if emphasized_motifs and poem_imagery:
            imagery_matches = 0
            for motif in emphasized_motifs:
                match_score = flexible_match(motif, poem_imagery, threshold=0.5)
                if match_score > 0:
                    imagery_matches += match_score
            
            imagery_score = min(1.0, imagery_matches / len(emphasized_motifs))
            score_components.append(("imagery_match", imagery_score, 0.4))
        
        # 3. Emotion alignment (fuzzy match emotions)
        poem_emotions = [str(e).lower() for e in poem_analysis.get('emotions', [])]
        
        # Define stance-appropriate emotions (from canonical analysis)
        if narrative_data['stance'] == "supporting":
            expected_emotions = ["tense", "guarded", "watchful", "observant", "vigilant", "detached"]
        elif narrative_data['stance'] == "opposing":
            expected_emotions = ["defiant", "unsettled", "unease", "uneasy", "curiosity", "cynicism", "mysterious"]
        else:  # ambivalent
            expected_emotions = ["uncertain", "conflicted", "claustrophobic", "tense", "uneasy", "curiosity", "isolation"]
        
        if poem_emotions and expected_emotions:
            emotion_matches = 0
            for emotion in poem_emotions:
                match_score = flexible_match(emotion, expected_emotions, threshold=0.6)
                if match_score > 0:
                    emotion_matches += match_score
            
            emotion_score = min(1.0, emotion_matches / len(poem_emotions))
            score_components.append(("emotion_match", emotion_score, 0.3))
        
        # Calculate weighted score
        total_weight = sum(weight for _, _, weight in score_components)
        if total_weight > 0:
            total_score = sum(score * weight for _, score, weight in score_components) / total_weight
        else:
            total_score = 0
        
        print(f"\n   Components:")
        for component_name, score, weight in score_components:
            print(f"      {component_name}: {score:.2f} (weight: {weight})")
        
        return total_score


def main():
    tester = RealTimeAdherenceTest()
    
    route_id = "MARTA_5"
    test_cases = [
        (0.1, "opposing"),
        (0.3, "opposing"),
        (0.5, "ambivalent"),
        (0.7, "supporting"),
        (0.9, "supporting"),
    ]
    
    results = []
    for story_influence, expected_stance in test_cases:
        score = tester.test_route_with_fresh_generation(route_id, story_influence)
        if score is not None:
            results.append((story_influence, expected_stance, score))
    
    # Summary
    print(f"\n{'='*70}")
    print("📈 SUMMARY")
    print(f"{'='*70}")
    if results:
        avg_score = sum(r[2] for r in results) / len(results)
        print(f"Average Adherence Score: {avg_score:.2f}/1.0")
        print(f"\nDetailed Results:")
        for story_inf, stance, score in results:
            status = "✅" if score >= 0.6 else "⚠️" if score >= 0.4 else "❌"
            print(f"  {status} story_influence={story_inf} ({stance}): {score:.2f}")
    else:
        print("❌ No valid results to summarize")


if __name__ == "__main__":
    main()
