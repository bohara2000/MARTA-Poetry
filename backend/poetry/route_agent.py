import random
from datetime import datetime
from .character_agent import get_route_personality
from .narrative_engine import apply_story_influence
from .prompt_builder import build_poetry_prompt
from storage.poem_store import PoemStore
from openai import AzureOpenAI
from config import AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_DEPLOYMENT_NAME

endpoint = AZURE_OPENAI_ENDPOINT
model_name = AZURE_OPENAI_DEPLOYMENT_NAME
deployment = AZURE_OPENAI_DEPLOYMENT_NAME
api_version = "2024-12-01-preview"
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

    def _set_initial_goal(self):
        # Placeholder goal logic—can evolve later
        return f"Inspire riders with the spirit of Route {self.route_id}"

    def receive_message(self, message):
        # Placeholder for future agent communication
        self.memory.append({"type": "message", "content": message, "timestamp": datetime.utcnow().isoformat()})

    def generate_poem(self, story_influence):
        narrative_data = apply_story_influence(self.route_id, self.personality, story_influence)
        prompt = build_poetry_prompt(self.route_id, self.personality, narrative_data, story_influence)

        # Customize the system prompt based on agent traits
        alignment = self.personality["alignment"]
        tone = self.personality["tone"]

        system_prompt = (
            f"You are a poetic transit muse for Route {self.route_id}. "
            f"Your poetic voice is {tone}, shaped by a sense of {alignment}. "
            "You write vivid, rhythm-driven, speculative free verse poems inspired by urban transit and local myth. "
            "Never explain your work—just create the poem. Avoid rhyme unless it happens naturally."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]

        print("prompt:", prompt)
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

