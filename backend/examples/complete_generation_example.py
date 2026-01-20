"""
Complete Poem Generation Example

This shows the full flow from route personality → graph query → prompt → generation → analysis → graph update.
"""

from typing import Dict, Any
from openai import AzureOpenAI
from datetime import datetime
import sys
import os


# Add the parent directory (backend) to Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from config import AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_DEPLOYMENT_NAME, AZURE_OPENAI_API_VERSION


# Your existing imports
from poetry.graph import get_poetry_graph, ExtendedPoetryGraph, PoemAnalyzer
from poetry.prompt_builder import PromptBuilder, load_route_personality


async def generate_poem_for_route(
    route_id: str,
    context: Dict[str, Any] = None,
    graph: ExtendedPoetryGraph = None
) -> Dict[str, Any]:
    """
    Complete poem generation pipeline with personality-driven prompts.
    
    This is the function you'd call from your FastAPI endpoints.
    
    Args:
        route_id: MARTA route identifier (e.g., "MARTA_5")
        context: Optional context (time, location, passenger count)
        graph: Graph instance (will use singleton if not provided)
    
    Returns:
        Dictionary with poem and metadata
    """
    # Get graph if not provided
    if graph is None:
        graph = get_poetry_graph()
    
    # ==================== STEP 1: LOAD ROUTE PERSONALITY ====================
    print(f"\n📋 Step 1: Loading personality for {route_id}")
    personality = load_route_personality(route_id)
    
    print(f"   - Name: {personality.get('name', route_id)}")
    print(f"   - Description: {personality.get('description', 'N/A')}")
    print(f"   - Loyalty to canon: {personality.get('loyalty_to_canon', 0.5):.0%}")
    print(f"   - Rebellious mode: {personality.get('rebellious_mode', 'None')}")
    
    
    # ==================== STEP 2: BUILD PROMPT FROM GRAPH ====================
    print(f"\n🔍 Step 2: Querying knowledge graph and building prompt")
    prompt_builder = PromptBuilder(graph)
    
    prompt = prompt_builder.build_prompt_for_route(
        route_id=route_id,
        personality=personality,
        context=context
    )
    
    print(f"   - Graph summary: {graph.get_graph_summary()}")
    print(f"   - Prompt built with personality-driven constraints")
    
    
    # ==================== STEP 3: GENERATE POEM ====================
    print(f"\n✍️  Step 3: Generating poem with Azure OpenAI")
    
    
    client = AzureOpenAI(
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=AZURE_OPENAI_API_KEY,
        api_version=AZURE_OPENAI_API_VERSION
    )
    
    try:
        # For reasoning models like o1-mini, we need different parameters
        if "o1" in AZURE_OPENAI_DEPLOYMENT_NAME.lower():
            response = client.chat.completions.create(
                model=AZURE_OPENAI_DEPLOYMENT_NAME,
                messages=[
                    {
                        "role": "user",
                        "content": f"You are a poet creating distinctive voices for MARTA transit routes. {prompt}"
                    }
                ]
            )
        else:
            response = client.chat.completions.create(
                model=AZURE_OPENAI_DEPLOYMENT_NAME,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a poet creating distinctive voices for MARTA transit routes. Follow the constraints provided exactly."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_completion_tokens=2000  # Increased to allow for reasoning + content
            )
       
        poem_text = response.choices[0].message.content
        if poem_text:
            poem_text = poem_text.strip()
        else:
            poem_text = ""
        print(f"   ✓ Poem generated ({len(poem_text)} characters)")
        
    except Exception as e:
        print(f"   ✗ Generation failed: {e}")
        return {"error": str(e)}
    
    
    # ==================== STEP 4: ANALYZE POEM ====================
    print(f"\n🔬 Step 4: Analyzing poem to extract metadata")
    
    analyzer = PoemAnalyzer()
    
    try:
        metadata = analyzer.analyze_poem(
            poem_text,
            title=f"{personality.get('name', route_id)} - {datetime.now().strftime('%Y-%m-%d')}"
        )
        
        print(f"   ✓ Analysis complete:")
        print(f"     - Themes: {', '.join(metadata['themes'][:3])}")
        print(f"     - Sound devices: {', '.join(metadata['sound_devices'][:3])}")
        print(f"     - Emotions: {', '.join(metadata['emotions'][:2])}")
        
    except Exception as e:
        print(f"   ⚠ Analysis failed: {e}, using defaults")
        metadata = {
            "themes": [],
            "imagery": [],
            "emotions": [],
            "sound_devices": [],
            "structure_metadata": {},
            "sound_metadata": {}
        }
    
    
    # ==================== STEP 5: ADD TO GRAPH ====================
    print(f"\n💾 Step 5: Adding poem to knowledge graph")
    
    poem_id = f"poem_{route_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    graph.add_poem(
        poem_id=poem_id,
        title=f"{personality.get('name', route_id)} - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        text=poem_text,
        route_id=route_id,
        themes=metadata["themes"],
        imagery=metadata["imagery"],
        emotions=metadata["emotions"],
        sound_devices=metadata["sound_devices"],
        structure_metadata=metadata["structure_metadata"],
        sound_metadata=metadata["sound_metadata"],
        metadata={
            "context": context,
            "loyalty_to_canon": personality.get("loyalty_to_canon"),
            "rebellious_mode": personality.get("rebellious_mode")
        }
    )
    
    print(f"   ✓ Poem added with ID: {poem_id}")
    
    
    # ==================== STEP 6: SAVE GRAPH ====================
    print(f"\n💿 Step 6: Saving graph")
    graph.save_graph()
    print(f"   ✓ Graph saved")
    
    
    # ==================== STEP 7: RETURN RESULT ====================
    print(f"\n✅ Generation complete!")
    
    new_summary = graph.get_graph_summary()
    print(f"   Graph now has {new_summary['total_poems']} poems")
    
    return {
        "poem_id": poem_id,
        "route_id": route_id,
        "route_name": personality.get("name", route_id),
        "text": poem_text,
        "metadata": metadata,
        "personality": {
            "loyalty_to_canon": personality.get("loyalty_to_canon"),
            "rebellious_mode": personality.get("rebellious_mode")
        },
        "prompt_used": prompt,  # Useful for debugging
        "context": context
    }


