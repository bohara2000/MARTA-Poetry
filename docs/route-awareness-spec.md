# Route Awareness Specification

## Goal
Make each generated poem feel anchored to a real MARTA route while preserving speculative voice. Routes should feel like sentient entities embedded in specific neighborhoods. Live data should shape style (tempo, density, tone) rather than literal content.

## Core Principles
- **Grounded + speculative**: real neighborhood references with mythic overlay.
- **Metaphorical first**: prefer metaphorical hints; allow occasional explicit references.
- **Route-locked voice**: each route retains its established personality and sound preferences.
- **Live data influences style**: real-time signals affect pacing, rhythm, and density, not factual narration.

## Route Awareness Contract (Minimums)
Each poem must include:
1. **Local anchors**: 2–3 neighborhood signals per route.
2. **Speculative overlay**: sentient street/city logic mapped onto anchors.
3. **Implicit route identity**: the reader can infer the route without direct route IDs.
4. **Live-style modulation**: style varies with live conditions (even if subtly).

## Anchor Types (Real-World)
Use 2–3 from this list per poem:
- Major stops (from GTFS)
- Neighborhood or corridor names
- Landmarks or institutions
- Street-level textures (markets, schools, hospitals, stadiums)

**Reference mode**:
- 70–90% metaphorical hints
- 10–30% explicit references (one anchor can be named directly)

## Speculative Overlay (Mythic Layer)
Tie anchors to a recurring speculative system:
- Streets as sentient traders (Talent economy)
- Stops as shrines, markets, or courts
- Signals and cameras as watchers or ritual devices
- Passengers as emissaries or vessels

## Live Data Style Modulation (No Literal Mentions Required)
Live signals modify style, not content:

| Signal | Style Effect |
|---|---|
| **Vehicle position / headway** | Line length and stanza count (bunched = short, clipped; smooth = longer, flowing) |
| **Traffic congestion** | Density of consonants/alliteration (congested = harder, tighter) |
| **Weather** | Sound texture (rain = assonance/internal rhyme; clear = alliteration; wind = breathy cadence) |
| **Time of day** | Tone filter (dawn = bright/anticipatory; night = hushed/ritual; rush hour = percussive) |
| **Service alerts** | Structural disruption (line breaks, fragmenting, abrupt turns) |

## Prompt-Level Constraints (Conceptual)
- Use route-specific **major stops** as grounding, but avoid listing them.
- Integrate **2–3 anchor hints** and **1 speculative reinterpretation**.
- Vary pacing and line density based on live signals.
- Avoid generic city imagery that could fit any route.

## Output Guardrails
- **No route IDs** in poem text.
- **No detached abstraction**: at least one concrete place cue must appear.
- **Mode fidelity**: bus imagery for bus routes, rail imagery for rail routes.

## Context Sourcing Decisions
- **Live anchor precedence**: use live anchor when available; fall back to static anchors when not.
- **Live location source**: GTFS-Realtime vehicle positions.
- **Location context**: Mapbox reverse geocoding (temporary).
- **Historical context**: separate source (Wikipedia/Wikidata preferred).
- **Quality control**: manual review of historical snippets at start.
- **Refresh cadence**: once per poem.
- **Latency target**: under 5 seconds total for lookups.
- **Caching**:
	- Reverse-geocode: cache to keep latency under target.
	- Historical context: persistent cache across restarts.
	- Re-fetch per poem with cache as the first lookup layer.
- **Live anchor fields**: capture neighborhood, place name, and POI (use all three with filtering).
	- **POI filtering**: leave open initially; evaluate later.
- **Live signals selected**: vehicle positions and service alerts (alerts emphasized for rail modes).
- **Weather source**: NWS; weather-to-style mapping should be configurable.
- **Time-of-day source**: solar events (sunrise/sunset).
- **Traffic source**: use GTFS-RT `congestion_level` if provided; otherwise Mapbox traffic.
- **Traffic impact**: modulates rhythm and density only.

## Recommended Route Metadata Extension
Add to each route personality:
- `neighborhood_anchors`: list of 6–10 real anchors
- `speculative_roles`: 2–4 mythic archetypes (e.g., trader, oracle, warden)
- `metaphor_bias`: ratio for metaphor vs explicit references

## Acceptance Criteria
A poem is “route-aware” if:
- A reader can identify or strongly infer the route corridor or neighborhood.
- At least 2 local anchors are present (metaphorical or explicit).
- The poem’s pacing or sonic texture changes when live signals change.

## Next Steps (When Implementing)
1. Expand route personality data with neighborhood anchors.
2. Add live signal inputs to prompt builder as **style modifiers**.
3. Create tests that verify anchor presence and style shifts.
