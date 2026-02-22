"""
Test production deployment of talent economy framework.
Tests the actual FastAPI endpoint with the retry logic.
"""

import sys
import os
import asyncio

backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

from app import generate_poem_for_route
from poetry.graph import initialize_graph


async def test_production_generation():
    """Test production poem generation with talent economy."""
    
    # Initialize graph
    print("Initializing graph...")
    initialize_graph("data/poetry_graph.json")
    
    print("\n" + "="*80)
    print("PRODUCTION TEST: Route 5 - Stormy Morning Rush")
    print("="*80)
    print("This tests the full production pipeline with:")
    print("- Talent economy framework")
    print("- Retry logic for empty responses")
    print("- Higher token limits for reasoning models")
    print("="*80 + "\n")
    
    # Test with the scenario that previously failed
    context = {
        "time_of_day": "morning_rush",
        "location": "Peachtree & 5th",
        "passenger_count": "very_high",
        "signals": {
            "weather": "Heavy Rain and Thunderstorms",
            "traffic": "heavy congestion",
            "solar": {"phase": "morning"}
        },
        "story_influence": 0.75
    }
    
    result = await generate_poem_for_route(
        route_id="MARTA_5",
        context=context
    )
    
    if "error" in result:
        print(f"\n❌ FAILED: {result['error']}\n")
        return False
    
    print("\n" + "="*80)
    print("✅ SUCCESS - Generated Poem:")
    print("="*80)
    print(f"\nTitle: {result.get('title', 'Untitled')}")
    print(f"By: {result.get('route_name', 'Unknown Route')}")
    print("\n" + "-"*80)
    print(result.get('text', '(no poem)'))
    print("-"*80)
    
    print(f"\nMetadata:")
    print(f"  Themes: {', '.join(result.get('metadata', {}).get('themes', []))}")
    print(f"  Sound devices: {', '.join(result.get('metadata', {}).get('sound_devices', []))}")
    
    print("\n" + "="*80)
    print("PRODUCTION TEST COMPLETE")
    print("="*80)
    
    return True


if __name__ == "__main__":
    success = asyncio.run(test_production_generation())
    sys.exit(0 if success else 1)
