# Mock poetry collection - replace with actual source later
MOCK_POETRY_COLLECTION = {
    "central_themes": [
        "urban surveillance and observation",
        "movement as freedom and control", 
        "community formation in transit spaces",
        "technology mediating human connection",
        "the politics of public space"
    ],
    "core_motifs": [
        "watching eyes", "mechanical birds", "voices in motion", 
        "windows as frames", "rhythmic cycles", "intersections",
        "barriers and passages", "collective breath"
    ],
    "narrative_fragments": [
        "the city breathes through its arteries of motion",
        "each journey is a negotiation with power",
        "we are witnessed by glass and steel",
        "transit reveals who belongs where",
        "movement creates temporary communities"
    ],
    "emotional_register": "observant, political, communal"
}

def get_narrative_stance(story_influence):
    """
    Determine route's stance toward the central narrative.
    """
    if story_influence <= 0.3:
        return "opposing"
    elif story_influence >= 0.7:
        return "supporting" 
    else:
        return "ambivalent"

def apply_story_influence(route, personality, story_influence):
    """
    Creates narrative relationship data showing how route personality interacts with central poetry collection.

    Args:
        route (str): The route identifier.
        personality (dict): The personality traits for the route.
        story_influence (float): Route's relationship to narrative (0.0=opposes, 1.0=supports).

    Returns:
        dict: Structured data about route's narrative stance and emphasized elements.
    """
    collection = MOCK_POETRY_COLLECTION
    stance = get_narrative_stance(story_influence)
    
    # Route's personality affects how it relates to narrative
    alignment = personality['alignment']
    tone = personality['tone']
    quirks = personality['quirks']
    
    if stance == "supporting":
        emphasized_motifs = collection["core_motifs"][:3]  # Embrace core motifs
        rejected_motifs = []
        emotional_tone = f"{tone} but harmonious with urban observation"
        narrative_fragments = collection["narrative_fragments"][:2]
        
    elif stance == "opposing":
        emphasized_motifs = ["freedom from surveillance", "escape routes", "hidden spaces"]
        rejected_motifs = collection["core_motifs"][:2]  # Reject surveillance themes
        emotional_tone = f"{tone} but defiant toward observation"
        narrative_fragments = ["this route refuses to be catalogued", "movement without witness"]
        
    else:  # ambivalent
        emphasized_motifs = collection["core_motifs"][1:3]  # Selective engagement
        rejected_motifs = [collection["core_motifs"][0]]  # Partial rejection
        emotional_tone = f"{tone} but conflicted about visibility"
        narrative_fragments = ["sometimes watched, sometimes free"]
    
    return {
        "stance": stance,
        "story_influence_level": story_influence,
        "emphasized_motifs": emphasized_motifs,
        "rejected_motifs": rejected_motifs,
        "emotional_tone": emotional_tone,
        "narrative_fragments": narrative_fragments,
        "route_personality": {
            "alignment": alignment,
            "tone": tone,
            "quirks": quirks
        }
    }
