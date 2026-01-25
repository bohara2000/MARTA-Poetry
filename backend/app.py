from contextlib import asynccontextmanager
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from poetry.graph import initialize_graph, get_poetry_graph, ExtendedPoetryGraph, PoemAnalyzer
from poetry.prompt_builder import PromptBuilder, load_route_personality
from poetry.personality_routes import router as personality_router
from admin_api import router as admin_router
from openai import AzureOpenAI
import csv
import os
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
from config import AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_DEPLOYMENT_NAME, AZURE_OPENAI_API_VERSION
import random

def generate_creative_title(poem_text: str, route_name: str, context: Dict[str, Any] = None) -> str:
    """
    Generate a creative title for a poem based on its content, route, and context.
    
    Args:
        poem_text: The generated poem text
        route_name: The name of the route (e.g., "Route 5 - Peachtree")
        context: Optional context information
        
    Returns:
        Formatted title string in the format "Title\nBy [Route Name]"
    """
    # Extract key imagery and themes from the first few lines of the poem
    lines = poem_text.strip().split('\n')[:3]  # Use first 3 lines for inspiration
    
    # Time-based title templates
    time_titles = {
        'morning_rush': [
            "Dawn's Commute", "First Light Journey", "Morning Pulse", "Sunrise Transit",
            "Early Hours", "Coffee & Rails", "Awakening Streets"
        ],
        'afternoon': [
            "Midday Rhythms", "Afternoon Flow", "Sunlit Passages", "Noon Journey",
            "Between Hours", "City at Rest", "Quiet Transit"
        ],
        'evening_rush': [
            "Homeward Bound", "Evening Exodus", "Twilight Routes", "After Work",
            "Golden Hour Transit", "End of Day", "Dusk Journey"
        ],
        'late_night': [
            "Midnight Runner", "Night Shift", "After Hours", "Nocturne",
            "City Sleeps", "Lone Journey", "Night Transit"
        ]
    }
    
    # Context-based titles
    passenger_titles = {
        'high': ['Crowded Car', 'Rush Hour Symphony', 'Packed Journey', 'Full House'],
        'medium': ['Steady Flow', 'Regular Route', 'Balanced Journey', 'Even Pace'],
        'low': ['Empty Seats', 'Quiet Ride', 'Solitary Journey', 'Sparse Transit']
    }
    
    # Route-specific inspiration (based on route name keywords)
    route_keywords = {
        'peachtree': ['Urban Pulse', 'City Heartbeat', 'Downtown Dreams', 'Concrete Poetry'],
        'memorial': ['Memory Lane', 'Remembered Routes', 'Historical Journey', 'Past & Present'],
        'downtown': ['Metro Pulse', 'City Center', 'Urban Core', 'Central Lines'],
        'airport': ['Sky Connector', 'Terminal Journey', 'Flight Path', 'Departure Point'],
        'north': ['Northbound', 'Upward Journey', 'Northern Routes', 'Heading North'],
        'south': ['Southward', 'Southern Trail', 'Downward Journey', 'Southern Routes'],
        'east': ['Eastbound', 'Rising Sun Route', 'Eastern Trail', 'Morning Path'],
        'west': ['Westbound', 'Setting Sun Route', 'Western Trail', 'Evening Path']
    }
    
    # Try to pick a contextual title first
    title = None
    
    # Time-based title
    if context and context.get('time_of_day'):
        time_key = context['time_of_day']
        if time_key in time_titles:
            title = random.choice(time_titles[time_key])
    
    # If no time-based title, try passenger count
    if not title and context and context.get('passenger_count'):
        passenger_key = context['passenger_count']
        if passenger_key in passenger_titles:
            title = random.choice(passenger_titles[passenger_key])
    
    # If no context title, try route-based
    if not title and route_name:
        route_lower = route_name.lower()
        for keyword, titles in route_keywords.items():
            if keyword in route_lower:
                title = random.choice(titles)
                break
    
    # Fallback to generic poetic titles
    if not title:
        generic_titles = [
            'Transit Dreams', 'Urban Journey', 'City Lines', 'Moving Forward',
            'Route Poetry', 'Street Symphony', 'Public Transit', 'City Pulse',
            'Metro Musings', 'Transit Tales', 'Urban Rhythms', 'Journey Song'
        ]
        title = random.choice(generic_titles)
    
    # Format as "Title\nBy [Route Name]"
    return f"{title}\nBy {route_name}"

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    
    # STARTUP
    graph_path = os.getenv("POETRY_GRAPH_PATH", "data/poetry_graph.json")
    
    try:
        graph = initialize_graph(graph_path)
        summary = graph.get_graph_summary()
        print(f"✓ Poetry graph initialized: {summary}")
    except Exception as e:
        print(f"⚠ Failed to initialize graph: {e}")
        print("  Graph will be created on first use")
    
    yield  # Application runs here
    
    # SHUTDOWN
    try:
        graph = get_poetry_graph()
        graph.save_graph()
        print("✓ Poetry graph saved")
    except Exception as e:
        print(f"⚠ Failed to save graph: {e}")

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(personality_router)
app.include_router(admin_router)

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
    personality = load_route_personality(route_id)
    
    # ==================== STEP 2: BUILD PROMPT FROM GRAPH ====================
    prompt_builder = PromptBuilder(graph)
    
    prompt = prompt_builder.build_prompt_for_route(
        route_id=route_id,
        personality=personality,
        context=context
    )
    
    # ==================== STEP 3: GENERATE POEM ====================
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
            
        if not poem_text:
            return {"error": "Generated poem is empty"}
        
    except Exception as e:
        return {"error": str(e)}
    
    # ==================== STEP 4: ANALYZE POEM ====================
    analyzer = PoemAnalyzer()
    
    # Generate creative title
    route_name = personality.get('name', route_id)
    creative_title = generate_creative_title(poem_text, route_name, context)
    
    try:
        metadata = analyzer.analyze_poem(
            poem_text,
            title=creative_title
        )
        
    except Exception as e:
        print(f"Analysis failed: {e}, using defaults")
        metadata = {
            "themes": [],
            "imagery": [],
            "emotions": [],
            "sound_devices": [],
            "structure_metadata": {},
            "sound_metadata": {}
        }
    
    # ==================== STEP 5: ADD TO GRAPH ====================
    poem_id = f"poem_{route_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    try:
        graph.add_poem(
            poem_id=poem_id,
            title=creative_title,
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
        
        # Save graph
        graph.save_graph()
        
    except Exception as e:
        print(f"Failed to save to graph: {e}")
    
    # ==================== STEP 6: RETURN RESULT ====================
    return {
        "poem_id": poem_id,
        "route_id": route_id,
        "route_name": personality.get("name", route_id),
        "title": creative_title,
        "text": poem_text,
        "metadata": metadata,
        "personality": {
            "loyalty_to_canon": personality.get("loyalty_to_canon"),
            "rebellious_mode": personality.get("rebellious_mode"),
            "description": personality.get("description")
        },
        "context": context
    }

@app.get("/api/poetry")
async def get_poetry(
    route: str, 
    story_influence: float = Query(0.7, ge=0.0, le=1.0), 
    route_type: str = Query('bus', pattern='^(bus|train)$'),
    time_of_day: Optional[str] = Query(None, pattern='^(morning_rush|afternoon|evening_rush|late_night)$'),
    location: Optional[str] = None,
    passenger_count: Optional[str] = Query(None, pattern='^(low|medium|high)$')
):
    """
    Generate a poem based on the route, route type, and story influence.
    
    Args:
        route: Route identifier (e.g., "5", "MARTA_5")
        story_influence: How much the story influences the poem (0.0-1.0)
        route_type: Type of route ('bus' or 'train') 
        time_of_day: Optional context for time
        location: Optional context for location
        passenger_count: Optional context for passenger density
    """
    try:
        # Format route_id consistently
        if not route.startswith("MARTA_"):
            route_id = f"MARTA_{route}"
        else:
            route_id = route
            
        # Build context from parameters
        context = {
            "story_influence": story_influence,
            "route_type": route_type
        }
        
        if time_of_day:
            context["time_of_day"] = time_of_day
        if location:
            context["location"] = location
        if passenger_count:
            context["passenger_count"] = passenger_count
            
        # Generate the poem
        result = await generate_poem_for_route(route_id, context)
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
            
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/route-personality/{route_id}")
async def get_route_personality(route_id: str):
    """
    Get personality information for a specific route.
    
    Args:
        route_id: Route identifier (e.g., "5", "MARTA_5")
    """
    try:
        # Format route_id consistently
        if not route_id.startswith("MARTA_"):
            route_id = f"MARTA_{route_id}"
            
        personality = load_route_personality(route_id)
        
        return {
            "route_id": route_id,
            "name": personality.get("name", route_id),
            "description": personality.get("description", ""),
            "loyalty_to_canon": personality.get("loyalty_to_canon", 0.5),
            "rebellious_mode": personality.get("rebellious_mode"),
            "themes": personality.get("themes", []),
            "voice_style": personality.get("voice_style", ""),
            "inspiration": personality.get("inspiration", "")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/routes")
def get_routes(type: str = Query('bus', enum=['bus', 'train'])):
    """
    Return a list of available bus or train routes from the GTFS feed.
    """
    base_dir = os.path.join(os.path.dirname(__file__), "data", "gtfs")
    routes_path = os.path.join(base_dir, "routes.txt")
    routes = []
    try:
        with open(routes_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # GTFS: route_type 0=tram, 1=subway, 2=rail, 3=bus, 4=ferry, 5=cable, 6=gondola, 7=funicular
                route_type = row.get("route_type", "3")
                if type == 'bus' and route_type == '3':
                    routes.append({
                        "route_id": row.get("route_id"),
                        "route_short_name": row.get("route_short_name"),
                        "route_long_name": row.get("route_long_name")
                    })
                elif type == 'train' and route_type in ['1', '2', '0']:
                    routes.append({
                        "route_id": row.get("route_id"),
                        "route_short_name": row.get("route_short_name"),
                        "route_long_name": row.get("route_long_name")
                    })
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    return {"routes": routes}


@app.get("/")
def root():
    return {"message": "MARTA Poetry API is running."}