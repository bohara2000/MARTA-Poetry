import random
from datetime import datetime
from .character_agent import get_route_personality
from .narrative_engine import apply_story_influence
from .prompt_builder import PromptBuilder
from storage.poem_store import PoemStore
from openai import AzureOpenAI
from config import AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_DEPLOYMENT_NAME, AZURE_OPENAI_API_VERSION

endpoint = AZURE_OPENAI_ENDPOINT
model_name = AZURE_OPENAI_DEPLOYMENT_NAME
deployment = AZURE_OPENAI_DEPLOYMENT_NAME
api_version = AZURE_OPENAI_API_VERSION 
subscription_key = AZURE_OPENAI_API_KEY

client = AzureOpenAI(    
    api_key=subscription_key,
    api_version=api_version,
    azure_endpoint=endpoint
)

class RouteAgent:
    def __init__(self, route_id):
        self.route_id = route_id
        self.personality = get_route_personality(route_id)
        self.memory = []  # Stores past poem summaries or metadata
        self.goal = self._set_initial_goal()
        self.store = PoemStore()
        self.prompt_builder = PromptBuilder(None)  # Will use simple implementation
        
        # Extract human-friendly route name
        self.route_name = self.personality.get('name', route_id)
        self.major_stops = self.personality.get('major_stops', [])
        self.route_mode = self.personality.get('route_mode', 'bus')  # bus, train, rail

    def _set_initial_goal(self):
        # Placeholder goal logic—can evolve later
        return f"Inspire riders with the spirit of Route {self.route_id}"

    def receive_message(self, message):
        # Placeholder for future agent communication
        self.memory.append({"type": "message", "content": message, "timestamp": datetime.utcnow().isoformat()})

    def generate_poem(self, story_influence):
        """Generate a poem with narrative constraints based on story_influence."""
        narrative_data = apply_story_influence(self.route_id, self.personality, story_influence)
        
        # Build prompt with narrative constraints
        prompt = self._build_constrained_prompt(narrative_data, story_influence)

        # Customize the system prompt based on agent traits
        alignment = self.personality.get("alignment", "exploratory")
        tone = self.personality.get("tone", "observant")

        system_prompt = (
            f"You are a poetic transit muse for {self.route_name}. "
            f"Your poetic voice is {tone}, shaped by a sense of {alignment}. "
            f"You are a SPECULATIVE POET who transforms {self.route_mode} transit into myth, legend, and alternative realities. "
            f"Use imagery and experience specific to {self.route_mode}s—not generic transit. "
            "You write vivid, rhythm-driven free verse that reimagines the ordinary as extraordinary. "
            "You see hidden ecosystems, alternative cosmologies, and mythological truths in stations, vehicles, and commuters. "
            "Never explain your work—just create the speculative vision. Avoid rhyme unless it happens naturally. "
            "Never mention your route number or route ID directly. Speak in first, second, or third person. "
            "Follow the narrative constraints and emphasized elements provided in the user prompt."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]

        print(f"\n📝 Generating poem for Route {self.route_id} with story_influence={story_influence}")
        print(f"🎯 Narrative Stance: {narrative_data['stance'].upper()}")
        print(f"📌 Emphasized Motifs: {', '.join(narrative_data['emphasized_motifs'][:2])}")
        
        try:
            response = client.chat.completions.create(                
                messages=messages,
                model=deployment,
            )
            poem_text = response.choices[0].message.content
        except Exception as e:
            poem_text = f"Error generating poem: {e}"

        self.store.save_poem(self.route_id, poem_text, story_influence, self.personality)
        self.memory.append({"type": "poem", "content": poem_text, "timestamp": datetime.utcnow().isoformat()})

        return poem_text
    
    def _build_constrained_prompt(self, narrative_data, story_influence):
        """Build a prompt that explicitly includes narrative constraints."""
        stance = narrative_data['stance']
        emphasized_motifs = narrative_data['emphasized_motifs']
        rejected_motifs = narrative_data['rejected_motifs']
        emotional_tone = narrative_data['emotional_tone']
        narrative_fragments = narrative_data['narrative_fragments']
        
        # Build stops/geography context
        stops_context = ""
        if self.major_stops:
            stops_list = ", ".join(self.major_stops[:3])
            stops_context = f"\nYou know these stops intimately: {stops_list}"
        
        # Build mode-specific imagery guidance
        mode_imagery = ""
        if self.route_mode == "bus":
            mode_imagery = """
YOUR VEHICLE & IMAGERY: You are a bus. Use imagery appropriate to buses:
- Diesel and rubber and asphalt
- Hydraulic doors, steering wheels, mirrors
- City blocks and street-level perspective
- Concrete, curbs, intersections, traffic signals
- The faces and bodies of passengers at close range
"""
        elif self.route_mode in ["train", "rail"]:
            mode_imagery = """
YOUR VEHICLE & IMAGERY: You are a train/rail vehicle. Use imagery appropriate to rail:
- Steel rails, overhead lines, third rails
- Tunnels, platforms, station architecture
- The rhythm of wheels on tracks
- Elevation changes and underground passages
- Station names and platform numbers
"""
        
        # Build identity guidance
        identity_guidance = f"""
YOUR IDENTITY:
You are {self.route_name.split(' - ')[1] if ' - ' in self.route_name else self.route_name}.{stops_context}

DO NOT:
- Mention "Route 5" or "MARTA_5" or reference your route number directly
- Use generic transit imagery that doesn't match your mode of operation
- Write about trains if you're a bus, or buses if you're a train

DO:
- Speak in first person ("I carry..."), second person ("you board..."), or third person ("the route flows...")
- Use your actual stops and geography as grounding
- Draw from {self.route_mode}-specific experience
"""
        
        prompt = f"""You are a speculative poet embedded in MARTA's transit system.

As a speculative poet, you:
- Transform mundane transit observations into myth and legend
- Build imagined ecosystems and hidden worlds within the station
- Reinterpret technology, infrastructure, and commuters through fantastical lenses
- Create alternative cosmologies where the ordinary becomes extraordinary
- Write as if you're documenting a reality that exists just beneath the surface

{mode_imagery}

{identity_guidance}

NARRATIVE STANCE: {stance.upper()}
As a speculative poet, you take a {stance} stance toward the surveillance/control systems of urban transit.

EMOTIONAL TONE: {emotional_tone}
Your speculative imagination is filtered through this emotional lens.

KEY MOTIFS TO WEAVE INTO YOUR SPECULATION (transform these through your imaginative lens):
{chr(10).join(f"  - {motif}" for motif in emphasized_motifs)}

NARRATIVE FRAGMENTS TO BUILD UPON (use these as seeds for speculation):
{chr(10).join(f"  - {frag}" for frag in narrative_fragments)}

MOTIFS TO AVOID (these don't fit your speculative vision):
{chr(10).join(f"  - {motif}" for motif in rejected_motifs)}

Write a free verse poem that speculates on hidden realities, alternative ecosystems, and mythological transformations within the transit system. Be vivid, rhythmic, and world-building. Transform the literal into the legendary."""
        
        return prompt

