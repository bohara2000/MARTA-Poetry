"""
Generate actual poems using the talent economy framework.
"""

import sys
import os
import asyncio
from datetime import datetime

# Add the backend directory to Python path
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


def generate_poem(route_id: str, context: dict, story_influence: float = 0.7):
    """Generate a single poem with talent economy framework."""
    
    # Initialize OpenAI client
    client = AzureOpenAI(
        api_key=AZURE_OPENAI_API_KEY,
        api_version=AZURE_OPENAI_API_VERSION,
        azure_endpoint=AZURE_OPENAI_ENDPOINT
    )
    
    # Get graph and personality
    graph = get_poetry_graph()
    personality = load_route_personality(route_id)
    
    # Build prompt
    builder = PromptBuilder(graph)
    prompt = builder.build_prompt_for_route(
        route_id=route_id,
        personality=personality,
        context=context,
        story_influence=story_influence
    )
    
    print(f"\n{'='*80}")
    print(f"GENERATING POEM: {personality.get('name')}")
    print(f"{'='*80}")
    print(f"Context: {context.get('time_of_day')} at {context.get('location')}")
    print(f"Talent Economy: {personality.get('talent_economy', {}).get('enabled', False)}")
    print(f"{'='*80}\n")
    
    # Generate poem
    try:
        response = client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT_NAME,
            messages=[
                {"role": "system", "content": "You are a poetic voice for a transit route."},
                {"role": "user", "content": prompt}
            ],
            temperature=1,
            max_completion_tokens=2000  # Increased for reasoning models (o1/o4 series)
        )
        
        # Debug: print the full response
        print(f"DEBUG: Response status: {response}")
        print(f"DEBUG: Choices: {response.choices}")
        
        if response.choices and len(response.choices) > 0:
            poem_text = response.choices[0].message.content
            if poem_text:
                poem_text = poem_text.strip()
            else:
                print("⚠️ Warning: Empty content in response")
                poem_text = "(empty response)"
        else:
            print("⚠️ Warning: No choices in response")
            poem_text = "(no choices)"
        
        print("GENERATED POEM:")
        print("-" * 80)
        print(poem_text)
        print("-" * 80)
        
        return poem_text
        
    except Exception as e:
        print(f"❌ Error generating poem: {e}")
        return None


def main():
    """Generate poems for different routes and contexts."""
    
    # Initialize graph
    print("Initializing poetry graph...")
    initialize_graph("data/poetry_graph.json")
    
    # Test 1: Route 5 - Morning Rush (Sympathetic Joy Merchant)
    print("\n\n" + "="*80)
    print("TEST 1: Route 5 - Morning Rush")
    print("Expected: Buried extraction in natural metaphors, sympathetic tone")
    print("="*80)
    
    generate_poem(
        route_id="MARTA_5",
        context={
            "time_of_day": "morning_rush",
            "location": "Peachtree & Ellis",
            "passenger_count": "high",
            "signals": {
                "weather": "Clear",
                "traffic": "moderate congestion",
                "solar": {"phase": "dawn"}
            }
        },
        story_influence=0.7
    )
    
    # Test 2: Route 21 - Late Night (Brutal Truth Collector)
    print("\n\n" + "="*80)
    print("TEST 2: Route 21 - Late Night")
    print("Expected: More explicit extraction, revealing tone, premium market")
    print("="*80)
    
    generate_poem(
        route_id="MARTA_21",
        context={
            "time_of_day": "late_night",
            "location": "Memorial Drive",
            "passenger_count": "low",
            "signals": {
                "weather": "Clear",
                "traffic": "light",
                "solar": {"phase": "night"}
            }
        },
        story_influence=0.3
    )
    
    # Test 3: Route 27 - Evening (Memory Witness)
    print("\n\n" + "="*80)
    print("TEST 3: Route 27 - Evening")
    print("Expected: Complicit tone, economic/architectural metaphors, moderate visibility")
    print("="*80)
    
    generate_poem(
        route_id="MARTA_27339",
        context={
            "time_of_day": "evening",
            "location": "Cheshire Bridge Road",
            "passenger_count": "moderate",
            "signals": {
                "weather": "Cloudy",
                "traffic": "moderate",
                "solar": {"phase": "dusk"}
            }
        },
        story_influence=0.5
    )
    
    # Test 4: Route 5 - Rainy Morning (High anxiety premium)
    print("\n\n" + "="*80)
    print("TEST 4: Route 5 - Rainy Morning")
    print("Expected: Premium market (weather anxiety), extraction opportunities noted")
    print("="*80)
    
    generate_poem(
        route_id="MARTA_5",
        context={
            "time_of_day": "morning",
            "location": "Peachtree Center",
            "passenger_count": "moderate",
            "signals": {
                "weather": "Rain",
                "traffic": "heavy congestion",
                "solar": {"phase": "morning"}
            }
        },
        story_influence=0.8
    )


if __name__ == "__main__":
    main()
