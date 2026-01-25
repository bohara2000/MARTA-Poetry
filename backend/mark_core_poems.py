#!/usr/bin/env python3
"""
Quick script to mark specific user poems as core narrative.
"""

import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from poetry.graph.extended_poetry_graph import ExtendedPoetryGraph

def mark_core_poems():
    """Mark key user poems as core narrative."""
    graph_path = backend_dir / "data" / "poetry_graph.json"
    graph = ExtendedPoetryGraph(str(graph_path))
    
    # Key poems that could form the narrative core
    core_poem_candidates = [
        ("user_poem_Children_of_the_Woods", "Children of the Woods"),
        ("user_poem_The_Silent_Station", "The Silent Station"),
        ("user_poem_The_Dreams_from_Mistren_Peachtree_Street", "The Dreams from Mistren Peachtree Street")
    ]
    
    print("🎯 MARKING KEY POEMS AS CORE NARRATIVE")
    print("=" * 50)
    
    marked_count = 0
    for poem_id, title in core_poem_candidates:
        if graph.mark_poem_as_core(poem_id):
            print(f"✅ Marked as CORE: {title}")
            marked_count += 1
        else:
            print(f"❌ Failed to mark: {title} (ID: {poem_id})")
    
    if marked_count > 0:
        graph.save_graph()
        print(f"\n💾 Successfully marked {marked_count} poems as core narrative!")
        print("\n🎯 What this means:")
        print("   • These poems now form your narrative foundation")
        print("   • You can connect other poems to them")
        print("   • They'll be prioritized in narrative generation")
    else:
        print("\n❌ No poems were marked as core.")
    
    print(f"\n📊 Next steps:")
    print(f"   • Run: python scripts/narrative_manager.py --status")
    print(f"   • Consider marking other poems as 'extensions'")
    print(f"   • Create connections between related poems")

if __name__ == "__main__":
    mark_core_poems()