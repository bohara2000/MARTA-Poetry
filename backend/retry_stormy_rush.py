"""
Regenerate the failed stormy rush hour poem.
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

# Initialize
initialize_graph("data/poetry_graph.json")
graph = get_poetry_graph()

route_id = "MARTA_5"
personality = load_route_personality(route_id)
context = {
    "time_of_day": "morning_rush",
    "location": "Peachtree & 5th",
    "passenger_count": "very_high",
    "signals": {
        "weather": "Heavy Rain and Thunderstorms",
        "traffic": "heavy congestion",
        "solar": {"phase": "morning"}
    }
}

builder = PromptBuilder(graph)
prompt = builder.build_prompt_for_route(
    route_id=route_id,
    personality=personality,
    context=context,
    story_influence=0.75
)

print("="*80)
print("Route 5 - Stormy Rush Hour (RETRY)")
print("="*80)
print("Expected: Premium market (weather anxiety spike + congestion frustration)")
print("Sympathetic but aware of high-value extraction opportunity.")
print("="*80)

client = AzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    api_version=AZURE_OPENAI_API_VERSION,
    azure_endpoint=AZURE_OPENAI_ENDPOINT
)

# Try with even higher token limit
response = client.chat.completions.create(
    model=AZURE_OPENAI_DEPLOYMENT_NAME,
    messages=[
        {"role": "system", "content": "You are a poetic voice for a transit route."},
        {"role": "user", "content": prompt}
    ],
    temperature=1,
    max_completion_tokens=4000  # Very high limit for this complex scenario
)

poem_text = response.choices[0].message.content.strip() if response.choices[0].message.content else "(empty)"

# Show reasoning token usage
usage = response.usage
print(f"\nToken Usage:")
print(f"  Prompt: {usage.prompt_tokens}")
print(f"  Completion: {usage.completion_tokens}")
if hasattr(usage.completion_tokens_details, 'reasoning_tokens'):
    print(f"  Reasoning: {usage.completion_tokens_details.reasoning_tokens}")
print()

print("GENERATED POEM:")
print("-" * 80)
print(poem_text)
print("-" * 80)