# ==================== DEMONSTRATION ====================

async def demo():
    """
    Demonstrate the complete flow with different route personalities.
    """
    print("=" * 80)
    print("MARTA POETRY GENERATION - COMPLETE DEMO")
    print("=" * 80)
    
    # Initialize graph
    from poetry.graph import initialize_graph
    graph = initialize_graph("data/poetry_graph.json")
    
    print(f"\nStarting graph state: {graph.get_graph_summary()}")
    
    
    # ==================== DEMO 1: LOYAL ROUTE ====================
    print("\n" + "=" * 80)
    print("DEMO 1: LOYAL ROUTE (MARTA Route 5 - High Canon Adherence)")
    print("=" * 80)
    
    result1 = await generate_poem_for_route(
        route_id="MARTA_5",
        context={
            "time_of_day": "morning_rush",
            "location": "Peachtree Street",
            "passenger_count": "high"
        },
        graph=graph
    )
    
    print("\n📖 GENERATED POEM:")
    print("-" * 80)
    if "error" in result1:
        print(f"❌ ERROR: {result1['error']}")
    else:
        print(result1["text"])
    print("-" * 80)
    
    
    # ==================== DEMO 2: REBELLIOUS ROUTE (INVERT) ====================
    print("\n" + "=" * 80)
    print("DEMO 2: REBELLIOUS ROUTE - INVERT MODE (MARTA Route 21)")
    print("=" * 80)
    
    result2 = await generate_poem_for_route(
        route_id="MARTA_21",
        context={
            "time_of_day": "late_night",
            "location": "Memorial Drive",
            "passenger_count": "low"
        },
        graph=graph
    )
    
    print("\n📖 GENERATED POEM:")
    print("-" * 80)
    if "error" in result2:
        print(f"❌ ERROR: {result2['error']}")
    else:
        print(result2["text"])
    print("-" * 80)
    
    
    # ==================== COMPARE APPROACHES ====================
    print("\n" + "=" * 80)
    print("COMPARISON: How Personalities Led to Different Poems")
    print("=" * 80)
    
    print("\nRoute 5 (Loyal):")
    if "error" not in result1:
        print(f"  - Used canonical patterns")
        print(f"  - Themes: {', '.join(result1['metadata']['themes'][:3])}")
        print(f"  - Sounds: {', '.join(result1['metadata']['sound_devices'][:3])}")
    else:
        print(f"  - Generation failed: {result1['error']}")
    
    print("\nRoute 21 (Rebellious - Invert):")
    if "error" not in result2:
        print(f"  - Inverted canonical patterns")
        print(f"  - Themes: {', '.join(result2['metadata']['themes'][:3])}")
        print(f"  - Sounds: {', '.join(result2['metadata']['sound_devices'][:3])}")
    else:
        print(f"  - Generation failed: {result2['error']}")
    
    
    # ==================== FINAL GRAPH STATE ====================
    print("\n" + "=" * 80)
    print("FINAL GRAPH STATE")
    print("=" * 80)
    
    final_summary = graph.get_graph_summary()
    print(f"\nPoems: {final_summary['total_poems']}")
    print(f"Themes: {final_summary['total_themes']}")
    print(f"Sound devices: {final_summary['total_sound_devices']}")
    print(f"Routes contributing: {final_summary['contributing_routes']}")
    
    # Show route statistics
    print("\nRoute Statistics:")
    for route_id in ["MARTA_5", "MARTA_21"]:
        stats = graph.get_route_statistics(route_id)
        if stats["poem_count"] > 0:
            print(f"\n  {route_id}:")
            print(f"    Poems: {stats['poem_count']}")
            print(f"    Top themes: {list(stats['themes'].keys())[:3]}")
            print(f"    Top sounds: {list(stats['sound_devices'].keys())[:3]}")


# ==================== FASTAPI ENDPOINT EXAMPLE ====================

def fastapi_endpoint_example():
    """
    Example of how to use this in a FastAPI endpoint.
    """
    from fastapi import APIRouter, Depends
    from poetry.graph import get_poetry_graph, ExtendedPoetryGraph
    
    router = APIRouter()
    
    @router.post("/api/routes/{route_id}/generate")
    async def generate_poem(
        route_id: str,
        time_of_day: str = None,
        location: str = None,
        graph: ExtendedPoetryGraph = Depends(get_poetry_graph)
    ):
        """
        Generate a poem for a MARTA route.
        
        The route's personality determines how it relates to the poetry canon.
        """
        context = {}
        if time_of_day:
            context["time_of_day"] = time_of_day
        if location:
            context["location"] = location
        
        result = await generate_poem_for_route(
            route_id=route_id,
            context=context,
            graph=graph
        )
        
        return result


if __name__ == "__main__":
    import asyncio
    asyncio.run(demo())
