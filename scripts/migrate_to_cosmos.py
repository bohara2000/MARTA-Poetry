#!/usr/bin/env python3
"""
Migrate existing JSON data to Cosmos DB containers.

This script:
1. Reads poetry_graph.json and route_personalities.json
2. Transforms data into Cosmos DB schema
3. Inserts into appropriate containers (poems, routes, personalities, graph)
"""

import json
import os
import sys
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List

# Get project root and add backend to path
project_root = Path(__file__).parent.parent
backend_path = project_root / "backend"
sys.path.insert(0, str(backend_path))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv(backend_path / ".env")

from services.cosmos_db_client import (
    upsert_item,
    COSMOS_CONTAINER_POEMS,
    COSMOS_CONTAINER_ROUTES,
    COSMOS_CONTAINER_PERSONALITIES,
    COSMOS_CONTAINER_GRAPH,
)


def sanitize_cosmos_id(id_value: str) -> str:
    """
    Sanitize ID for Cosmos DB compliance.
    Cosmos DB IDs cannot contain: /, \\, ?, #
    """
    if not id_value:
        return f"node_{datetime.now(timezone.utc).timestamp()}"
    
    # Replace illegal characters with underscores
    sanitized = re.sub(r'[/\\?#]', '_', str(id_value))
    
    # Replace spaces with underscores
    sanitized = sanitized.replace(' ', '_')
    
    # Ensure it's not empty or just whitespace
    sanitized = sanitized.strip()
    if not sanitized:
        return f"node_{datetime.now(timezone.utc).timestamp()}"
    
    return sanitized


def load_json_file(filepath: str) -> Dict[str, Any]:
    """Load JSON file."""
    print(f"Loading {filepath}...")
    with open(filepath, "r") as f:
        return json.load(f)


def migrate_poetry_graph(graph_data: Dict[str, Any]) -> None:
    """Migrate poetry graph nodes to Cosmos DB containers."""
    nodes = graph_data.get("nodes", [])
    edges = graph_data.get("links", [])
    
    print(f"\nMigrating {len(nodes)} nodes from poetry graph...")
    
    poems_count = 0
    other_nodes_count = 0
    
    for node in nodes:
        node_type = node.get("type", "unknown")
        original_id = node.get("id", f"node_{other_nodes_count}")
        sanitized_id = sanitize_cosmos_id(original_id)
        
        if node_type == "poem":
            # Migrate poem to poems container
            poem_doc = {
                "id": sanitized_id,
                "type": "poem",
                "title": node.get("title", "Untitled"),
                "text": node.get("text", ""),
                "route_id": node.get("route_id", ""),
                "created_at": node.get("created_at", datetime.now(timezone.utc).isoformat()),
                "metadata": node.get("metadata", {}),
            }
            
            # Add connections/edges - sanitize target IDs too
            connections = [
                sanitize_cosmos_id(edge["target"]) for edge in edges 
                if sanitize_cosmos_id(edge.get("source", "")) == sanitized_id
            ]
            poem_doc["connections"] = connections
            
            upsert_item(poem_doc, COSMOS_CONTAINER_POEMS)
            poems_count += 1
            
        else:
            # Migrate other node types to graph container
            # Create a copy without the original 'id' field to avoid overwriting sanitized ID
            node_data = {k: v for k, v in node.items() if k != 'id'}
            
            graph_doc = {
                "id": sanitized_id,
                "nodeType": node_type,
                **node_data,
            }
            
            # Add connections/edges - sanitize target IDs too
            connections = [
                sanitize_cosmos_id(edge["target"]) for edge in edges 
                if sanitize_cosmos_id(edge.get("source", "")) == sanitized_id
            ]
            graph_doc["connections"] = connections
            
            upsert_item(graph_doc, COSMOS_CONTAINER_GRAPH)
            other_nodes_count += 1
        
        if (poems_count + other_nodes_count) % 100 == 0:
            print(f"  Processed {poems_count + other_nodes_count} nodes...")
    
    print(f"✓ Migrated {poems_count} poems")
    print(f"✓ Migrated {other_nodes_count} other nodes")


