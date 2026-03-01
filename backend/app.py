from contextlib import asynccontextmanager
from fastapi import FastAPI, Query, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from poetry.graph import initialize_graph, get_poetry_graph, ExtendedPoetryGraph, PoemAnalyzer
from poetry.prompt_builder import PromptBuilder, load_route_personality
from services.context_service import ContextService
from services.context_contract import validate_context_payload
from poetry.personality_routes import router as personality_router
from admin_api import router as admin_router, get_graph
from openai import AzureOpenAI
from audio_service import get_audio_service
import csv
import json
import os
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List
from config import (
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_DEPLOYMENT_NAME,
    AZURE_OPENAI_API_VERSION,
    AZURE_OPENAI_API_KEY_TITLES,
    AZURE_OPENAI_ENDPOINT_TITLES,
    AZURE_OPENAI_DEPLOYMENT_NAME_TITLES,
    AZURE_OPENAI_API_VERSION_TITLES,
)
import random


# ==================== PYDANTIC MODELS ====================

class AudioGenerationRequest(BaseModel):
    """Request model for audio generation."""
    route: str
    poem_text: str
    voice: Optional[str] = None
    speed: float = 0.9
    poem_id: Optional[str] = None


class PoemGenerationRequest(BaseModel):
    """Request model for poem generation."""
    route: str
    story_influence: float = 0.7
    route_type: str = "bus"
    time_of_day: Optional[str] = None
    location: Optional[str] = None
    passenger_count: Optional[str] = None
    include_audio: bool = False
    # Source poem metadata for "Generate Similar Poem" feature
    source_poem_id: Optional[str] = None
    source_themes: Optional[List[str]] = None
    source_imagery: Optional[List[str]] = None
    source_emotions: Optional[List[str]] = None


# ==================== HELPER FUNCTIONS ====================

def generate_creative_title(
    poem_text: str,
    route_name: str,
    context: Dict[str, Any] = None,
    metadata: Dict[str, Any] = None
) -> str:
    """
    Generate a creative title for a poem using AI analysis of the poem's content.
    
    Args:
        poem_text: The generated poem text
        route_name: The name of the route (e.g., "Route 5 - Peachtree")
        context: Optional context information
        
    Returns:
        Formatted title string in the format "Title\nBy [Route Name]"
    """
    def _format_token(value: str) -> str:
        return value.replace("_", " ").strip().title()

    def _best_anchor(ctx: Dict[str, Any]) -> Optional[str]:
        if not ctx:
            return None
        live_anchor = ctx.get("live_anchor") if isinstance(ctx.get("live_anchor"), dict) else {}
        for key in ("neighborhood", "place", "poi"):
            value = live_anchor.get(key)
            if isinstance(value, str) and value.strip():
                return value
        fallback_anchors = ctx.get("fallback_anchors") if isinstance(ctx.get("fallback_anchors"), list) else []
        for anchor in fallback_anchors:
            if isinstance(anchor, str) and anchor.strip():
                return anchor
        return None

    def _fallback_title(meta: Dict[str, Any], ctx: Dict[str, Any]) -> str:
        imagery = [_format_token(i) for i in (meta or {}).get("imagery", []) if isinstance(i, str)]
        themes = [_format_token(t) for t in (meta or {}).get("themes", []) if isinstance(t, str)]
        emotions = [_format_token(e) for e in (meta or {}).get("emotions", []) if isinstance(e, str)]
        anchor = _best_anchor(ctx)

        primary = imagery[0] if imagery else (themes[0] if themes else None)
        secondary = None
        if anchor:
            secondary = _format_token(anchor)
        elif emotions:
            secondary = emotions[0]
        elif len(themes) > 1:
            secondary = themes[1]

        if primary and secondary:
            title = f"{primary} {secondary}"
        elif primary:
            title = primary
        else:
            title = "City Echo"

        words = title.split()
        if len(words) > 5:
            title = " ".join(words[:5])
        return title

    try:
        # Initialize Azure OpenAI client for title generation
        client = AzureOpenAI(
            azure_endpoint=AZURE_OPENAI_ENDPOINT_TITLES,
            api_key=AZURE_OPENAI_API_KEY_TITLES,
            api_version=AZURE_OPENAI_API_VERSION_TITLES
        )
        
        themes_hint = ", ".join((metadata or {}).get("themes", [])[:4]) if metadata else ""
        imagery_hint = ", ".join((metadata or {}).get("imagery", [])[:4]) if metadata else ""
        emotions_hint = ", ".join((metadata or {}).get("emotions", [])[:3]) if metadata else ""
        anchor_hint = _best_anchor(context)

        analysis_prompt = f"""Generate ONE short, evocative title that matches this poem.

    POEM:
    {poem_text}

    Helpful hints (use at least one concrete noun if present):
    - Anchors: {anchor_hint or 'none'}
    - Themes: {themes_hint or 'none'}
    - Imagery: {imagery_hint or 'none'}
    - Emotions: {emotions_hint or 'none'}

    Requirements:
    - 2-5 words max
    - Must reflect actual content, imagery, or mood
    - Avoid generic transit words (route, transit, metro, city, journey, urban)
    - Must stand alone as a title

    Respond with ONLY the title, nothing else. No quotes, no explanation."""
        
        # Call the API to generate the title
        response = client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT_NAME_TITLES,
            messages=[
                {
                    "role": "user",
                    "content": analysis_prompt
                }
            ],
            max_completion_tokens=50
        )
        
        # Extract the title from the response
        title = response.choices[0].message.content.strip()
        
        # Clean up the title (remove quotes if present)
        title = title.strip('"\'')
        
        # Check if title is empty and raise error if so
        if not title or title.isspace():
            raise ValueError("AI returned empty title")

        generic_markers = {
            "route",
            "transit",
            "metro",
            "city",
            "urban",
            "journey",
            "lines",
            "poetry",
            "pulse",
            "musings",
            "tales",
            "song",
        }
        if any(marker in title.lower() for marker in generic_markers):
            title = _fallback_title(metadata or {}, context or {})
        
        # Format as "Title\nBy [Route Name]"
        return f"{title}\nBy {route_name}"
        
    except Exception as e:
        # Fallback to template-based approach if AI generation fails
        print(f"⚠ AI title generation failed: {type(e).__name__}: {e}")
        
        # Fallback generic titles
        fallback_titles = [
            'Transit Dreams', 'Urban Journey', 'City Lines', 'Moving Forward',
            'Route Poetry', 'Street Symphony', 'Public Transit', 'City Pulse',
            'Metro Musings', 'Transit Tales', 'Urban Rhythms', 'Journey Song',
            'Rails & Reverie', 'Metro Pulse', "Commuter's Song", 'Urban Poetry'
        ]
        title = _fallback_title(metadata or {}, context or {})
        return f"{title}\nBy {route_name}"

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    
    # STARTUP
    # Try to initialize graph from Cosmos DB; fall back to JSON file
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

