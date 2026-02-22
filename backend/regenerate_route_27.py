"""
Regenerate Route 27 poem with higher token limit.
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

# Route 27 context
route_id = "MARTA_27339"
personality = load_route_personality(route_id)
context = {
    "time_of_day": "evening",
    "location": "Cheshire Bridge Road",
    "passenger_count": "moderate",
    "signals": {
        "weather": "Cloudy",
        "traffic": "moderate",
        "solar": {"phase": "dusk"}
    }
}

builder = PromptBuilder(graph)
prompt = builder.build_prompt_for_route(
    route_id=route_id,
    personality=personality,
    context=context,
    story_influence=0.5
)

print("="*80)
print("Route 27 - Evening (Memory Witness)")
print("="*80)
print("Expected: Complicit tone, economic/architectural metaphors, moderate visibility")
print("="*80)

client = AzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    api_version=AZURE_OPENAI_API_VERSION,
    azure_endpoint=AZURE_OPENAI_ENDPOINT
)

response = client.chat.completions.create(
    model=AZURE_OPENAI_DEPLOYMENT_NAME,
    messages=[
        {"role": "system", "content": "You are a poetic voice for a transit route."},
        {"role": "user", "content": prompt}
    ],
    temperature=1,
    max_completion_tokens=3000  # Even higher for this complex prompt
)

poem_text = response.choices[0].message.content.strip() if response.choices[0].message.content else "(empty)"

print("\nGENERATED POEM:")
print("-" * 80)
print(poem_text)
print("-" * 80)