def migrate_route_personalities(personalities_data: Dict[str, Any]) -> None:
    """Migrate route personalities to routes and personalities containers."""
    print(f"\nMigrating {len(personalities_data)} route personalities...")
    
    routes_count = 0
    personalities_count = 0
    
    for route_id, personality in personalities_data.items():
        sanitized_route_id = sanitize_cosmos_id(route_id)
        sanitized_personality_id = sanitize_cosmos_id(f"personality_{route_id}")
        
        # Create route document
        route_doc = {
            "id": sanitized_route_id,
            "type": "route",
            "name": personality.get("name", route_id),
            "description": personality.get("description", ""),
            "route_mode": personality.get("route_mode", "bus"),
            "major_stops": personality.get("major_stops", []),
            "personality_id": sanitized_personality_id,
            "metadata": {
                "loyalty_to_canon": personality.get("loyalty_to_canon", 0.5),
                "rebellious_mode": personality.get("rebellious_mode"),
                "sound_preferences": personality.get("sound_preferences", {}),
                "theme_affinities": personality.get("theme_affinities", {}),
            },
        }
        
        upsert_item(route_doc, COSMOS_CONTAINER_ROUTES)
        routes_count += 1
        
        # Create personality document
        personality_doc = {
            "id": sanitized_personality_id,
            "type": "personality",
            "route_id": sanitized_route_id,
            "talent_economy": personality.get("talent_economy", {}),
            "traits": [],
            "metadata": {
                "loyalty_to_canon": personality.get("loyalty_to_canon", 0.5),
                "sound_preferences": personality.get("sound_preferences", {}),
                "theme_affinities": personality.get("theme_affinities", {}),
            },
        }
        
        # Extract traits from talent_economy if available
        if personality.get("talent_economy", {}).get("enabled"):
            te = personality["talent_economy"]
            sympathy = te.get("sympathy_level", 0.5)
            if sympathy > 0.7:
                personality_doc["traits"].append("sympathetic")
            elif sympathy < 0.3:
                personality_doc["traits"].append("detached")
            
            address_mode = te.get("address_mode", "")
            if address_mode:
                personality_doc["traits"].append(address_mode)
        
        upsert_item(personality_doc, COSMOS_CONTAINER_PERSONALITIES)
        personalities_count += 1
        
        if (routes_count + personalities_count) % 20 == 0:
            print(f"  Processed {routes_count} routes and {personalities_count} personalities...")
    
    print(f"✓ Migrated {routes_count} routes")
    print(f"✓ Migrated {personalities_count} personalities")


def main():
    """Main migration function."""
    print("=" * 60)
    print("MARTA Poetry - Cosmos DB Data Migration")
    print("=" * 60)
    
    # Check environment variables
    required_vars = ["COSMOS_ENDPOINT", "COSMOS_KEY", "COSMOS_DATABASE"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"\n❌ Error: Missing environment variables: {', '.join(missing_vars)}")
        print("Please ensure your .env file is configured correctly.")
        sys.exit(1)
    
    # Define file paths
    base_dir = Path(__file__).parent.parent / "backend" / "data"
    poetry_graph_path = base_dir / "poetry_graph.json"
    personalities_path = base_dir / "route_personalities.json"
    
    # Check if files exist
    if not poetry_graph_path.exists():
        print(f"\n❌ Error: {poetry_graph_path} not found")
        sys.exit(1)
    
    if not personalities_path.exists():
        print(f"\n❌ Error: {personalities_path} not found")
        sys.exit(1)
    
    try:
        # Load data
        poetry_graph = load_json_file(str(poetry_graph_path))
        route_personalities = load_json_file(str(personalities_path))
        
        # Migrate data
        migrate_poetry_graph(poetry_graph)
        migrate_route_personalities(route_personalities)
        
        print("\n" + "=" * 60)
        print("✓ Migration completed successfully!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Verify data in Azure Portal → Cosmos DB → Data Explorer")
        print("2. Test queries using the cosmos_db_client module")
        print("3. Update application code to use Cosmos DB instead of JSON files")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
