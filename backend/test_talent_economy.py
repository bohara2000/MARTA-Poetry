"""
Test script to verify talent economy integration in prompt generation.
"""

import sys
import os
from pprint import pprint

# Add the backend directory to Python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

from poetry.graph import get_poetry_graph, initialize_graph
from poetry.prompt_builder import PromptBuilder, load_route_personality


def test_route_5_morning():
    """Test Route 5 with morning rush context."""
    print("="*80)
    print("TEST: Route 5 - Morning Rush (Sympathetic Joy Merchant)")
    print("="*80)
    
    # Initialize and load graph
    initialize_graph("data/poetry_graph.json")
    graph = get_poetry_graph()
    
    # Load Route 5 personality
    route_id = "MARTA_5"
    personality = load_route_personality(route_id)
    
    print("\n🔧 Route Personality:")
    print(f"  Name: {personality.get('name')}")
    print(f"  Description: {personality.get('description')}")
    print(f"  Loyalty: {personality.get('loyalty_to_canon')}")
    
    talent_config = personality.get('talent_economy', {})
    if talent_config.get('enabled'):
        print(f"\n💰 Talent Economy Config:")
        print(f"  Sympathy Level: {talent_config.get('sympathy_level')}")
        print(f"  Extraction Visibility: {talent_config.get('extraction_visibility')}")
        print(f"  Preferred Currencies: {', '.join(talent_config.get('preferred_currencies', []))}")
        print(f"  Address Mode: {talent_config.get('address_mode')}")
    
    # Create context
    context = {
        "time_of_day": "morning_rush",
        "location": "Peachtree & Ellis",
        "passenger_count": "high",
        "signals": {
            "weather": "Clear",
            "traffic": "moderate congestion",
            "solar": {"phase": "dawn"}
        }
    }
    
    print(f"\n🌍 Context:")
    print(f"  Time: {context['time_of_day']}")
    print(f"  Location: {context['location']}")
    print(f"  Weather: Clear, dawn, moderate traffic")
    
    # Build prompt
    builder = PromptBuilder(graph)
    prompt = builder.build_prompt_for_route(
        route_id=route_id,
        personality=personality,
        context=context,
        story_influence=0.7
    )
    
    print("\n" + "="*80)
    print("GENERATED PROMPT:")
    print("="*80)
    print(prompt)
    print("="*80)


def test_route_21_night():
    """Test Route 21 with late night context."""
    print("\n\n")
    print("="*80)
    print("TEST: Route 21 - Late Night (Brutal Truth Collector)")
    print("="*80)
    
    # Graph already initialized, just get it
    graph = get_poetry_graph()
    
    # Load Route 21 personality
    route_id = "MARTA_21"
    personality = load_route_personality(route_id)
    
    print("\n🔧 Route Personality:")
    print(f"  Name: {personality.get('name')}")
    print(f"  Description: {personality.get('description')}")
    print(f"  Loyalty: {personality.get('loyalty_to_canon')}")
    
    talent_config = personality.get('talent_economy', {})
    if talent_config.get('enabled'):
        print(f"\n💰 Talent Economy Config:")
        print(f"  Sympathy Level: {talent_config.get('sympathy_level')}")
        print(f"  Extraction Visibility: {talent_config.get('extraction_visibility')}")
        print(f"  Preferred Currencies: {', '.join(talent_config.get('preferred_currencies', []))}")
        print(f"  Address Mode: {talent_config.get('address_mode')}")
    
    # Create context
    context = {
        "time_of_day": "late_night",
        "location": "Memorial Drive",
        "passenger_count": "low",
        "signals": {
            "weather": "Clear",
            "traffic": "light",
            "solar": {"phase": "night"}
        }
    }
    
    print(f"\n🌍 Context:")
    print(f"  Time: {context['time_of_day']}")
    print(f"  Location: {context['location']}")
    print(f"  Weather: Clear night, light traffic")
    
    # Build prompt
    builder = PromptBuilder(graph)
    prompt = builder.build_prompt_for_route(
        route_id=route_id,
        personality=personality,
        context=context,
        story_influence=0.3
    )
    
    print("\n" + "="*80)
    print("GENERATED PROMPT:")
    print("="*80)
    print(prompt)
    print("="*80)


if __name__ == "__main__":
    test_route_5_morning()
    test_route_21_night()
