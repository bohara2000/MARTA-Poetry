"""
Route Personality Management API

FastAPI endpoints for viewing and modifying route personalities.
Add this to your backend.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
import json
from pathlib import Path

router = APIRouter(prefix="/api/personalities", tags=["personalities"])

# Path to personalities file
PERSONALITIES_FILE = Path("data/route_personalities.json")


# ==================== PYDANTIC MODELS ====================

class RoutePersonality(BaseModel):
    """Model for a single route personality."""
    name: str = Field(..., description="Display name of the route")
    description: str = Field(..., description="Character description")
    loyalty_to_canon: float = Field(
        ..., 
        ge=0.0, 
        le=1.0, 
        description="0.0 (rebel) to 1.0 (traditionalist)"
    )
    rebellious_mode: Optional[str] = Field(
        None,
        description="null, 'ignore', 'invert', or 'create_new'"
    )
    sound_preferences: Dict[str, float] = Field(
        default_factory=dict,
        description="Sound device preferences (0.0 to 1.0)"
    )
    theme_affinities: Dict[str, float] = Field(
        default_factory=dict,
        description="Theme affinities (0.0 to 1.0)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Route 5 - Peachtree",
                "description": "Downtown's pulse, alliterative and alive",
                "loyalty_to_canon": 0.9,
                "rebellious_mode": None,
                "sound_preferences": {
                    "alliteration": 0.95,
                    "repetition": 0.8,
                    "internal_rhyme": 0.4
                },
                "theme_affinities": {
                    "urban_life": 0.95,
                    "morning": 0.8
                }
            }
        }


class PersonalitiesResponse(BaseModel):
    """Response model for listing all personalities."""
    personalities: Dict[str, RoutePersonality]
    total: int


class UpdatePersonalityRequest(BaseModel):
    """Request model for updating a personality."""
    personality: RoutePersonality


# ==================== HELPER FUNCTIONS ====================

def load_personalities() -> Dict[str, Dict[str, Any]]:
    """Load personalities from JSON file."""
    if not PERSONALITIES_FILE.exists():
        return {}
    
    with open(PERSONALITIES_FILE, 'r') as f:
        return json.load(f)


def save_personalities(personalities: Dict[str, Dict[str, Any]]) -> None:
    """Save personalities to JSON file."""
    # Ensure data directory exists
    PERSONALITIES_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    with open(PERSONALITIES_FILE, 'w') as f:
        json.dump(personalities, f, indent=2)


def get_available_sound_devices() -> List[str]:
    """Get list of available sound devices."""
    return [
        "alliteration",
        "assonance",
        "consonance",
        "end_rhyme",
        "internal_rhyme",
        "slant_rhyme",
        "repetition",
        "anaphora",
        "onomatopoeia"
    ]


def get_available_themes() -> List[str]:
    """Get list of common themes."""
    return [
        "urban_life",
        "morning",
        "evening",
        "night",
        "transition",
        "isolation",
        "hope",
        "darkness",
        "truth",
        "labor",
        "routine",
        "peace",
        "fatigue",
        "memory"
    ]


# ==================== API ENDPOINTS ====================

@router.get("/", response_model=PersonalitiesResponse)
async def list_personalities():
    """
    Get all route personalities.
    """
    personalities = load_personalities()
    
    return PersonalitiesResponse(
        personalities=personalities,
        total=len(personalities)
    )


@router.get("/{route_id}", response_model=RoutePersonality)
async def get_personality(route_id: str):
    """
    Get a specific route's personality.
    """
    personalities = load_personalities()
    
    if route_id not in personalities:
        raise HTTPException(
            status_code=404,
            detail=f"Route {route_id} not found"
        )
    
    return RoutePersonality(**personalities[route_id])


@router.put("/{route_id}", response_model=RoutePersonality)
async def update_personality(
    route_id: str,
    request: UpdatePersonalityRequest
):
    """
    Update a route's personality.
    """
    personalities = load_personalities()
    
    # Convert Pydantic model to dict
    personality_dict = request.personality.model_dump()
    
    # Update
    personalities[route_id] = personality_dict
    
    # Save
    save_personalities(personalities)
    
    return request.personality


@router.post("/{route_id}", response_model=RoutePersonality, status_code=201)
async def create_personality(
    route_id: str,
    request: UpdatePersonalityRequest
):
    """
    Create a new route personality.
    """
    personalities = load_personalities()
    
    if route_id in personalities:
        raise HTTPException(
            status_code=400,
            detail=f"Route {route_id} already exists. Use PUT to update."
        )
    
    # Convert Pydantic model to dict
    personality_dict = request.personality.model_dump()
    
    # Create
    personalities[route_id] = personality_dict
    
    # Save
    save_personalities(personalities)
    
    return request.personality


@router.delete("/{route_id}")
async def delete_personality(route_id: str):
    """
    Delete a route's personality.
    """
    personalities = load_personalities()
    
    if route_id not in personalities:
        raise HTTPException(
            status_code=404,
            detail=f"Route {route_id} not found"
        )
    
    del personalities[route_id]
    save_personalities(personalities)
    
    return {"message": f"Deleted personality for {route_id}"}


@router.get("/options/sound-devices")
async def get_sound_device_options():
    """
    Get list of available sound devices for dropdowns.
    """
    return {"sound_devices": get_available_sound_devices()}


@router.get("/options/themes")
async def get_theme_options():
    """
    Get list of available themes for dropdowns.
    """
    return {"themes": get_available_themes()}


@router.get("/options/rebellious-modes")
async def get_rebellious_mode_options():
    """
    Get list of available rebellious modes.
    """
    return {
        "modes": [
            {"value": None, "label": "None (Balanced)", "description": "Mix of canonical and fresh"},
            {"value": "ignore", "label": "Ignore Canon", "description": "Use rare/underutilized elements"},
            {"value": "invert", "label": "Invert Canon", "description": "Canonical themes with opposite treatment"},
            {"value": "create_new", "label": "Create New", "description": "Pioneer unexplored territory"}
        ]
    }


# ==================== BULK OPERATIONS ====================

@router.post("/bulk/import")
async def bulk_import_personalities(personalities: Dict[str, RoutePersonality]):
    """
    Import multiple personalities at once.
    Useful for seeding or restoring from backup.
    """
    existing = load_personalities()
    
    # Convert all to dicts
    for route_id, personality in personalities.items():
        if isinstance(personality, RoutePersonality):
            existing[route_id] = personality.model_dump()
        else:
            existing[route_id] = personality
    
    save_personalities(existing)
    
    return {
        "message": f"Imported {len(personalities)} personalities",
        "total": len(existing)
    }


@router.get("/bulk/export")
async def bulk_export_personalities():
    """
    Export all personalities for backup.
    """
    return load_personalities()


# ==================== VALIDATION ====================

@router.post("/{route_id}/validate")
async def validate_personality(route_id: str, personality: RoutePersonality):
    """
    Validate a personality configuration without saving.
    Returns validation result and any warnings.
    """
    warnings = []
    
    # Check loyalty vs rebellious_mode consistency
    if personality.loyalty_to_canon > 0.7 and personality.rebellious_mode:
        warnings.append(
            "High loyalty (>0.7) with rebellious_mode set - these may conflict"
        )
    
    # Check if preferences sum makes sense
    total_sound_pref = sum(personality.sound_preferences.values())
    if total_sound_pref > 5.0:
        warnings.append(
            f"Sound preferences sum to {total_sound_pref:.1f} - consider normalizing"
        )
    
    total_theme_aff = sum(personality.theme_affinities.values())
    if total_theme_aff > 5.0:
        warnings.append(
            f"Theme affinities sum to {total_theme_aff:.1f} - consider normalizing"
        )
    
    # Check for extreme values
    if personality.loyalty_to_canon < 0.1:
        warnings.append(
            "Very low loyalty (<0.1) - route will be extremely rebellious"
        )
    
    if personality.loyalty_to_canon > 0.95:
        warnings.append(
            "Very high loyalty (>0.95) - route may lack variety"
        )
    
    return {
        "valid": True,
        "warnings": warnings,
        "route_id": route_id,
        "personality_type": _get_personality_type(personality)
    }


def _get_personality_type(personality: RoutePersonality) -> str:
    """Classify personality type for UI."""
    if personality.loyalty_to_canon > 0.8:
        return "Traditionalist"
    elif personality.rebellious_mode == "invert":
        return "Contrarian"
    elif personality.rebellious_mode == "ignore":
        return "Explorer"
    elif personality.rebellious_mode == "create_new":
        return "Pioneer"
    else:
        return "Balanced"


# ==================== USAGE IN app.py ====================

"""
To use this in your app.py:

from poetry.personality_routes import router as personality_router

app.include_router(personality_router)
"""
