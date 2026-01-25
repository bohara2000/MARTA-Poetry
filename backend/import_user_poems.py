#!/usr/bin/env python3
"""
Import User Poems into Poetry Graph

This script reads poems from the poems directory and imports them into the poetry graph
with proper metadata for narrative management.
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Any
import uuid
from datetime import datetime

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from poetry.graph.extended_poetry_graph import ExtendedPoetryGraph


def parse_poem_file(file_path: Path) -> Dict[str, Any]:
    """Parse a poem file and extract title, content, and basic metadata."""
    content = file_path.read_text(encoding='utf-8').strip()
    lines = content.split('\n')
    
    # First non-empty line is usually the title
    title = None
    poem_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if title is None:
            title = line
        else:
            poem_lines.append(line)
    
    # Join the rest as poem content, preserving line breaks
    poem_content = '\n'.join(poem_lines)
    
    return {
        'title': title or file_path.stem.replace('_', ' '),
        'content': content,  # Full content including title
        'poem_text': poem_content,  # Just the poem body
        'filename': file_path.name
    }


def analyze_poem_themes(title: str, content: str) -> Dict[str, List[str]]:
    """Basic analysis to suggest themes, imagery, and emotions.
    
    Note: This provides suggested themes based on keyword detection.
    You can manually add more themes later using the narrative manager.
    """
    content_lower = content.lower()
    
    # Basic theme detection (suggestions only - you can add more themes manually)
    themes = []
    if any(word in content_lower for word in ['death', 'die', 'dying', 'grave', 'cemetery', 'mortality']):
        themes.append('mortality')
    if any(word in content_lower for word in ['love', 'heart', 'beloved', 'romance', 'affection']):
        themes.append('love')
    if any(word in content_lower for word in ['time', 'past', 'future', 'memory', 'remember', 'temporal']):
        themes.append('time')
    if any(word in content_lower for word in ['nature', 'tree', 'forest', 'earth', 'green', 'woods', 'natural']):
        themes.append('nature')
    if any(word in content_lower for word in ['city', 'urban', 'street', 'building', 'train', 'station', 'metropolitan']):
        themes.append('urban')
    if any(word in content_lower for word in ['technology', 'network', 'digital', 'tech', 'networked', 'filaments', 'bio/techno']):
        themes.append('technology')
    if any(word in content_lower for word in ['journey', 'travel', 'path', 'road', 'destination', 'commuter', 'transit']):
        themes.append('journey')
    if any(word in content_lower for word in ['silence', 'quiet', 'whisper', 'sound', 'noise', 'silent', 'voice']):
        themes.append('sound_silence')
    if any(word in content_lower for word in ['family', 'children', 'grandchildren', 'generations', 'ancestors']):
        themes.append('family_generations')
    if any(word in content_lower for word in ['transformation', 'change', 'evolution', 'becoming', 'transition']):
        themes.append('transformation')
    if any(word in content_lower for word in ['connection', 'network', 'relationship', 'link', 'bond']):
        themes.append('connection')
    if any(word in content_lower for word in ['isolation', 'alone', 'separate', 'disconnect', 'apart']):
        themes.append('isolation')
    
    # Basic imagery detection
    imagery = []
    if any(word in content_lower for word in ['woods', 'forest', 'tree', 'leaves']):
        imagery.append('forest')
    if any(word in content_lower for word in ['station', 'train', 'platform', 'tracks']):
        imagery.append('transit')
    if any(word in content_lower for word in ['earth', 'ground', 'soil', 'underground']):
        imagery.append('earth')
    if any(word in content_lower for word in ['voice', 'sound', 'echo', 'whisper']):
        imagery.append('voice')
    if any(word in content_lower for word in ['children', 'child', 'grandchildren']):
        imagery.append('children')
    if any(word in content_lower for word in ['network', 'filaments', 'connection']):
        imagery.append('network')
    
    # Basic emotion detection
    emotions = []
    if any(word in content_lower for word in ['cry', 'cried', 'tears', 'weeping']):
        emotions.append('sorrow')
    if any(word in content_lower for word in ['joy', 'happy', 'celebration', 'laugh']):
        emotions.append('joy')
    if any(word in content_lower for word in ['fear', 'afraid', 'terror', 'scared']):
        emotions.append('fear')
    if any(word in content_lower for word in ['wonder', 'mysterious', 'strange', 'surprise']):
        emotions.append('wonder')
    if any(word in content_lower for word in ['alone', 'lonely', 'solitude', 'isolation']):
        emotions.append('loneliness')
    if any(word in content_lower for word in ['alive', 'living', 'life', 'vital']):
        emotions.append('vitality')
    
    return {
        'themes': themes,
        'imagery': imagery,
        'emotions': emotions
    }


def import_poems_to_graph():
    """Import all poems from the poems directory into the poetry graph."""
    poems_dir = backend_dir / "poems"
    graph_path = backend_dir / "data" / "poetry_graph.json"
    
    if not poems_dir.exists():
        print(f"❌ Poems directory not found: {poems_dir}")
        return
    
    # Load or create graph
    graph = ExtendedPoetryGraph(str(graph_path))
    
    # Find all .txt files in poems directory
    poem_files = list(poems_dir.glob("*.txt"))
    
    if not poem_files:
        print(f"❌ No .txt files found in {poems_dir}")
        return
    
    print(f"📚 Found {len(poem_files)} poem files to import")
    print("=" * 60)    
    print("ℹ️  Note: Auto-detected themes are suggestions based on keywords.")
    print("   You can add more themes manually using the narrative manager.")
    print("=" * 60)    
    imported_count = 0
    skipped_count = 0
    
    for poem_file in poem_files:
        try:
            # Parse the poem
            poem_data = parse_poem_file(poem_file)
            title = poem_data['title']
            content = poem_data['content']
            
            # Generate a unique ID based on filename
            poem_id = f"user_poem_{poem_file.stem}"
            
            # Check if already exists
            if graph.graph.has_node(poem_id):
                print(f"⚠️  Skipping '{title}' - already exists in graph")
                skipped_count += 1
                continue
            
            # Analyze for themes, imagery, emotions
            analysis = analyze_poem_themes(title, content)
            
            # Add to graph
            graph.add_poem(
                poem_id=poem_id,
                title=title,
                text=content,
                route_id="user_authored",
                themes=analysis['themes'],
                imagery=analysis['imagery'],
                emotions=analysis['emotions'],
                metadata={
                    'source_file': poem_file.name,
                    'import_date': datetime.now().isoformat(),
                    'author': 'user',
                    'source_type': 'manual_import'
                },
                narrative_role="unassigned"  # Start as unassigned
            )
            
            print(f"✅ Imported: {title}")
            print(f"   ID: {poem_id}")
            if analysis['themes']:
                print(f"   Themes: {', '.join(analysis['themes'])}")
            if analysis['imagery']:
                print(f"   Imagery: {', '.join(analysis['imagery'])}")
            if analysis['emotions']:
                print(f"   Emotions: {', '.join(analysis['emotions'])}")
            print()
            
            imported_count += 1
            
        except Exception as e:
            print(f"❌ Error importing {poem_file.name}: {e}")
            continue
    
    # Save the graph
    if imported_count > 0:
        graph.save_graph()
        print(f"💾 Saved graph with {imported_count} new poems")
    
    print(f"\n📊 Import Summary:")
    print(f"   • Successfully imported: {imported_count}")
    print(f"   • Skipped (already exists): {skipped_count}")
    print(f"   • Total poem files found: {len(poem_files)}")
    
    if imported_count > 0:
        print(f"\n🎯 Next Steps:")
        print(f"   • Use the narrative manager to assign roles:")
        print(f"     python scripts/narrative_manager.py --interactive")
        print(f"   • Mark important poems as 'core' narrative")
        print(f"   • Mark supporting poems as 'extension'")
        print(f"   • Create connections between related poems")
        print(f"   • Add more themes manually if auto-detection missed any")
        print(f"   • Review and refine the auto-detected themes")


def add_manual_themes_to_poem(poem_id: str, additional_themes: List[str]):
    """Helper function to manually add themes after import."""
    graph_path = backend_dir / "data" / "poetry_graph.json"
    graph = ExtendedPoetryGraph(str(graph_path))
    
    if not graph.graph.has_node(poem_id):
        print(f"❌ Poem {poem_id} not found in graph")
        return False
    
    for theme in additional_themes:
        theme_id = f"theme_{theme.lower().replace(' ', '_')}"
        # This will create the theme node if it doesn't exist
        graph._add_or_update_entity(theme_id, "theme", theme)
        graph.graph.add_edge(poem_id, theme_id, type="has_theme")
    
    graph.save_graph()
    print(f"✅ Added {len(additional_themes)} themes to {poem_id}")
    return True


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Import user poems into the poetry graph')
    parser.add_argument('--import', action='store_true', help='Import poems from poems directory')
    parser.add_argument('--add-themes', help='Add themes to existing poem (format: poem_id:theme1,theme2)')
    
    args = parser.parse_args()
    
    if args.add_themes:
        try:
            poem_id, themes_str = args.add_themes.split(':', 1)
            themes = [t.strip() for t in themes_str.split(',')]
            add_manual_themes_to_poem(poem_id, themes)
        except ValueError:
            print("❌ Format should be: --add-themes poem_id:theme1,theme2")
    else:
        import_poems_to_graph()