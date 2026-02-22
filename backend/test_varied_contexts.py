"""
Generate more test poems with varied contexts to showcase talent economy dynamics.
"""

import sys
import os

backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

from poetry.graph import get_poetry_graph, initialize_graph
from poetry.prompt_builder import PromptBuilder, load_route_personality
from openai import AzureOpenAI
from config import (
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_DEPLOYMENT_NAME,
    AZURE_OPENAI_API_VERSION
)


def generate_poem(route_id: str, context: dict, story_influence: float, test_name: str, expected: str):
    """Generate a single poem."""
    
    client = AzureOpenAI(
        api_key=AZURE_OPENAI_API_KEY,
        api_version=AZURE_OPENAI_API_VERSION,
        azure_endpoint=AZURE_OPENAI_ENDPOINT
    )
    
    graph = get_poetry_graph()
    personality = load_route_personality(route_id)
    
    builder = PromptBuilder(graph)
    prompt = builder.build_prompt_for_route(
        route_id=route_id,
        personality=personality,
        context=context,
        story_influence=story_influence
    )
    
    print(f"\n{'='*80}")
    print(f"TEST: {test_name}")
    print(f"{'='*80}")
    print(f"Route: {personality.get('name')}")
    print(f"Time: {context.get('time_of_day')}")
    print(f"Location: {context.get('location')}")
    print(f"Weather: {context.get('signals', {}).get('weather', 'N/A')}")
    print(f"Traffic: {context.get('signals', {}).get('traffic', 'N/A')}")
    print(f"\nExpected: {expected}")
    print(f"{'='*80}\n")
    
    try:
        response = client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT_NAME,
            messages=[
                {"role": "system", "content": "You are a poetic voice for a transit route."},
                {"role": "user", "content": prompt}
            ],
            temperature=1,
            max_completion_tokens=3000
        )
        
        poem_text = response.choices[0].message.content
        if poem_text:
            poem_text = poem_text.strip()
        else:
            poem_text = "(empty response)"
        
        print("POEM:")
        print("-" * 80)
        print(poem_text)
        print("-" * 80)
        
        return poem_text
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def main():
    """Generate diverse test poems."""
    
    print("Initializing poetry graph...")
    initialize_graph("data/poetry_graph.json")
    
    # Test 1: Route 5 - Heavy rain + traffic congestion (PREMIUM market)
    generate_poem(
        route_id="MARTA_5",
        context={
            "time_of_day": "morning_rush",
            "location": "Peachtree & 5th",
            "passenger_count": "very_high",
            "signals": {
                "weather": "Heavy Rain and Thunderstorms",
                "traffic": "heavy congestion",
                "solar": {"phase": "morning"}
            }
        },
        story_influence=0.75,
        test_name="Route 5 - Stormy Rush Hour",
        expected="Premium market (weather anxiety spike + congestion frustration). Sympathetic but aware of high-value extraction opportunity."
    )
    
    # Test 2: Route 5 - Sunny weekend afternoon (LOW-GRADE market)
    generate_poem(
        route_id="MARTA_5",
        context={
            "time_of_day": "afternoon",
            "location": "Peachtree Station",
            "passenger_count": "low",
            "signals": {
                "weather": "Sunny and Clear",
                "traffic": "light",
                "solar": {"phase": "afternoon"}
            }
        },
        story_influence=0.6,
        test_name="Route 5 - Calm Weekend",
        expected="Commodity/low-grade market. Less valuable emotional currency available. Route may note the scarcity."
    )
    
    # Test 3: Route 21 - 3 AM (ULTRA-PREMIUM market)
    generate_poem(
        route_id="MARTA_21",
        context={
            "time_of_day": "late_night",
            "location": "Memorial Drive",
            "passenger_count": "very_low",
            "signals": {
                "weather": "Clear",
                "traffic": "light",
                "solar": {"phase": "deep_night"}
            }
        },
        story_influence=0.2,
        test_name="Route 21 - 3 AM Deep Night",
        expected="Ultra-premium scarcity market. Explicit extraction of rare midnight vulnerability and isolation."
    )
    
    # Test 4: Route 27 - Evening rain + gentrification observation
    generate_poem(
        route_id="MARTA_27339",
        context={
            "time_of_day": "evening",
            "location": "Cheshire Bridge Road",
            "passenger_count": "moderate",
            "signals": {
                "weather": "Light Rain",
                "traffic": "moderate",
                "solar": {"phase": "dusk"}
            }
        },
        story_influence=0.5,
        test_name="Route 27 - Rainy Gentrification Zone",
        expected="Complicit tone noting contradiction/memory extraction. Rain provides melancholy premium."
    )
    
    # Test 5: Route 21 - Friday night (different extraction than work commute)
    generate_poem(
        route_id="MARTA_21",
        context={
            "time_of_day": "night",
            "location": "East Atlanta",
            "passenger_count": "moderate",
            "signals": {
                "weather": "Clear",
                "traffic": "moderate",
                "solar": {"phase": "night"}
            }
        },
        story_influence=0.4,
        test_name="Route 21 - Friday Night Social Traffic",
        expected="Different currency extraction - anticipation, social energy vs work dread. Still revealing/clinical."
    )
    
    # Test 6: Route 5 - Early dawn (hope/anticipation currency)
    generate_poem(
        route_id="MARTA_5",
        context={
            "time_of_day": "early_morning",
            "location": "Peachtree & North Avenue",
            "passenger_count": "low",
            "signals": {
                "weather": "Clear",
                "traffic": "light",
                "solar": {"phase": "pre-dawn"}
            }
        },
        story_influence=0.8,
        test_name="Route 5 - Pre-Dawn Quiet",
        expected="Dawn anticipation/hope currency. Sympathetic extraction of rare early morning optimism."
    )


if __name__ == "__main__":
    main()
