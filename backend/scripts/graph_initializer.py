#!/usr/bin/env python3
"""
Manual Graph Initialization and Examination Tool

This script allows you to:
1. Initialize a new poetry graph from existing poems
2. Examine and analyze the current graph state
3. Add new poems manually
4. View graph statistics and relationships

Usage:
    python scripts/graph_initializer.py --examine           # View current graph
    python scripts/graph_initializer.py --initialize       # Initialize from poems
    python scripts/graph_initializer.py --add-poem         # Add a new poem manually
    python scripts/graph_initializer.py --analyze          # Deep analysis
"""

import sys
import os
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from poetry.graph.extended_poetry_graph import ExtendedPoetryGraph
from poetry.graph.poem_analyzer_azure import PoemAnalyzer
from config import AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_DEPLOYMENT_NAME, AZURE_OPENAI_API_VERSION


class GraphManager:
    """Manages the poetry graph for manual operations."""
    
    def __init__(self):
        """Initialize the graph manager."""
        self.graph_path = backend_dir / "data" / "poetry_graph.json"
        self.poems_dir = backend_dir / "poems"
        self.graph = None
        self.analyzer = None
        
    def load_or_create_graph(self) -> ExtendedPoetryGraph:
        """Load existing graph or create new one."""
        if self.graph is None:
            if self.graph_path.exists():
                print(f"📂 Loading existing graph from {self.graph_path}")
                self.graph = ExtendedPoetryGraph(str(self.graph_path))
            else:
                print("🆕 Creating new graph")
                self.graph = ExtendedPoetryGraph()
                self.graph.graph_path = str(self.graph_path)
        return self.graph
    
    def get_analyzer(self) -> PoemAnalyzer:
        """Get the poem analyzer."""
        if self.analyzer is None:
            self.analyzer = PoemAnalyzer()
        return self.analyzer
    
    def examine_graph(self):
        """Examine the current state of the graph."""
        graph = self.load_or_create_graph()
        
        print("=" * 60)
        print("🔍 POETRY GRAPH EXAMINATION")
        print("=" * 60)
        
        # Basic summary
        summary = graph.get_graph_summary()
        print("\n📊 Graph Summary:")
        print(f"   • Total poems: {summary['total_poems']}")
        print(f"   • Total themes: {summary['total_themes']}")
        print(f"   • Total imagery: {summary['total_imagery']}")
        print(f"   • Total emotions: {summary['total_emotions']}")
        print(f"   • Total sound devices: {summary['total_sound_devices']}")
        print(f"   • Contributing routes: {summary['contributing_routes']}")
        print(f"   • Total connections: {summary['total_connections']}")
        
        # Get all poems
        poems = [(node_id, data) for node_id, data in graph.graph.nodes(data=True) 
                if data.get("type") == "poem"]
        
        if not poems:
            print("\n❌ No poems found in graph!")
            return
        
        print(f"\n📚 Poems in Graph ({len(poems)} total):")
        for i, (poem_id, poem_data) in enumerate(poems[:10], 1):  # Show first 10
            title = poem_data.get("title", "Untitled")
            route_id = poem_data.get("route_id", "Unknown")
            created_at = poem_data.get("created_at", "Unknown")
            print(f"   {i:2}. {title[:50]}..." if len(title) > 50 else f"   {i:2}. {title}")
            print(f"       Route: {route_id}, Created: {created_at}")
        
        if len(poems) > 10:
            print(f"       ... and {len(poems) - 10} more poems")
        
        # Show route statistics
        route_stats = graph.get_all_routes_statistics()
        if route_stats:
            print(f"\n🚌 Route Statistics:")
            for stats in route_stats:
                route_id = stats['route_id']
                poem_count = stats['poem_count']
                print(f"   • {route_id}: {poem_count} poems")
        
        # Show most common themes/imagery/emotions
        self._show_common_elements(graph, "theme", "🎭 Themes")
        self._show_common_elements(graph, "imagery", "🖼️  Imagery")
        self._show_common_elements(graph, "emotion", "💭 Emotions")
        self._show_common_elements(graph, "sound_device", "🎵 Sound Devices")
    
    def _show_common_elements(self, graph: ExtendedPoetryGraph, element_type: str, title: str):
        """Show most common elements of a given type."""
        elements = [(node_id, data) for node_id, data in graph.graph.nodes(data=True) 
                   if data.get("type") == element_type]
        
        if not elements:
            return
        
        # Count connections to poems
        element_counts = []
        for element_id, element_data in elements:
            poem_connections = sum(1 for neighbor in graph.graph.neighbors(element_id)
                                 if graph.graph.nodes[neighbor].get("type") == "poem")
            name = element_data.get("name", element_id)
            element_counts.append((name, poem_connections))
        
        # Sort by connection count
        element_counts.sort(key=lambda x: x[1], reverse=True)
        
        print(f"\n{title} (Top 5):")
        for name, count in element_counts[:5]:
            print(f"   • {name}: {count} poem(s)")
    
    def initialize_from_poems(self, batch_mode: bool = False):
        """Initialize graph from poem files in the poems directory."""
        graph = self.load_or_create_graph()
        analyzer = self.get_analyzer()
        
        print("=" * 60)
        print("🚀 INITIALIZING GRAPH FROM POEMS")
        if batch_mode:
            print("📦 Running in BATCH MODE (skip duplicates automatically)")
        print("=" * 60)
        
        # Look for poem files
        poem_files = []
        if self.poems_dir.exists():
            poem_files.extend(self.poems_dir.glob("*.txt"))
            poem_files.extend(self.poems_dir.glob("*.md"))
            poem_files.extend(self.poems_dir.glob("*.json"))
        
        if not poem_files:
            print(f"❌ No poem files found in {self.poems_dir}")
            print("   Create .txt, .md, or .json files with your poems")
            return
        
        print(f"📂 Found {len(poem_files)} poem files")
        
        for poem_file in poem_files:
            print(f"\n📜 Processing: {poem_file.name}")
            
            try:
                if poem_file.suffix == ".json":
                    self._process_json_poem(poem_file, graph, analyzer, batch_mode)
                else:
                    self._process_text_poem(poem_file, graph, analyzer, batch_mode)
            except Exception as e:
                print(f"   ❌ Error processing {poem_file.name}: {e}")
        
        # Save the graph
        print(f"\n💾 Saving graph to {self.graph_path}")
        graph.save_graph()
        print("✅ Graph initialization complete!")
    
    def _process_json_poem(self, poem_file: Path, graph: ExtendedPoetryGraph, analyzer: PoemAnalyzer, batch_mode: bool = False):
        """Process a JSON poem file."""
        with open(poem_file, 'r', encoding='utf-8') as f:
            poem_data = json.load(f)
        
        poem_id = poem_data.get("id") or poem_file.stem
        title = poem_data.get("title") or poem_file.stem
        text = poem_data.get("text") or poem_data.get("content", "")
        route_id = poem_data.get("route_id", "MANUAL")
        
        if not text:
            print(f"   ⚠️  No text found in {poem_file.name}")
            return
        
        self._add_poem_to_graph(poem_id, title, text, route_id, graph, analyzer, batch_mode)
    
    def _process_text_poem(self, poem_file: Path, graph: ExtendedPoetryGraph, analyzer: PoemAnalyzer, batch_mode: bool = False):
        """Process a text poem file."""
        with open(poem_file, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        # Simple parsing - first line as title if it looks like one
        lines = content.split('\n')
        if len(lines) > 1 and len(lines[0]) < 100 and not lines[0].endswith('.'):
            title = lines[0]
            text = '\n'.join(lines[1:]).strip()
        else:
            title = poem_file.stem
            text = content
        
        poem_id = poem_file.stem
        route_id = "MANUAL"
        
        self._add_poem_to_graph(poem_id, title, text, route_id, graph, analyzer, batch_mode)
    
    def _add_poem_to_graph(self, poem_id: str, title: str, text: str, route_id: str, 
                          graph: ExtendedPoetryGraph, analyzer: PoemAnalyzer, batch_mode: bool = False):
        """Add a poem to the graph with analysis."""
        
        # Check if poem already exists
        if graph.graph.has_node(poem_id):
            existing_data = graph.graph.nodes[poem_id]
            if existing_data.get("type") == "poem":
                print(f"   ⚠️  Poem already exists: {title}")
                print(f"       ID: {poem_id}")
                print(f"       Existing title: {existing_data.get('title', 'Untitled')}")
                
                if batch_mode:
                    print(f"   ⏭️  Skipped existing poem (batch mode): {title}")
                    return
                
                # Ask user what to do
                try:
                    response = input("       Action: (s)kip, (o)verwrite, (r)ename? [s]: ").lower().strip()
                    
                    if response == 'o' or response == 'overwrite':
                        print(f"   🔄 Overwriting existing poem: {title}")
                    elif response == 'r' or response == 'rename':
                        # Generate new ID with timestamp
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        original_id = poem_id
                        poem_id = f"{poem_id}_{timestamp}"
                        print(f"   📝 Renamed: {original_id} → {poem_id}")
                    else:
                        print(f"   ⏭️  Skipped existing poem: {title}")
                        return
                except (EOFError, KeyboardInterrupt):
                    print(f"   ⏭️  Skipped existing poem: {title}")
                    return
        
        print(f"   🔍 Analyzing poem: {title}")
        
        # Analyze the poem
        try:
            analysis = analyzer.analyze_poem(text)
            
            # Extract elements
            themes = analysis.get("themes", [])
            imagery = analysis.get("imagery", [])
            emotions = analysis.get("emotions", [])
            sound_devices = analysis.get("sound_devices", [])
            structure_metadata = analysis.get("structure", {})
            sound_metadata = analysis.get("sound_patterns", {})
            
            # Determine narrative role - manual poems are likely core narrative
            narrative_role = "core" if route_id == "MANUAL" else "route_generated"
            
            # Add to graph
            graph.add_poem(
                poem_id=poem_id,
                title=title,
                text=text,
                route_id=route_id,
                themes=themes,
                imagery=imagery,
                emotions=emotions,
                sound_devices=sound_devices,
                structure_metadata=structure_metadata,
                sound_metadata=sound_metadata,
                narrative_role=narrative_role,
                metadata={
                    "created_at": datetime.now().isoformat(),
                    "source": "manual",
                }
            )
            
            print(f"   ✅ Added: {len(themes)} themes, {len(imagery)} imagery, "
                  f"{len(emotions)} emotions, {len(sound_devices)} sound devices")
        
        except Exception as e:
            print(f"   ❌ Analysis failed: {e}")
            # Add poem without analysis - manual poems are likely core narrative
            narrative_role = "core" if route_id == "MANUAL" else "route_generated"
            graph.add_poem(
                poem_id=poem_id,
                title=title,
                text=text,
                route_id=route_id,
                narrative_role=narrative_role,
                metadata={
                    "created_at": datetime.now().isoformat(),
                    "source": "manual",
                    "analysis_failed": str(e)
                }
            )
            print(f"   ⚠️  Added poem without analysis")
    
    def add_poem_interactive(self):
        """Add a poem interactively."""
        graph = self.load_or_create_graph()
        analyzer = self.get_analyzer()
        
        print("=" * 60)
        print("✍️  INTERACTIVE POEM ADDITION")
        print("=" * 60)
        
        # Get poem details
        poem_id = input("Poem ID (unique identifier): ").strip()
        if not poem_id:
            print("❌ Poem ID is required")
            return
        
        if graph.graph.has_node(poem_id):
            print(f"❌ Poem with ID '{poem_id}' already exists")
            return
        
        title = input("Poem title: ").strip()
        if not title:
            title = poem_id
        
        route_id = input("Route ID (e.g., MARTA_5 or MANUAL): ").strip()
        if not route_id:
            route_id = "MANUAL"
        
        print("\nEnter the poem text (press Ctrl+D when finished):")
        text_lines = []
        try:
            while True:
                line = input()
                text_lines.append(line)
        except EOFError:
            pass
        
        text = '\n'.join(text_lines).strip()
        if not text:
            print("❌ Poem text is required")
            return
        
        # Add the poem
        self._add_poem_to_graph(poem_id, title, text, route_id, graph, analyzer)
        
        # Save the graph
        print(f"\n💾 Saving graph...")
        graph.save_graph()
        print("✅ Poem added successfully!")
    
    def analyze_deep(self):
        """Perform deep analysis of the graph."""
        graph = self.load_or_create_graph()
        
        print("=" * 60)
        print("🔬 DEEP GRAPH ANALYSIS")
        print("=" * 60)
        
        # Get all poems
        poems = [(node_id, data) for node_id, data in graph.graph.nodes(data=True) 
                if data.get("type") == "poem"]
        
        if not poems:
            print("❌ No poems found for analysis!")
            return
        
        # Analyze co-occurrences
        print("\n🔗 Element Co-occurrences:")
        
        theme_emotion = graph.get_entity_co_occurrence("theme", "emotion")
        if theme_emotion:
            print("\n   Theme-Emotion pairs (top 10):")
            sorted_pairs = sorted(theme_emotion.items(), key=lambda x: x[1], reverse=True)
            for (theme, emotion), count in sorted_pairs[:10]:
                print(f"     • {theme} + {emotion}: {count} times")
        
        imagery_emotion = graph.get_entity_co_occurrence("imagery", "emotion")
        if imagery_emotion:
            print("\n   Imagery-Emotion pairs (top 10):")
            sorted_pairs = sorted(imagery_emotion.items(), key=lambda x: x[1], reverse=True)
            for (imagery, emotion), count in sorted_pairs[:10]:
                print(f"     • {imagery} + {emotion}: {count} times")
        
        # Analyze poem structures
        print("\n📐 Structural Analysis:")
        line_counts = []
        forms = []
        
        for poem_id, poem_data in poems:
            metadata = poem_data.get("metadata", {})
            structure = metadata.get("structure", {})
            
            if structure:
                line_count = structure.get("line_count", 0)
                form = structure.get("form", "unknown")
                
                if line_count > 0:
                    line_counts.append(line_count)
                if form != "unknown":
                    forms.append(form)
        
        if line_counts:
            avg_lines = sum(line_counts) / len(line_counts)
            min_lines = min(line_counts)
            max_lines = max(line_counts)
            print(f"   • Line counts: avg={avg_lines:.1f}, min={min_lines}, max={max_lines}")
        
        if forms:
            from collections import Counter
            form_counts = Counter(forms)
            print("   • Forms used:")
            for form, count in form_counts.most_common():
                print(f"     • {form}: {count} poems")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Poetry Graph Manual Management Tool")
    parser.add_argument("--examine", action="store_true", help="Examine current graph state")
    parser.add_argument("--initialize", action="store_true", help="Initialize graph from poems")
    parser.add_argument("--batch", action="store_true", help="Skip duplicates automatically (use with --initialize)")
    parser.add_argument("--add-poem", action="store_true", help="Add a poem interactively")
    parser.add_argument("--analyze", action="store_true", help="Perform deep analysis")
    
    args = parser.parse_args()
    
    manager = GraphManager()
    
    if args.examine:
        manager.examine_graph()
    elif args.initialize:
        manager.initialize_from_poems(batch_mode=args.batch)
    elif args.add_poem:
        manager.add_poem_interactive()
    elif args.analyze:
        manager.analyze_deep()
    else:
        # Default: examine graph
        print("No command specified. Use --help for options.")
        print("Defaulting to --examine\n")
        manager.examine_graph()


if __name__ == "__main__":
    main()