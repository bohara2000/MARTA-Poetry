"""
FastAPI Integration for Poetry Knowledge Graph

This module provides FastAPI dependencies and utilities for integrating
the poetry graph into your API endpoints.

Supports both Cosmos DB and JSON file-based graphs.
"""

from typing import Optional
from contextlib import contextmanager
from fastapi import Depends, HTTPException
from functools import lru_cache
import os

# Singleton instance
_graph_instance: Optional['ExtendedPoetryGraph'] = None


def initialize_graph(graph_path: Optional[str] = None) -> 'ExtendedPoetryGraph':
    """
    Initialize the global graph instance.
    
    Supports two modes:
    1. Cosmos DB (if COSMOS_ENDPOINT env var is set): Loads from cloud
    2. JSON file (if graph_path provided): Loads from local file
    
    Args:
        graph_path: Path to the graph JSON file (optional, for backward compatibility)
    
    Returns:
        The initialized graph instance
    """
    global _graph_instance
    
    # Import here to avoid circular imports
    from .extended_poetry_graph import ExtendedPoetryGraph
    
    # Check if we should use Cosmos DB
    cosmos_endpoint = os.getenv("COSMOS_ENDPOINT")
    
    if cosmos_endpoint:
        # Use Cosmos DB
        print("Initializing graph from Cosmos DB...")
        _graph_instance = ExtendedPoetryGraph(cosmos_db_mode=True)
        # If Cosmos DB returned no poems, fall back to JSON file
        if _graph_instance.get_summary().get("total_poems", 0) == 0:
            print("⚠️  Cosmos DB returned no poems. Attempting fallback to JSON file...")
            fallback_path = graph_path or "data/poetry_graph.json"
            try:
                print(f"Initializing graph from fallback JSON: {fallback_path}...")
                _graph_instance = ExtendedPoetryGraph(graph_path=fallback_path)
                print(f"✓ Loaded {_graph_instance.get_summary().get('total_poems', 0)} poems from JSON fallback")
            except Exception as e:
                print(f"⚠️  Fallback JSON load failed: {e}")
    elif graph_path:
        # Fall back to JSON file
        print(f"Initializing graph from {graph_path}...")
        _graph_instance = ExtendedPoetryGraph(graph_path=graph_path)
    else:
        # Initialize empty graph
        print("Initializing empty graph (no data source provided)...")
        _graph_instance = ExtendedPoetryGraph()
    
    return _graph_instance


def get_poetry_graph() -> 'ExtendedPoetryGraph':
    """
    Get the global graph instance.
    
    This is used as a FastAPI dependency:
    
    @app.get("/api/graph/summary")
    async def get_summary(graph: ExtendedPoetryGraph = Depends(get_poetry_graph)):
        return graph.get_graph_summary()
    
    Returns:
        The graph instance
    
    Raises:
        RuntimeError: If graph hasn't been initialized
    """
    if _graph_instance is None:
        raise RuntimeError(
            "Poetry graph not initialized. "
            "Call initialize_graph() in your app startup event."
        )
    return _graph_instance


@contextmanager
def GraphManager():
    """
    Context manager for graph operations with automatic saving.
    
    Usage:
        with GraphManager() as graph:
            graph.add_poem(...)
        # Graph is automatically saved on successful exit
    """
    graph = get_poetry_graph()
    try:
        yield graph
        graph.save_graph()
    except Exception as e:
        # Don't save if there was an error
        raise e