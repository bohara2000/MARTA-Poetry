"""
FastAPI Integration for Poetry Knowledge Graph

This module provides FastAPI dependencies and utilities for integrating
the poetry graph into your API endpoints.
"""

from typing import Optional
from fastapi import Depends, HTTPException
from functools import lru_cache
import os

from poetry_graph import PoetryGraph


# Singleton instance of the graph
_graph_instance: Optional[PoetryGraph] = None


def get_graph_path() -> str:
    """
    Get the path to the graph file from environment variable or use default.
    """
    return os.getenv("POETRY_GRAPH_PATH", "data/poetry_graph.json")


@lru_cache()
def get_poetry_graph() -> PoetryGraph:
    """
    Dependency that provides the poetry graph instance.
    This creates a singleton that's shared across all requests.
    
    Usage in FastAPI endpoints:
        @app.get("/poems/{poem_id}")
        def get_poem(poem_id: str, graph: PoetryGraph = Depends(get_poetry_graph)):
            return graph.get_poem(poem_id)
    """
    global _graph_instance
    
    if _graph_instance is None:
        graph_path = get_graph_path()
        _graph_instance = PoetryGraph(graph_path)
    
    return _graph_instance


def initialize_graph(graph_path: Optional[str] = None) -> PoetryGraph:
    """
    Initialize the graph on application startup.
    Call this in your FastAPI app's startup event.
    
    Example:
        @app.on_event("startup")
        async def startup_event():
            graph = initialize_graph("data/poetry_graph.json")
            logger.info(f"Loaded graph with {graph.get_graph_summary()}")
    """
    global _graph_instance
    
    path = graph_path or get_graph_path()
    _graph_instance = PoetryGraph(path)
    
    return _graph_instance


def save_graph_state(graph: PoetryGraph = Depends(get_poetry_graph)) -> None:
    """
    Save the current state of the graph.
    Call this periodically or on shutdown.
    
    Example:
        @app.on_event("shutdown")
        async def shutdown_event():
            graph = get_poetry_graph()
            graph.save_graph()
    """
    graph.save_graph()


class GraphManager:
    """
    Context manager for graph operations that ensures saving after changes.
    
    Usage:
        with GraphManager() as graph:
            graph.add_poem(...)
            # Graph is automatically saved on exit
    """
    
    def __init__(self, graph: Optional[PoetryGraph] = None):
        self.graph = graph or get_poetry_graph()
    
    def __enter__(self) -> PoetryGraph:
        return self.graph
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:  # Only save if no exception occurred
            self.graph.save_graph()
        return False  # Don't suppress exceptions
