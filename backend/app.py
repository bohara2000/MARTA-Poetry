from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from poetry.generator import generate_poem

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/poetry")
def get_poetry(route: str, story_influence: float = 0.7):
    """
    Generate a poem based on the route and story influence.
    """
    poem = generate_poem(route, story_influence)
    return {"poem": poem}