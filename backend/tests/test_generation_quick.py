#!/usr/bin/env python3
"""Quick test of poem generation with narrative constraints."""

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from poetry.route_agent import RouteAgent

def test_generation():
    """Test poem generation with different story_influence levels."""
    route_id = "MARTA_5"
    agent = RouteAgent(route_id)
    
    print("=" * 70)
    print(f"Testing Poem Generation for {route_id}")
    print("=" * 70)
    
    # Test with different story influence levels
    test_cases = [
        (0.1, "opposing"),
        (0.5, "ambivalent"),
        (0.9, "supporting")
    ]
    
    for story_influence, expected_stance in test_cases:
        print(f"\n{'='*70}")
        print(f"Test Case: story_influence={story_influence} (expected: {expected_stance})")
        print(f"{'='*70}")
        
        try:
            poem = agent.generate_poem(story_influence)
            print("\n📖 GENERATED POEM:")
            print("-" * 70)
            print(poem[:500] if len(poem) > 500 else poem)
            if len(poem) > 500:
                print(f"... [{len(poem)} total characters]")
            print("-" * 70)
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_generation()
