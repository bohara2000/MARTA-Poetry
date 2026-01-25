#!/usr/bin/env python3
"""
Individual Poem Explorer

This script lets you explore individual poems in the graph and their connections.
"""

import sys
import os
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from poetry.graph.extended_poetry_graph import ExtendedPoetryGraph


class PoemExplorer:
    """Explores individual poems and their connections."""
    
    def __init__(self):
        """Initialize the poem explorer."""
        self.graph_path = backend_dir / "data" / "poetry_graph.json"
        self.graph = None
    
    def load_graph(self) -> ExtendedPoetryGraph:
        """Load the graph."""
        if self.graph is None:
            if not self.graph_path.exists():
                print(f"❌ Graph file not found: {self.graph_path}")
                print("Run 'python scripts/graph_initializer.py --examine' first")
                sys.exit(1)
            
            self.graph = ExtendedPoetryGraph(str(self.graph_path))
        return self.graph
    
    def list_poems(self):
        """List all poems in the graph."""
        graph = self.load_graph()
        
        poems = [(node_id, data) for node_id, data in graph.graph.nodes(data=True) 
                if data.get("type") == "poem"]
        
        if not poems:
            print("❌ No poems found in graph!")
            return
        
        print("=" * 80)
        print("📚 ALL POEMS IN GRAPH")
        print("=" * 80)
        
        for i, (poem_id, poem_data) in enumerate(poems, 1):
            title = poem_data.get("title", "Untitled")
            route_id = poem_data.get("route_id", "Unknown")
            created_at = poem_data.get("created_at", "Unknown")
            
            if created_at != "Unknown" and "T" in created_at:
                # Format datetime for display
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                    created_at = dt.strftime("%Y-%m-%d %H:%M")
                except:
                    pass
            
            print(f"{i:3}. [{poem_id}] {title}")
            print(f"     Route: {route_id} | Created: {created_at}")
            
            # Show first line of poem
            text = poem_data.get("text", "")
            if text:
                first_line = text.split('\n')[0][:60]
                if len(text.split('\n')[0]) > 60:
                    first_line += "..."
                print(f"     \"{first_line}\"")
            print()
    
    def show_poem_details(self, poem_id: str):
        """Show detailed information about a specific poem."""
        graph = self.load_graph()
        
        if not graph.graph.has_node(poem_id):
            print(f"❌ Poem '{poem_id}' not found in graph!")
            return
        
        poem_data = graph.get_poem(poem_id)
        
        print("=" * 80)
        print(f"📜 POEM DETAILS: {poem_data.get('title', 'Untitled')}")
        print("=" * 80)
        
        # Basic info
        print(f"🆔 ID: {poem_id}")
        print(f"📝 Title: {poem_data.get('title', 'Untitled')}")
        print(f"🚌 Route: {poem_data.get('route_id', 'Unknown')}")
        print(f"📅 Created: {poem_data.get('created_at', 'Unknown')}")
        
        # Poem text
        text = poem_data.get('text', '')
        print(f"\n📄 Text ({len(text)} characters):")
        print("-" * 40)
        print(text)
        print("-" * 40)
        
        # Connections
        themes = poem_data.get('themes', [])
        imagery = poem_data.get('imagery', [])
        emotions = poem_data.get('emotions', [])
        sound_devices = poem_data.get('sound_devices', [])
        narrative_connections = poem_data.get('narrative_connections', [])
        
        if themes:
            print(f"\n🎭 Themes ({len(themes)}):")
            for theme in themes:
                print(f"   • {theme}")
        
        if imagery:
            print(f"\n🖼️  Imagery ({len(imagery)}):")
            for image in imagery:
                print(f"   • {image}")
        
        if emotions:
            print(f"\n💭 Emotions ({len(emotions)}):")
            for emotion in emotions:
                print(f"   • {emotion}")
        
        if sound_devices:
            print(f"\n🎵 Sound Devices ({len(sound_devices)}):")
            for device in sound_devices:
                print(f"   • {device}")
        
        if narrative_connections:
            print(f"\n🔗 Narrative Connections ({len(narrative_connections)}):")
            for conn in narrative_connections:
                target_id = conn['target_poem_id']
                conn_type = conn.get('connection_type', 'unknown')
                strength = conn.get('strength', 'unknown')
                notes = conn.get('notes', '')
                
                # Get target poem title
                target_data = graph.graph.nodes.get(target_id, {})
                target_title = target_data.get('title', target_id)
                
                print(f"   → {target_title} ({conn_type}, strength: {strength})")
                if notes:
                    print(f"     Notes: {notes}")
        
        # Structure metadata
        metadata = poem_data.get('metadata', {})
        structure = metadata.get('structure', {})
        if structure:
            print(f"\n📐 Structure:")
            line_count = structure.get('line_count', 'Unknown')
            form = structure.get('form', 'Unknown')
            print(f"   • Lines: {line_count}")
            print(f"   • Form: {form}")
            
            # More structure details
            if 'enjambment_lines' in structure:
                enjambment = structure['enjambment_lines']
                print(f"   • Enjambment lines: {len(enjambment)} ({enjambment[:5]}{'...' if len(enjambment) > 5 else ''})")
            
            if 'caesura_lines' in structure:
                caesura = structure['caesura_lines']
                print(f"   • Caesura lines: {len(caesura)} ({caesura[:5]}{'...' if len(caesura) > 5 else ''})")
        
        # Sound patterns
        sound_patterns = metadata.get('sound_patterns', {})
        if sound_patterns:
            print(f"\n🎵 Sound Patterns:")
            for pattern_type, pattern_data in sound_patterns.items():
                if isinstance(pattern_data, list):
                    print(f"   • {pattern_type}: {len(pattern_data)} instances")
                else:
                    print(f"   • {pattern_type}: {pattern_data}")
    
    def find_related_poems(self, poem_id: str):
        """Find poems related to the given poem."""
        graph = self.load_graph()
        
        if not graph.graph.has_node(poem_id):
            print(f"❌ Poem '{poem_id}' not found in graph!")
            return
        
        poem_data = graph.get_poem(poem_id)
        poem_title = poem_data.get('title', 'Untitled')
        
        print("=" * 80)
        print(f"🔍 FINDING POEMS RELATED TO: {poem_title}")
        print("=" * 80)
        
        # Get all poems
        all_poems = [(node_id, data) for node_id, data in graph.graph.nodes(data=True) 
                    if data.get("type") == "poem" and node_id != poem_id]
        
        if not all_poems:
            print("❌ No other poems found!")
            return
        
        # Find shared themes, imagery, emotions
        base_themes = set(poem_data.get('themes', []))
        base_imagery = set(poem_data.get('imagery', []))
        base_emotions = set(poem_data.get('emotions', []))
        base_sounds = set(poem_data.get('sound_devices', []))
        
        related_poems = []
        
        for other_id, other_data in all_poems:
            other_poem_data = graph.get_poem(other_id)
            other_themes = set(other_poem_data.get('themes', []))
            other_imagery = set(other_poem_data.get('imagery', []))
            other_emotions = set(other_poem_data.get('emotions', []))
            other_sounds = set(other_poem_data.get('sound_devices', []))
            
            # Calculate similarity
            shared_themes = base_themes & other_themes
            shared_imagery = base_imagery & other_imagery
            shared_emotions = base_emotions & other_emotions
            shared_sounds = base_sounds & other_sounds
            
            total_shared = len(shared_themes) + len(shared_imagery) + len(shared_emotions) + len(shared_sounds)
            
            if total_shared > 0:
                related_poems.append({
                    'id': other_id,
                    'title': other_poem_data.get('title', 'Untitled'),
                    'route_id': other_poem_data.get('route_id', 'Unknown'),
                    'total_shared': total_shared,
                    'shared_themes': shared_themes,
                    'shared_imagery': shared_imagery,
                    'shared_emotions': shared_emotions,
                    'shared_sounds': shared_sounds
                })
        
        # Sort by similarity
        related_poems.sort(key=lambda x: x['total_shared'], reverse=True)
        
        if not related_poems:
            print("❌ No related poems found!")
            return
        
        print(f"📊 Found {len(related_poems)} related poems:\n")
        
        for i, poem in enumerate(related_poems[:10], 1):  # Show top 10
            print(f"{i:2}. {poem['title']} [{poem['id']}]")
            print(f"     Route: {poem['route_id']} | Similarity: {poem['total_shared']} shared elements")
            
            shared_details = []
            if poem['shared_themes']:
                shared_details.append(f"themes: {', '.join(list(poem['shared_themes'])[:3])}")
            if poem['shared_imagery']:
                shared_details.append(f"imagery: {', '.join(list(poem['shared_imagery'])[:3])}")
            if poem['shared_emotions']:
                shared_details.append(f"emotions: {', '.join(list(poem['shared_emotions'])[:3])}")
            if poem['shared_sounds']:
                shared_details.append(f"sounds: {', '.join(list(poem['shared_sounds'])[:3])}")
            
            if shared_details:
                print(f"     Shared: {'; '.join(shared_details)}")
            print()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Poetry Individual Poem Explorer")
    parser.add_argument("--list", action="store_true", help="List all poems")
    parser.add_argument("--show", type=str, help="Show details for a specific poem ID")
    parser.add_argument("--related", type=str, help="Find poems related to a specific poem ID")
    
    args = parser.parse_args()
    
    explorer = PoemExplorer()
    
    if args.list:
        explorer.list_poems()
    elif args.show:
        explorer.show_poem_details(args.show)
    elif args.related:
        explorer.find_related_poems(args.related)
    else:
        print("Poetry Individual Poem Explorer")
        print("Use --help for options")
        print("\nAvailable commands:")
        print("  --list           List all poems")
        print("  --show POEM_ID   Show detailed information about a poem")
        print("  --related POEM_ID Find poems related to the given poem")


if __name__ == "__main__":
    main()