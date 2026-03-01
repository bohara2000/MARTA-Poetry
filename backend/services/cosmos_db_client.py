import os
from typing import Any, Dict, List, Optional

from azure.cosmos import CosmosClient

COSMOS_ENDPOINT = os.getenv("COSMOS_ENDPOINT")
COSMOS_KEY = os.getenv("COSMOS_KEY")
COSMOS_DATABASE = os.getenv("COSMOS_DATABASE")
COSMOS_CONTAINER = os.getenv("COSMOS_CONTAINER", "poems")

# Explicit container names for the deployed schema
COSMOS_CONTAINER_POEMS = os.getenv("COSMOS_CONTAINER_POEMS", "poems")
COSMOS_CONTAINER_ROUTES = os.getenv("COSMOS_CONTAINER_ROUTES", "routes")
COSMOS_CONTAINER_PERSONALITIES = os.getenv("COSMOS_CONTAINER_PERSONALITIES", "personalities")
COSMOS_CONTAINER_GRAPH = os.getenv("COSMOS_CONTAINER_GRAPH", "graph")

if not COSMOS_ENDPOINT or not COSMOS_KEY or not COSMOS_DATABASE:
    raise ValueError(
        "Missing Cosmos DB configuration. Set COSMOS_ENDPOINT, COSMOS_KEY, and COSMOS_DATABASE."
    )

client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
database = client.get_database_client(COSMOS_DATABASE)


def get_container_client(container_name: Optional[str] = None):
    resolved_container = container_name or COSMOS_CONTAINER
    return database.get_container_client(resolved_container)

# Example query stub
def get_items(query: str, container_name: Optional[str] = None) -> List[Dict[str, Any]]:
    container = get_container_client(container_name)
    return list(container.query_items(
        query=query,
        enable_cross_partition_query=True
    ))

# Example add stub
def add_item(item: Dict[str, Any], container_name: Optional[str] = None) -> Dict[str, Any]:
    container = get_container_client(container_name)
    container.create_item(body=item)
    return item

# Update an item by id
def update_item(
    item_id: str,
    partition_key: str,
    updated_fields: Dict[str, Any],
    container_name: Optional[str] = None,
) -> Dict[str, Any]:
    container = get_container_client(container_name)
    item = container.read_item(item=item_id, partition_key=partition_key)
    item.update(updated_fields)
    container.replace_item(item=item_id, body=item)
    return item


def upsert_item(item: Dict[str, Any], container_name: Optional[str] = None) -> Dict[str, Any]:
    container = get_container_client(container_name)
    return container.upsert_item(body=item)

# Remove an item by id
def remove_item(item_id: str, partition_key: str, container_name: Optional[str] = None) -> None:
    container = get_container_client(container_name)
    container.delete_item(item=item_id, partition_key=partition_key)
