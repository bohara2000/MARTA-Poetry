"""
FastAPI Integration for Poetry Knowledge Graph

This module provides FastAPI dependencies and utilities for integrating
the poetry graph into your API endpoints.
"""

from typing import Optional
from contextlib import contextmanager
from fastapi import Depends, HTTPException
from functools import lru_cache
import os

# Singleton instance
_graph_instance: Optional['ExtendedPoetryGraph'] = None


def initialize_graph(graph_path: str) -> 'ExtendedPoetryGraph':
    """
    Initialize the global graph instance.
    
    Args:
        graph_path: Path to the graph JSON file
    
    Returns:
        The initialized graph instance
    """
    global _graph_instance
    
    # Import here to avoid circular imports
    from .extended_poetry_graph import ExtendedPoetryGraph
    
    _graph_instance = ExtendedPoetryGraph(graph_path)
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