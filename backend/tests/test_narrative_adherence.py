#!/usr/bin/env python3
"""
Narrative Adherence Testing Tool

This script tests how well a route's generated poems adhere to the expected narrative stance
based on their story_influence parameter and personality settings.
"""

import sys
import os
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List, Tuple
from datetime import datetime
from collections import Counter

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from poetry.graph.extended_poetry_graph import ExtendedPoetryGraph
from poetry.narrative_engine import apply_story_influence, get_narrative_stance, MOCK_POETRY_COLLECTION
from poetry.graph.poem_analyzer_azure import PoemAnalyzer
from poetry.character_agent import get_route_personality


class NarrativeAdherenceTest:
    """Tests narrative adherence for routes based on story influence."""
    
    def __init__(self):
        """Initialize the narrative adherence tester."""
        self.graph_path = backend_dir / "data" / "poetry_graph.json"
        self.graph = None
        self.analyzer = PoemAnalyzer()
    
    def load_graph(self) -> ExtendedPoetryGraph:
        """Load the graph."""
        if self.graph is None:
            if not self.graph_path.exists():
                raise FileNotFoundError(f"Graph file not found: {self.graph_path}")
            self.graph = ExtendedPoetryGraph(str(self.graph_path))
        return self.graph
    
    def test_route_narrative_adherence(self, route_id: str, story_influence: float) -> Dict[str, Any]:
        """
        Test how well a route's poems adhere to expected narrative stance.
        
        Args:
            route_id: The route to test
            story_influence: The story influence level to test against
            
        Returns:
            Dictionary with test results and analysis
        """
        graph = self.load_graph()
        
        print(f"\n🧪 Testing Narrative Adherence for Route {route_id}")
        print(f"📊 Story Influence: {story_influence:.2f}")
        print("=" * 60)
        
        # Get expected narrative stance
        personality = get_route_personality(route_id)
        expected_stance = get_narrative_stance(story_influence)
        narrative_data = apply_story_influence(route_id, personality, story_influence)
        
        print(f"🎯 Expected Narrative Stance: {expected_stance.upper()}")
        print(f"📝 Expected Emotional Tone: {narrative_data['emotional_tone']}")
        
        # Get route's actual poems
        route_poems = self._get_route_poems(graph, route_id)
        
        if not route_poems:
            return {
                "route_id": route_id,
                "story_influence": story_influence,
                "expected_stance": expected_stance,
                "test_result": "NO_POEMS",
                "message": "No poems found for this route"
            }
        
        print(f"📚 Found {len(route_poems)} poems to analyze")
        
        # Analyze each poem for narrative elements
        adherence_scores = []
        detailed_analysis = []
        
        for poem_id, poem_data in route_poems:
            poem_text = poem_data.get("text", "")
            poem_title = poem_data.get("title", "Untitled")
            
            score, analysis = self._analyze_poem_adherence(
                poem_text, poem_title, expected_stance, narrative_data
            )
            
            adherence_scores.append(score)
            detailed_analysis.append({
                "poem_id": poem_id,
                "title": poem_title,
                "adherence_score": score,
                "analysis": analysis
            })
            
            print(f"   📖 '{poem_title[:40]}...': {score:.2f}/1.0")
        
        # Calculate overall adherence
        avg_adherence = sum(adherence_scores) / len(adherence_scores)
        
        # Determine test result
        if avg_adherence >= 0.8:
            result = "HIGH_ADHERENCE"
        elif avg_adherence >= 0.6:
            result = "MODERATE_ADHERENCE"
        elif avg_adherence >= 0.4:
            result = "LOW_ADHERENCE"
        else:
            result = "POOR_ADHERENCE"
        
        print(f"\n🎯 Overall Adherence Score: {avg_adherence:.2f}/1.0")
        print(f"📊 Test Result: {result}")
        
        return {
            "route_id": route_id,
            "story_influence": story_influence,
            "expected_stance": expected_stance,
            "avg_adherence_score": avg_adherence,
            "test_result": result,
            "poems_analyzed": len(route_poems),
            "detailed_analysis": detailed_analysis,
            "narrative_data": narrative_data
        }
    
    def _get_route_poems(self, graph: ExtendedPoetryGraph, route_id: str) -> List[Tuple[str, Dict]]:
        """Get all poems for a specific route."""
        poems = []
        for node_id, data in graph.graph.nodes(data=True):
            if (data.get("type") == "poem" and 
                data.get("route_id") == route_id):
                poems.append((node_id, data))
        return poems
    
    def _analyze_poem_adherence(
        self,
        poem_text: str,
        poem_title: str,
        expected_stance: str,
        narrative_data: Dict[str, Any]
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Analyze how well a poem adheres to expected narrative stance.
        
        Returns:
            Tuple of (adherence_score, detailed_analysis)
        """
        try:
            # Get poem analysis
            poem_analysis = self.analyzer.analyze_poem(poem_text, poem_title)
        except Exception as e:
            print(f"   ⚠️ Analysis failed for '{poem_title}': {e}")
            return 0.0, {"error": str(e)}
        
        # Check for expected motifs/themes
        expected_motifs = set(narrative_data.get("emphasized_motifs", []))
        rejected_motifs = set(narrative_data.get("rejected_motifs", []))
        
        poem_themes = set(poem_analysis.get("themes", []))
        poem_imagery = set(poem_analysis.get("imagery", []))
        poem_emotions = set(poem_analysis.get("emotions", []))
        
        # Calculate adherence score
        adherence_factors = []
        
        # 1. Theme alignment (40% weight)
        theme_alignment = self._calculate_theme_alignment(
            poem_themes, expected_stance
        )
        adherence_factors.append(("theme_alignment", theme_alignment, 0.4))
        
        # 2. Motif presence (30% weight)
        motif_score = self._calculate_motif_score(
            poem_imagery, expected_motifs, rejected_motifs
        )
        adherence_factors.append(("motif_adherence", motif_score, 0.3))
        
        # 3. Emotional tone alignment (20% weight)
        emotion_score = self._calculate_emotion_alignment(
            poem_emotions, expected_stance
        )
        adherence_factors.append(("emotion_alignment", emotion_score, 0.2))
        
        # 4. Narrative fragment detection (10% weight)
        fragment_score = self._check_narrative_fragments(
            poem_text, narrative_data.get("narrative_fragments", [])
        )
        adherence_factors.append(("narrative_fragments", fragment_score, 0.1))
        
        # Calculate weighted score
        total_score = sum(score * weight for _, score, weight in adherence_factors)
        
        analysis = {
            "adherence_factors": adherence_factors,
            "poem_themes": list(poem_themes),
            "poem_imagery": list(poem_imagery),
            "poem_emotions": list(poem_emotions),
            "expected_motifs": list(expected_motifs),
            "rejected_motifs": list(rejected_motifs)
        }
        
        return total_score, analysis
    
    def _calculate_theme_alignment(self, poem_themes: set, expected_stance: str) -> float:
        """Calculate how well poem themes align with narrative stance."""
        canonical_themes = set(MOCK_POETRY_COLLECTION["central_themes"])
        
        # Convert themes to lowercase for matching
        poem_themes_lower = {theme.lower() for theme in poem_themes}
        canonical_lower = {theme.lower() for theme in canonical_themes}
        
        if expected_stance == "supporting":
            # Should embrace canonical themes
            overlap = len(poem_themes_lower & canonical_lower)
            return min(1.0, overlap / 2.0)  # Normalize by expecting 2+ canonical themes
        
        elif expected_stance == "opposing":
            # Should avoid canonical themes
            overlap = len(poem_themes_lower & canonical_lower)
            return max(0.0, 1.0 - overlap / 2.0)  # Penalize canonical themes
        
        else:  # ambivalent
            # Should have some but not all canonical themes
            overlap = len(poem_themes_lower & canonical_lower)
            if overlap == 1:
                return 1.0  # Perfect ambivalence
            elif overlap == 0:
                return 0.7  # Acceptable avoidance
            else:
                return 0.5  # Too much engagement
    
    def _calculate_motif_score(
        self,
        poem_imagery: set,
        expected_motifs: set,
        rejected_motifs: set
    ) -> float:
        """Calculate motif adherence score."""
        if not expected_motifs and not rejected_motifs:
            return 1.0
        
        poem_imagery_lower = {img.lower() for img in poem_imagery}
        expected_lower = {motif.lower() for motif in expected_motifs}
        rejected_lower = {motif.lower() for motif in rejected_motifs}
        
        # Check for expected motifs (partial string matching)
        expected_found = 0
        for poem_img in poem_imagery_lower:
            for expected in expected_lower:
                if expected in poem_img or poem_img in expected:
                    expected_found += 1
                    break
        
        # Check for rejected motifs (penalty)
        rejected_found = 0
        for poem_img in poem_imagery_lower:
            for rejected in rejected_lower:
                if rejected in poem_img or poem_img in rejected:
                    rejected_found += 1
                    break
        
        # Calculate score
        expected_score = min(1.0, expected_found / max(1, len(expected_motifs)))
        rejection_penalty = rejected_found * 0.3
        
        return max(0.0, expected_score - rejection_penalty)
    
    def _calculate_emotion_alignment(self, poem_emotions: set, expected_stance: str) -> float:
        """Calculate emotional alignment with narrative stance."""
        surveillance_emotions = {"anxious", "tense", "watchful", "paranoid", "uncomfortable"}
        freedom_emotions = {"peaceful", "liberated", "defiant", "free", "rebellious"}
        ambivalent_emotions = {"conflicted", "uncertain", "contemplative", "complex"}
        
        poem_emotions_lower = {emotion.lower() for emotion in poem_emotions}
        
        if expected_stance == "supporting":
            # Should embrace surveillance themes emotionally
            return len(poem_emotions_lower & surveillance_emotions) / max(1, len(poem_emotions))
        
        elif expected_stance == "opposing":
            # Should embrace freedom/defiance emotions
            return len(poem_emotions_lower & freedom_emotions) / max(1, len(poem_emotions))
        
        else:  # ambivalent
            # Should show conflicted or contemplative emotions
            return len(poem_emotions_lower & ambivalent_emotions) / max(1, len(poem_emotions))
    
    def _check_narrative_fragments(self, poem_text: str, expected_fragments: List[str]) -> float:
        """Check for presence of narrative fragments in poem text."""
        if not expected_fragments:
            return 1.0
        
        poem_text_lower = poem_text.lower()
        fragments_found = 0
        
        for fragment in expected_fragments:
            # Check for key words from fragment
            fragment_words = fragment.lower().split()
            key_words = [w for w in fragment_words if len(w) > 3]  # Focus on significant words
            
            words_found = sum(1 for word in key_words if word in poem_text_lower)
            if words_found >= len(key_words) * 0.5:  # At least half the key words
                fragments_found += 1
        
        return fragments_found / len(expected_fragments)
    
    def test_multiple_story_influences(self, route_id: str, influences: List[float]) -> Dict[str, Any]:
        """Test a route across multiple story influence levels."""
        print(f"\n🧪 COMPREHENSIVE NARRATIVE ADHERENCE TEST")
        print(f"🚌 Route: {route_id}")
        print(f"📊 Testing {len(influences)} story influence levels")
        print("=" * 70)
        
        results = []
        for influence in influences:
            result = self.test_route_narrative_adherence(route_id, influence)
            results.append(result)
        
        # Summary analysis
        print(f"\n📈 SUMMARY ACROSS ALL INFLUENCE LEVELS:")
        print("-" * 50)
        
        for result in results:
            influence = result["story_influence"]
            stance = result["expected_stance"]
            score = result.get("avg_adherence_score", 0.0)
            test_result = result["test_result"]
            
            print(f"Story Influence {influence:.1f} ({stance}): {score:.2f} - {test_result}")
        
        return {
            "route_id": route_id,
            "test_results": results,
            "summary": {
                "avg_adherence_across_all": sum(r.get("avg_adherence_score", 0) for r in results) / len(results),
                "best_adherence": max(results, key=lambda r: r.get("avg_adherence_score", 0)),
                "worst_adherence": min(results, key=lambda r: r.get("avg_adherence_score", 0))
            }
        }
    
    def generate_adherence_report(self, route_id: str, save_to_file: bool = True) -> str:
        """Generate a comprehensive narrative adherence report for a route."""
        # Test across different story influence levels
        influence_levels = [0.1, 0.3, 0.5, 0.7, 0.9]
        results = self.test_multiple_story_influences(route_id, influence_levels)
        
        # Generate report
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("🧪 NARRATIVE ADHERENCE TEST REPORT")
        report_lines.append(f"Route: {route_id}")
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("=" * 80)
        
        # Executive Summary
        summary = results["summary"]
        report_lines.append("\n🎯 EXECUTIVE SUMMARY")
        report_lines.append("-" * 40)
        report_lines.append(f"Average Adherence Across All Tests: {summary['avg_adherence_across_all']:.2f}")
        
        best = summary["best_adherence"]
        worst = summary["worst_adherence"]
        
        report_lines.append(f"\nBest Performance:")
        report_lines.append(f"  Story Influence: {best['story_influence']:.1f} ({best['expected_stance']})")
        report_lines.append(f"  Adherence Score: {best.get('avg_adherence_score', 0):.2f}")
        report_lines.append(f"  Result: {best['test_result']}")
        
        report_lines.append(f"\nWorst Performance:")
        report_lines.append(f"  Story Influence: {worst['story_influence']:.1f} ({worst['expected_stance']})")
        report_lines.append(f"  Adherence Score: {worst.get('avg_adherence_score', 0):.2f}")
        report_lines.append(f"  Result: {worst['test_result']}")
        
        # Detailed Results
        report_lines.append("\n📊 DETAILED TEST RESULTS")
        report_lines.append("-" * 40)
        
        for test_result in results["test_results"]:
            influence = test_result["story_influence"]
            stance = test_result["expected_stance"]
            score = test_result.get("avg_adherence_score", 0)
            
            report_lines.append(f"\n🧪 Story Influence: {influence:.1f} ({stance})")
            report_lines.append(f"   Adherence Score: {score:.2f}")
            report_lines.append(f"   Test Result: {test_result['test_result']}")
            report_lines.append(f"   Poems Analyzed: {test_result['poems_analyzed']}")
            
            if test_result.get("detailed_analysis"):
                report_lines.append("   Individual Poem Scores:")
                for poem_analysis in test_result["detailed_analysis"][:5]:  # Show top 5
                    title = poem_analysis["title"][:30]
                    poem_score = poem_analysis["adherence_score"]
                    report_lines.append(f"     • {title}: {poem_score:.2f}")
        
        report_content = "\n".join(report_lines)
        
        if save_to_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            reports_dir = backend_dir / "reports"
            reports_dir.mkdir(exist_ok=True)
            report_file = reports_dir / f"narrative_adherence_{route_id}_{timestamp}.txt"
            
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report_content)
            print(f"\n📁 Report saved to: {report_file}")
        
        return report_content


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(
        description="Test narrative adherence for MARTA routes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_narrative_adherence.py --route MARTA_5 --influence 0.7
  python test_narrative_adherence.py --route MARTA_21 --comprehensive
  python test_narrative_adherence.py --report MARTA_5
        """
    )
    
    parser.add_argument('--route', '-r', required=True,
                       help='Route ID to test (e.g., MARTA_5)')
    parser.add_argument('--influence', '-i', type=float,
                       help='Story influence level to test (0.0-1.0)')
    parser.add_argument('--comprehensive', '-c', action='store_true',
                       help='Test multiple story influence levels')
    parser.add_argument('--report', action='store_true',
                       help='Generate comprehensive report')
    
    args = parser.parse_args()
    
    tester = NarrativeAdherenceTest()
    
    if args.report:
        tester.generate_adherence_report(args.route)
    elif args.comprehensive:
        influence_levels = [0.1, 0.3, 0.5, 0.7, 0.9]
        tester.test_multiple_story_influences(args.route, influence_levels)
    elif args.influence is not None:
        tester.test_route_narrative_adherence(args.route, args.influence)
    else:
        print("❌ Must specify either --influence, --comprehensive, or --report")
        sys.exit(1)


if __name__ == "__main__":
    main()