# Configure CORS based on environment
# Development: allow localhost dev server (port 5173)
# Production: allow Static Web Apps frontend domain
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
cors_origins = [origin.strip() for origin in cors_origins]  # Remove whitespace

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(personality_router)
app.include_router(admin_router)

context_service = ContextService()


@app.get("/api/context")
async def get_context(route_id: str = Query(...)):
    payload = context_service.build_context(route_id)
    is_valid, errors = validate_context_payload(payload)
    if not is_valid:
        raise HTTPException(status_code=500, detail={"errors": errors})
    return JSONResponse(payload)

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

    # Always include live context for route awareness
    base_context: Dict[str, Any] = context or {}
    try:
        live_context = context_service.build_context(route_id)
    except Exception as e:
        print(f"⚠️ Failed to build live context: {e}")
        live_context = {}

    if live_context:
        context = {**live_context, **base_context}
    else:
        context = base_context

    # Extract story_influence from context if available
    story_influence = None
    if context and "story_influence" in context:
        story_influence = context["story_influence"]
        print(f"📊 Story Influence from context: {story_influence}")
    
    prompt = prompt_builder.build_prompt_for_route(
        route_id=route_id,
        personality=personality,
        context=context,
        story_influence=story_influence
    )
    
    # Log the prompt for debugging
    print(f"\n{'='*80}")
    print(f"🎯 GENERATED PROMPT FOR {route_id}")
    print(f"Story Influence: {story_influence}")
    print(f"{'='*80}")
    print(prompt)
    print(f"{'='*80}\n")
    
    # ==================== STEP 3: GENERATE POEM ====================
    client = AzureOpenAI(
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=AZURE_OPENAI_API_KEY,
        api_version=AZURE_OPENAI_API_VERSION
    )
    
    try:
        poem_text = ""
        for attempt in range(3):
            # Start with 3000 tokens for reasoning models, increase to 5000 on retries
            max_completion_tokens = 3000 if attempt == 0 else 5000
            print(f"🧮 Attempt {attempt + 1}/3: max_completion_tokens={max_completion_tokens}")
            print(f"🧮 Prompt length (chars): {len(prompt)}")
            # For reasoning models like o1-mini or o4, we need different parameters
            if "o1" in AZURE_OPENAI_DEPLOYMENT_NAME.lower() or "o4" in AZURE_OPENAI_DEPLOYMENT_NAME.lower():
                response = client.chat.completions.create(
                    model=AZURE_OPENAI_DEPLOYMENT_NAME,
                    messages=[
                        {
                            "role": "user",
                            "content": f"You are a poet creating distinctive voices for MARTA transit routes. {prompt}"
                        }
                    ],
                    max_completion_tokens=max_completion_tokens
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
                    max_completion_tokens=max_completion_tokens
                )

            choice = response.choices[0]
            poem_text = choice.message.content
            if poem_text:
                poem_text = poem_text.strip()
            else:
                poem_text = ""

            # Log token usage for reasoning models
            if hasattr(response, 'usage'):
                usage = response.usage
                print(f"📊 Token usage - Prompt: {usage.prompt_tokens}, Completion: {usage.completion_tokens}")
                if hasattr(usage, 'completion_tokens_details') and usage.completion_tokens_details:
                    details = usage.completion_tokens_details
                    if hasattr(details, 'reasoning_tokens') and details.reasoning_tokens:
                        print(f"📊 Reasoning tokens: {details.reasoning_tokens}")

            if poem_text:
                print(f"✅ Poem generated successfully on attempt {attempt + 1}")
                break

            finish_reason = getattr(choice, "finish_reason", None)
            print(f"⚠️ Empty poem response on attempt {attempt + 1}/3, retrying...")
            print(f"🔎 Empty response details: finish_reason={finish_reason}")
            if attempt < 2:  # Don't sleep on last attempt
                await asyncio.sleep(0.5)

        if not poem_text:
            return {"error": "Generated poem is empty"}

    except Exception as e:
        return {"error": str(e)}
    
    # ==================== STEP 4: ANALYZE POEM ====================
    analyzer = PoemAnalyzer()

    route_name = personality.get('name', route_id)

    try:
        metadata = analyzer.analyze_poem(poem_text)
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

    # Generate creative title using analysis hints
    creative_title = generate_creative_title(poem_text, route_name, context, metadata)
    
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
                "prompt": prompt,
                "loyalty_to_canon": personality.get("loyalty_to_canon"),
                "rebellious_mode": personality.get("rebellious_mode"),
                "audio_files": []  # Initialize empty audio files list
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
        "prompt": prompt,
        "metadata": metadata,
        "personality": {
            "loyalty_to_canon": personality.get("loyalty_to_canon"),
            "rebellious_mode": personality.get("rebellious_mode"),
            "description": personality.get("description")
        },
        "context": context
    }

