# Canonical Poetry Collection extracted from core poems
# These are actual themes, imagery, and emotions that the analyzer detects
MOCK_POETRY_COLLECTION = {
    "central_themes": [
        "surveillance",
        "urban_life",
        "control_and_authority",
        "isolation",
        "the_uncanny",
        "interconnected_ecosystem",
        "order_vs_disorder",
        "commodification",
        "data_technology",
        "silence_vs_noise"
    ],
    "core_motifs": [
        "pigeons", "camera networks", "station rules", "mechanical roaches",
        "rats", "third rail", "K-9-2s", "slime molds", "silent station",
        "train", "headphones", "dusty platform", "plants", "pollen",
        "bees hitting wind chimes", "dark cars", "claws", "regurgitated scraps",
        "Ultraviolet Market", "bizarre mathematics", "ghettobird", "polar vortex",
        "high-hat tap-tap", "fork in asphalt", "superhighways", "rhinestone equations",
        "camera-hives"
    ],
    "core_emotions": [
        "tense", "claustrophobic", "suspenseful", "unsettled", "guarded",
        "uneasy", "curiosity", "cynicism", "unease"
    ],
    "narrative_fragments": [
        "the pigeons are polite, but firm",
        "the system does not give a damn",
        "this is a networked earth",
        "they are part of an ecosystem",
        "full of surprises",
        "monitoring and repairing",
        "resurrecting the jumpers",
        "the rules of the station are simple"
    ],
    "emotional_register": "tense, guarded, curious, cynical, unsettled"
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
    route_name = personality.get('name', route)
    route_description = personality.get('description', '')
    loyalty = personality.get('loyalty_to_canon', 0.5)
    
    if stance == "supporting":
        # Embrace surveillance, control, technology themes
        emphasized_motifs = [
            "camera networks", "surveillance", "pigeons", "K-9-2s",
            "station rules", "data_technology", "control_and_authority"
        ]
        rejected_motifs = ["unease", "resistance", "chaos"]
        emotional_tone = "tense, guarded, watchful, observant of systems"
        narrative_fragments = [
            "the system does not give a damn",
            "monitoring and repairing",
            "the rules of the station are simple",
            "pigeons are polite but firm"
        ]
        
    elif stance == "opposing":
        # Resist surveillance, seek freedom, embrace chaos
        emphasized_motifs = [
            "escape routes", "hidden spaces", "freedom from rules",
            "chaos", "disorder", "the_uncanny", "resistance"
        ]
        rejected_motifs = ["surveillance", "control", "authority", "pigeons", "K-9-2s"]
        emotional_tone = "defiant, unsettled, uncontrollable, seeking autonomy"
        narrative_fragments = [
            "the system does not give a damn",
            "full of surprises",
            "this is a networked earth that won't be contained"
        ]
        
    else:  # ambivalent
        # Caught between acceptance and resistance
        emphasized_motifs = [
            "mechanical roaches", "rats", "third rail", "slime molds",
            "interconnected_ecosystem", "order_vs_disorder",
            "isolation", "the_uncanny"
        ]
        rejected_motifs = []  # Accept some of both sides
        emotional_tone = "uncertain, conflicted, claustrophobic, curious about hidden systems"
        narrative_fragments = [
            "they are part of an ecosystem",
            "monitoring and repairing",
            "full of surprises",
            "resurrecting the jumpers"
        ]
    
    return {
        "stance": stance,
        "story_influence_level": story_influence,
        "emphasized_motifs": emphasized_motifs,
        "rejected_motifs": rejected_motifs,
        "emotional_tone": emotional_tone,
        "narrative_fragments": narrative_fragments,
        "route_personality": {
            "name": route_name,
            "description": route_description,
            "loyalty": loyalty
        }
    }
