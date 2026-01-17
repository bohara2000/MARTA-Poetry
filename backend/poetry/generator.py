from .route_agent import RouteAgent

# Optional: Cache agents in memory for reuse
route_agents = {}

def generate_poem(route, story_influence):
    if route not in route_agents:
        route_agents[route] = RouteAgent(route)
    agent = route_agents[route]
    return agent.generate_poem(story_influence)