@app.post("/api/poetry")
async def generate_poetry(
    request: PoemGenerationRequest,
    graph: ExtendedPoetryGraph = Depends(get_graph)
):
    """
    Generate a poem based on the route, route type, and story influence.
    
    Args:
        request: PoemGenerationRequest with route, story_influence, etc.
        graph: Poetry graph instance
    """
    try:
        # Format route_id consistently
        if not request.route.startswith("MARTA_"):
            route_id = f"MARTA_{request.route}"
        else:
            route_id = request.route
            
        # Build context from parameters
        context = {
            "story_influence": request.story_influence,
            "route_type": request.route_type
        }
        
        if request.time_of_day:
            context["time_of_day"] = request.time_of_day
        if request.location:
            context["location"] = request.location
        if request.passenger_count:
            context["passenger_count"] = request.passenger_count
        
        # Add source poem metadata if provided (for "Generate Similar Poem")
        if request.source_poem_id:
            context["source_poem_id"] = request.source_poem_id
        if request.source_themes:
            context["source_themes"] = request.source_themes
        if request.source_imagery:
            context["source_imagery"] = request.source_imagery
        if request.source_emotions:
            context["source_emotions"] = request.source_emotions
            
        # Generate the poem
        result = await generate_poem_for_route(route_id, context, graph)
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        # Generate audio if requested
        if request.include_audio and "text" in result:
            try:
                audio_service = get_audio_service()
                audio_result = audio_service.generate_audio(
                    poem_text=result["text"],
                    route_id=route_id
                )
                if audio_result.get("success"):
                    result["audio"] = audio_result
            except Exception as audio_error:
                print(f"⚠️  Audio generation failed (continuing without it): {str(audio_error)}")
                # Don't fail the entire request if audio generation fails
            
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/poetry")
async def get_poetry(
    route: str, 
    story_influence: float = Query(0.7, ge=0.0, le=1.0), 
    route_type: str = Query('bus', pattern='^(bus|train)$'),
    time_of_day: Optional[str] = Query(None, pattern='^(morning_rush|afternoon|evening_rush|late_night)$'),
    location: Optional[str] = None,
    passenger_count: Optional[str] = Query(None, pattern='^(low|medium|high)$'),
    include_audio: bool = Query(False, description="Whether to generate audio for the poem"),
    graph: ExtendedPoetryGraph = Depends(get_graph)
):
    """
    Generate a poem based on the route, route type, and story influence.
    
    This endpoint supports GET requests for backward compatibility.
    
    Args:
        route: Route identifier (e.g., "5", "MARTA_5")
        story_influence: How much the story influences the poem (0.0-1.0)
        route_type: Type of route ('bus' or 'train') 
        time_of_day: Optional context for time
        location: Optional context for location
        passenger_count: Optional context for passenger density
        include_audio: Whether to generate audio for the poem
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
        result = await generate_poem_for_route(route_id, context, graph)
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        # Generate audio if requested
        if include_audio and "text" in result:
            try:
                audio_service = get_audio_service()
                audio_result = audio_service.generate_audio(
                    poem_text=result["text"],
                    route_id=route_id
                )
                if audio_result.get("success"):
                    result["audio"] = audio_result
            except Exception as audio_error:
                print(f"⚠️  Audio generation failed (continuing without it): {str(audio_error)}")
                # Don't fail the entire request if audio generation fails
            
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
    Return a list of available bus or train routes from the GTFS feed that have personalities configured.
    Only routes with personality configurations are eligible for poem generation.
    """
    # Load configured personalities from Cosmos DB or JSON file
    personality_keys = set()
    
    # Try Cosmos DB first
    cosmos_endpoint = os.getenv("COSMOS_ENDPOINT")
    if cosmos_endpoint:
        try:
            from services.cosmos_db_client import (
                get_items,
                COSMOS_CONTAINER_ROUTES,
            )
            routes_docs = get_items("SELECT * FROM c", container_name=COSMOS_CONTAINER_ROUTES)
            personality_keys = {route.get("id") for route in routes_docs if route.get("id")}
        except Exception as e:
            print(f"Warning: Failed to load personalities from Cosmos DB: {e}")
    
    # Fall back to JSON file if Cosmos DB not available
    if not personality_keys:
        personalities_path = os.path.join(os.path.dirname(__file__), "data", "route_personalities.json")
        try:
            if os.path.exists(personalities_path):
                with open(personalities_path, 'r') as f:
                    personalities = json.load(f)
                    personality_keys = set(personalities.keys())
        except Exception as e:
            print(f"Warning: Failed to load personalities from JSON: {e}")
    
    base_dir = os.path.join(os.path.dirname(__file__), "data", "gtfs")
    routes_path = os.path.join(base_dir, "routes.txt")
    routes = []
    try:
        with open(routes_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                gtfs_route_id = row.get("route_id")
                short_name = row.get("route_short_name")
                
                # Check if either MARTA_<gtfs_id> or MARTA_<short_name> is in personalities
                has_personality = (
                    f"MARTA_{gtfs_route_id}" in personality_keys or
                    f"MARTA_{short_name}" in personality_keys
                )
                
                if not has_personality:
                    continue
                
                # GTFS: route_type 0=tram, 1=subway, 2=rail, 3=bus, 4=ferry, 5=cable, 6=gondola, 7=funicular
                route_type = row.get("route_type", "3")
                if type == 'bus' and route_type == '3':
                    routes.append({
                        "route_id": gtfs_route_id,
                        "route_short_name": short_name,
                        "route_long_name": row.get("route_long_name")
                    })
                elif type == 'train' and route_type in ['1', '2', '0']:
                    routes.append({
                        "route_id": gtfs_route_id,
                        "route_short_name": short_name,
                        "route_long_name": row.get("route_long_name")
                    })
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    return {"routes": routes}


@app.get("/")
def root():
    return {"message": "MARTA Poetry API is running."}


# ==================== AUDIO ENDPOINTS ====================

@app.post("/api/audio/generate")
async def generate_poem_audio(request: AudioGenerationRequest, graph: ExtendedPoetryGraph = Depends(get_graph)):
    """
    Generate audio from poem text using OpenAI TTS.
    
    Args:
        request: AudioGenerationRequest with route, poem_text, voice, speed, poem_id
        
    Returns:
        Audio generation result with URL and metadata
    """
    try:
        # Format route_id consistently
        if not request.route.startswith("MARTA_"):
            route_id = f"MARTA_{request.route}"
        else:
            route_id = request.route
        
        audio_service = get_audio_service()
        result = audio_service.generate_audio(
            poem_text=request.poem_text,
            route_id=route_id,
            voice=request.voice,
            speed=request.speed
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to generate audio"))
        
        # Add audio file to poem metadata if poem_id is provided
        if request.poem_id:
            try:
                # Get audio filename from result or construct it
                audio_file = result.get("audio_file", "")
                if audio_file:
                    audio_filename = audio_file.split("/")[-1]  # Get just the filename
                    
                    # Update poem metadata
                    if graph.graph.has_node(request.poem_id):
                        poem_data = graph.graph.nodes[request.poem_id]
                        metadata = poem_data.get("metadata", {})
                        audio_files = metadata.get("audio_files", [])
                        
                        if audio_filename not in audio_files:
                            audio_files.append(audio_filename)
                        
                        metadata["audio_files"] = audio_files
                        graph.graph.nodes[request.poem_id]["metadata"] = metadata
                        graph.save_graph()
                        
                        # Include updated audio_files in response
                        result["audio_files"] = audio_files
                        result["metadata"] = metadata
                        print(f"✅ Updated audio metadata for {request.poem_id}: {audio_files}")
                    else:
                        print(f"⚠️  Poem node not found: {request.poem_id}")
            except Exception as e:
                print(f"⚠️  Failed to update poem metadata with audio: {e}")
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/audio/{audio_id}/{voice}")
async def get_poem_audio(audio_id: str, voice: str):
    """
    Retrieve generated audio file for a poem.
    
    Args:
        audio_id: The audio identifier (e.g., MARTA_27339_d4495d21)
        voice: The voice used for generation
        
    Returns:
        Audio file (MP3) or error response
    """
    try:
        audio_service = get_audio_service()
        
        # Construct the expected filename
        filename = f"{audio_id}_{voice}.mp3"
        audio_path = audio_service.audio_dir / filename
        
        if not audio_path.exists():
            raise HTTPException(status_code=404, detail=f"Audio file not found: {filename}")
        
        return FileResponse(
            path=audio_path,
            media_type="audio/mpeg",
            filename=filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/audio/voices")
async def get_available_voices():
    """
    Get list of available voices for audio generation.
    
    Returns:
        List of available voice names
    """
    try:
        audio_service = get_audio_service()
        return {
            "voices": audio_service.list_available_voices(),
            "default": audio_service.default_voice,
            "description": "Select engaging voices for poetry narration"
        }
    except ValueError as e:
        # OPENAI_API_KEY not set
        raise HTTPException(status_code=500, detail=f"OpenAI configuration error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get voices: {str(e)}")


@app.get("/api/audio/check/{poem_id}")
async def check_poem_audio(poem_id: str):
    """
    Check if audio files exist for a poem.
    
    Args:
        poem_id: The poem ID
        
    Returns:
        List of available audio files (voice names) for this poem
    """
    try:
        from pathlib import Path
        import os
        
        # Get audio directory - try multiple possible paths
        possible_paths = [
            Path("audio"),
            Path(__file__).parent / "audio",
            Path.cwd() / "audio",
        ]
        
        audio_dir = None
        for path in possible_paths:
            if path.exists():
                audio_dir = path
                break
        
        if audio_dir is None:
            return {"audio_files": [], "debug": "audio directory not found"}
        
        # Extract route_id from poem_id (format: poem_MARTA_27446_20260131_185640)
        # We need to find audio files for this route
        parts = poem_id.split("_")
        if len(parts) >= 3 and parts[0] == "poem" and parts[1] == "MARTA":
            # Reconstruct route_id like MARTA_27446
            route_portion = f"{parts[1]}_{parts[2]}"
            
            # Find all audio files that match this route
            available_audio = []
            for audio_file in audio_dir.glob("*.mp3"):
                filename = audio_file.name
                if route_portion in filename:
                    # Extract voice (last underscore-separated part before .mp3)
                    parts = filename.replace(".mp3", "").rsplit("_", 1)
                    if len(parts) == 2:
                        voice = parts[1]
                        available_audio.append({
                            "voice": voice,
                            "filename": filename
                        })
            
            return {"audio_files": available_audio}
        
        return {"audio_files": []}
    except Exception as e:
        print(f"Error checking audio: {e}")
        import traceback
        traceback.print_exc()
        return {"audio_files": [], "error": str(e)}


@app.delete("/api/audio/{poem_id}")
async def delete_poem_audio(poem_id: str, voice: Optional[str] = Query(None)):
    """
    Delete audio file(s) for a poem.
    
    Args:
        poem_id: The poem identifier
        voice: Optional specific voice. If None, deletes all voices
        
    Returns:
        Deletion status
    """
    try:
        audio_service = get_audio_service()
        result = audio_service.delete_audio(poem_id, voice)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))