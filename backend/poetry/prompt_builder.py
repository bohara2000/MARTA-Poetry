def build_poetry_prompt(route, personality, narrative_data, story_influence):
    """
    Returns the user content for the chat message that feeds route-specific traits into the LLM.
    """

    details = f"""
Route Number: {route}
Tone: {personality['tone']}
Alignment: {personality['alignment']}
Quirks: {', '.join(personality['quirks'])}
Story Influence (0-1): {story_influence}
Narrative Stance: {narrative_data['stance']}
Emotional Relationship: {narrative_data['emotional_tone']}
"""

    # Build motifs section from structured narrative data
    emphasized_motifs = "\n".join(f"- {m}" for m in narrative_data['emphasized_motifs'])
    narrative_fragments = "\n".join(f"- {f}" for f in narrative_data['narrative_fragments'])
    
    if narrative_data['rejected_motifs']:
        rejected_motifs = "\n".join(f"- {m}" for m in narrative_data['rejected_motifs'])
        motif_section = f"Emphasized Motifs:\n{emphasized_motifs}\n\nRejected Themes:\n{rejected_motifs}\n\nNarrative Fragments:\n{narrative_fragments}"
    else:
        motif_section = f"Emphasized Motifs:\n{emphasized_motifs}\n\nNarrative Fragments:\n{narrative_fragments}"

    instructions = (
        "\nWrite a free verse poem based on the above details. "
        "You should subtly incorporate the story motifs into the mood and structure of the poem. "
        "Do not mention the words 'alignment' or 'quirks' directly—let them guide the tone and behavior of the route like a character. "
        "Avoid rhyme unless it arises naturally. Be vivid, strange, and grounded in the spirit of transit."
    )

    prompt = f"{details}\nStory Motifs:\n{motif_section}{instructions}"

    return prompt.strip()
