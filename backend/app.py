from contextlib import asynccontextmanager
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from poetry.graph import initialize_graph, get_poetry_graph
# from poetry.generator import generate_poem
from poetry.personality_routes import router as personality_router
import csv
import os

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

@app.get("/api/poetry")
def get_poetry(route: str, story_influence: float = 0.7, route_type: str = 'bus'):
    """
    Generate a poem based on the route, route type, and story influence.
    """
    # poem = generate_poem(graph, route, story_influence, route_type) 
    poem = f"This is a placeholder poem for route {route} with influence {story_influence} and type {route_type}."   
    return {"poem": poem}


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