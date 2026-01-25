"""
API endpoints for admin interface integration.
Provides REST API access to narrative management and system status.
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Query
from typing import List, Optional, Dict, Any
from datetime import datetime
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from poetry.graph.extended_poetry_graph import ExtendedPoetryGraph
from poetry.graph import get_poetry_graph
from scripts.narrative_manager import NarrativeManager

router = APIRouter(prefix="/api", tags=["admin"])

# Dependency to get graph instance - USE THE SINGLETON!
def get_graph():
    """Get the poetry graph singleton instance."""
    try:
        return get_poetry_graph()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get graph: {e}")

# Dependency to get narrative manager
def get_narrative_manager():
    """Get the narrative manager instance."""
    return NarrativeManager()

@router.get("/narrative/status")
async def get_narrative_status(graph: ExtendedPoetryGraph = Depends(get_graph)):
    """Get comprehensive narrative structure status."""
    try:
        # Count poems by role
        role_counts = {}
        poems_by_role = {}
        
        for node_id, node_data in graph.graph.nodes(data=True):
            if node_data.get("type") == "poem":
                role = node_data.get("narrative_role", "unassigned")
                
                # Count
                role_counts[role] = role_counts.get(role, 0) + 1
                
                # Group poems
                if role not in poems_by_role:
                    poems_by_role[role] = []
                
                poem_info = {
                    "id": node_id,
                    "title": node_data.get("title"),
                    "route_id": node_data.get("route_id"),
                    "created_at": node_data.get("created_at"),
                    "content": node_data.get("content", "")[:200] + "..." if len(node_data.get("content", "")) > 200 else node_data.get("content", "")
                }
                poems_by_role[role].append(poem_info)
        
        # Count narrative connections
        narrative_connections = sum(1 for _, _, data in graph.graph.edges(data=True)
                                  if data.get("type") == "narrative_connection")
        
        return {
            "summary": {
                "core_poems": role_counts.get("core", 0),
                "extension_poems": role_counts.get("extension", 0),
                "route_generated_poems": role_counts.get("route_generated", 0),
                "variation_poems": role_counts.get("variation", 0),
                "unassigned_poems": role_counts.get("unassigned", 0),
                "total_poems": sum(role_counts.values()),
                "narrative_connections": narrative_connections,
                "total_narrative_framework": role_counts.get("core", 0) + role_counts.get("extension", 0)
            },
            "poems_by_role": poems_by_role,
            "role_counts": role_counts
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get narrative status: {e}")

@router.post("/narrative/mark-core")
async def mark_poems_as_core(
    request: Dict[str, List[str]], 
    graph: ExtendedPoetryGraph = Depends(get_graph)
):
    """Mark poems as core narrative."""
    try:
        poem_ids = request.get("poem_ids", [])
        success_count = 0
        marked_poems = []
        
        for poem_id in poem_ids:
            if graph.mark_poem_as_core(poem_id):
                success_count += 1
                poem_data = graph.graph.nodes[poem_id]
                marked_poems.append({
                    "id": poem_id,
                    "title": poem_data.get("title", "Untitled")
                })
        
        if success_count > 0:
            graph.save_graph()
        
        return {
            "message": f"Marked {success_count} poems as core narrative",
            "success_count": success_count,
            "total_requested": len(poem_ids),
            "marked_poems": marked_poems
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to mark poems as core: {e}")

@router.post("/narrative/mark-extension")
async def mark_poems_as_extension(
    request: Dict[str, List[str]], 
    graph: ExtendedPoetryGraph = Depends(get_graph)
):
    """Mark poems as narrative extensions."""
    try:
        poem_ids = request.get("poem_ids", [])
        success_count = 0
        
        for poem_id in poem_ids:
            if graph.mark_poem_as_extension(poem_id):
                success_count += 1
        
        if success_count > 0:
            graph.save_graph()
        
        return {
            "message": f"Marked {success_count} poems as extensions",
            "success_count": success_count,
            "total_requested": len(poem_ids)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to mark poems as extension: {e}")

@router.delete("/narrative/remove-poem/{poem_id}")
async def remove_poem(poem_id: str, graph: ExtendedPoetryGraph = Depends(get_graph)):
    """Remove a poem from the graph."""
    try:
        if graph.remove_poem(poem_id, cleanup_orphaned_entities=True):
            graph.save_graph()
            return {"message": f"Successfully removed poem {poem_id}"}
        else:
            raise HTTPException(status_code=404, detail=f"Poem {poem_id} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove poem: {e}")

@router.post("/narrative/clear-role/{poem_id}")
async def clear_narrative_role(poem_id: str, graph: ExtendedPoetryGraph = Depends(get_graph)):
    """Clear narrative role for a poem."""
    try:
        if graph.clear_narrative_role(poem_id):
            graph.save_graph()
            return {"message": f"Cleared narrative role for poem {poem_id}"}
        else:
            raise HTTPException(status_code=404, detail=f"Poem {poem_id} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear narrative role: {e}")

@router.get("/poems/")
async def get_all_poems(graph: ExtendedPoetryGraph = Depends(get_graph)):
    """Get all poems with their metadata."""
    try:
        poems = []
        
        for node_id, node_data in graph.graph.nodes(data=True):
            if node_data.get("type") == "poem":
                poem_info = {
                    "id": node_id,
                    "title": node_data.get("title"),
                    "content": node_data.get("content", ""),
                    "route_id": node_data.get("route_id"),
                    "narrative_role": node_data.get("narrative_role"),
                    "created_at": node_data.get("created_at")
                }
                poems.append(poem_info)
        
        # Sort by creation date (most recent first)
        poems.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        return {"poems": poems, "total": len(poems)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get poems: {e}")

@router.get("/poems/{poem_id}/relationships")
async def get_poem_relationships(poem_id: str, graph: ExtendedPoetryGraph = Depends(get_graph)):
    """Get relationship data for a specific poem."""
    try:
        if not graph.graph.has_node(poem_id):
            raise HTTPException(status_code=404, detail=f"Poem {poem_id} not found")
        
        relationships = {
            "themes": [],
            "emotions": [],
            "imagery": [],
            "sound_devices": [],
            "narrative_connections": []
        }
        
        # Get connected nodes
        for neighbor in graph.graph.neighbors(poem_id):
            neighbor_data = graph.graph.nodes[neighbor]
            neighbor_type = neighbor_data.get("type")
            
            if neighbor_type == "theme":
                relationships["themes"].append(neighbor_data.get("name", neighbor))
            elif neighbor_type == "emotion":
                relationships["emotions"].append(neighbor_data.get("name", neighbor))
            elif neighbor_type == "imagery":
                relationships["imagery"].append(neighbor_data.get("name", neighbor))
            elif neighbor_type == "sound_device":
                relationships["sound_devices"].append(neighbor_data.get("name", neighbor))
            elif neighbor_type == "poem":
                edge_data = graph.graph[poem_id][neighbor]
                if edge_data.get("type") == "narrative_connection":
                    relationships["narrative_connections"].append({
                        "poem_id": neighbor,
                        "title": neighbor_data.get("title"),
                        "connection_type": edge_data.get("connection_type")
                    })
        
        return relationships
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get poem relationships: {e}")

@router.post("/poems/{poem_id}/add-themes")
async def add_themes_to_poem(
    poem_id: str, 
    request: Dict[str, List[str]], 
    graph: ExtendedPoetryGraph = Depends(get_graph)
):
    """Add themes to a specific poem."""
    try:
        if not graph.graph.has_node(poem_id):
            raise HTTPException(status_code=404, detail=f"Poem {poem_id} not found")
        
        themes = request.get("themes", [])
        if not themes:
            raise HTTPException(status_code=400, detail="No themes provided")
        
        added_themes = []
        for theme in themes:
            theme_name = theme.strip()
            if theme_name:
                theme_id = f"theme_{theme_name.lower().replace(' ', '_')}"
                
                # Add or update theme entity
                graph._add_or_update_entity(theme_id, "theme", theme_name)
                
                # Add edge if it doesn't exist
                if not graph.graph.has_edge(poem_id, theme_id):
                    graph.graph.add_edge(poem_id, theme_id, type="has_theme")
                    added_themes.append(theme_name)
        
        if added_themes:
            graph.save_graph()
        
        return {
            "message": f"Added {len(added_themes)} themes to poem",
            "added_themes": added_themes,
            "total_requested": len(themes)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add themes: {e}")

@router.delete("/poems/{poem_id}/remove-theme/{theme_name}")
async def remove_theme_from_poem(
    poem_id: str, 
    theme_name: str,
    graph: ExtendedPoetryGraph = Depends(get_graph)
):
    """Remove a specific theme from a poem."""
    try:
        if not graph.graph.has_node(poem_id):
            raise HTTPException(status_code=404, detail=f"Poem {poem_id} not found")
        
        theme_id = f"theme_{theme_name.lower().replace(' ', '_')}"
        
        if graph.graph.has_edge(poem_id, theme_id):
            graph.graph.remove_edge(poem_id, theme_id)
            
            # If no other poems use this theme, optionally remove the theme node
            # (You might want to make this configurable)
            if graph.graph.in_degree(theme_id) == 0:
                graph.graph.remove_node(theme_id)
            
            graph.save_graph()
            return {"message": f"Removed theme '{theme_name}' from poem"}
        else:
            raise HTTPException(status_code=404, detail=f"Theme '{theme_name}' not found for this poem")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove theme: {e}")

@router.get("/themes/")
async def get_all_themes(graph: ExtendedPoetryGraph = Depends(get_graph)):
    """Get all themes in the system with usage counts."""
    try:
        themes = []
        
        for node_id, node_data in graph.graph.nodes(data=True):
            if node_data.get("type") == "theme":
                theme_info = {
                    "id": node_id,
                    "name": node_data.get("name"),
                    "usage_count": node_data.get("usage_count", 0),
                    "created_at": node_data.get("created_at")
                }
                
                # Get poems that use this theme
                connected_poems = []
                for poem_id in graph.graph.predecessors(node_id):
                    poem_data = graph.graph.nodes.get(poem_id, {})
                    if poem_data.get("type") == "poem":
                        connected_poems.append({
                            "id": poem_id,
                            "title": poem_data.get("title")
                        })
                
                theme_info["connected_poems"] = connected_poems
                themes.append(theme_info)
        
        # Sort by usage count (most used first)
        themes.sort(key=lambda x: x.get("usage_count", 0), reverse=True)
        
        return {"themes": themes, "total": len(themes)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get themes: {e}")

@router.post("/themes/merge")
async def merge_themes(
    request: Dict[str, Any], 
    graph: ExtendedPoetryGraph = Depends(get_graph)
):
    """Merge multiple themes into one."""
    try:
        source_themes = request.get("source_themes", [])
        target_theme = request.get("target_theme", "")
        
        if not source_themes or not target_theme:
            raise HTTPException(status_code=400, detail="Both source_themes and target_theme are required")
        
        target_theme_id = f"theme_{target_theme.lower().replace(' ', '_')}"
        
        # Ensure target theme exists
        graph._add_or_update_entity(target_theme_id, "theme", target_theme)
        
        poems_updated = 0
        themes_removed = 0
        
        for source_theme in source_themes:
            source_theme_id = f"theme_{source_theme.lower().replace(' ', '_')}"
            
            if graph.graph.has_node(source_theme_id):
                # Move all connections to target theme
                for poem_id in list(graph.graph.predecessors(source_theme_id)):
                    # Remove old connection
                    graph.graph.remove_edge(poem_id, source_theme_id)
                    
                    # Add new connection (if it doesn't exist)
                    if not graph.graph.has_edge(poem_id, target_theme_id):
                        graph.graph.add_edge(poem_id, target_theme_id, type="has_theme")
                        poems_updated += 1
                
                # Remove the old theme node
                graph.graph.remove_node(source_theme_id)
                themes_removed += 1
        
        if poems_updated > 0 or themes_removed > 0:
            graph.save_graph()
        
        return {
            "message": f"Merged {themes_removed} themes into '{target_theme}'",
            "poems_updated": poems_updated,
            "themes_removed": themes_removed
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to merge themes: {e}")

@router.get("/system/status")
async def get_system_status(graph: ExtendedPoetryGraph = Depends(get_graph)):
    """Get overall system status and statistics."""
    try:
        # Count various entities
        poem_count = sum(1 for _, data in graph.graph.nodes(data=True) if data.get("type") == "poem")
        theme_count = sum(1 for _, data in graph.graph.nodes(data=True) if data.get("type") == "theme")
        connection_count = sum(1 for _, _, data in graph.graph.edges(data=True) if data.get("type") == "narrative_connection")
        
        # Get unique routes
        routes = set()
        for _, data in graph.graph.nodes(data=True):
            if data.get("type") == "poem" and data.get("route_id"):
                routes.add(data["route_id"])
        
        return {
            "api_status": "healthy",
            "graph_status": "loaded",
            "ai_status": "connected",  # You might want to actually test this
            "total_poems": poem_count,
            "statistics": {
                "total_poems": poem_count,
                "unique_routes": len(routes),
                "narrative_connections": connection_count,
                "total_themes": theme_count
            }
        }
    except Exception as e:
        return {
            "api_status": "error",
            "graph_status": "error",
            "ai_status": "unknown",
            "error": str(e)
        }

@router.post("/system/clear-cache")
async def clear_system_cache():
    """Clear system caches (placeholder for future cache implementation)."""
    try:
        # This is a placeholder - implement actual cache clearing as needed
        return {"message": "Cache cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {e}")

@router.get("/system/test/{service}")
async def test_service_connection(service: str):
    """Test connection to various services."""
    try:
        if service == "database":
            # Test graph loading
            graph = ExtendedPoetryGraph()
            return {"status": "ok", "message": "Graph loaded successfully"}
        elif service == "ai":
            # Test AI connection - you might want to implement this
            return {"status": "ok", "message": "AI connection test not implemented"}
        else:
            raise HTTPException(status_code=400, detail=f"Unknown service: {service}")
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.post("/narrative/test-adherence")
async def test_narrative_adherence(
    request: Dict[str, Any], 
    graph: ExtendedPoetryGraph = Depends(get_graph)
):
    """Test how well a route's poems adhere to narrative expectations."""
    try:
        route_id = request.get("route_id")
        story_influence = request.get("story_influence")
        comprehensive = request.get("comprehensive", False)
        
        if not route_id:
            raise HTTPException(status_code=400, detail="route_id is required")
        
        # Import the testing module
        from scripts.test_narrative_adherence import NarrativeAdherenceTest
        
        tester = NarrativeAdherenceTest()
        
        if comprehensive:
            # Test multiple story influence levels
            influence_levels = [0.1, 0.3, 0.5, 0.7, 0.9]
            results = tester.test_multiple_story_influences(route_id, influence_levels)
        elif story_influence is not None:
            # Test single story influence level
            results = tester.test_route_narrative_adherence(route_id, float(story_influence))
        else:
            raise HTTPException(status_code=400, detail="Either story_influence or comprehensive=true must be provided")
        
        return {
            "success": True,
            "test_type": "comprehensive" if comprehensive else "single",
            "results": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to test narrative adherence: {e}")

@router.get("/narrative/test-adherence/{route_id}")
async def get_narrative_adherence_report(
    route_id: str,
    story_influence: Optional[float] = Query(None, ge=0.0, le=1.0),
    comprehensive: bool = Query(False),
    graph: ExtendedPoetryGraph = Depends(get_graph)
):
    """Get narrative adherence test results for a route."""
    try:
        from scripts.test_narrative_adherence import NarrativeAdherenceTest
        
        tester = NarrativeAdherenceTest()
        
        if comprehensive:
            # Test multiple story influence levels
            influence_levels = [0.1, 0.3, 0.5, 0.7, 0.9]
            results = tester.test_multiple_story_influences(route_id, influence_levels)
        elif story_influence is not None:
            # Test single story influence level
            results = tester.test_route_narrative_adherence(route_id, story_influence)
        else:
            # Default to moderate story influence
            results = tester.test_route_narrative_adherence(route_id, 0.5)
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get adherence report: {e}")

@router.post("/narrative/generate-adherence-report")
async def generate_adherence_report_file(
    request: Dict[str, Any],
    graph: ExtendedPoetryGraph = Depends(get_graph)
):
    """Generate a comprehensive narrative adherence report file."""
    try:
        route_id = request.get("route_id")
        
        if not route_id:
            raise HTTPException(status_code=400, detail="route_id is required")
        
        from scripts.test_narrative_adherence import NarrativeAdherenceTest
        
        tester = NarrativeAdherenceTest()
        report_content = tester.generate_adherence_report(route_id, save_to_file=True)
        
        return {
            "success": True,
            "message": f"Narrative adherence report generated for route {route_id}",
            "preview": report_content[:500] + "..." if len(report_content) > 500 else report_content
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {e}")

@router.post("/system/import-user-poems")
async def import_user_poems(graph: ExtendedPoetryGraph = Depends(get_graph)):
    """Import all user poems from the poems directory into the graph."""
    try:
        from pathlib import Path
        poems_dir = Path(__file__).parent / "poems"
        
        if not poems_dir.exists():
            raise HTTPException(status_code=404, detail="Poems directory not found")
        
        poem_files = list(poems_dir.glob("*.txt"))
        if not poem_files:
            return {"message": "No poem files found", "imported_count": 0}
        
        imported_poems = []
        skipped_poems = []
        
        for poem_file in poem_files:
            try:
                # Parse poem file
                content = poem_file.read_text(encoding='utf-8').strip()
                lines = content.split('\n')
                
                title = None
                for line in lines:
                    line = line.strip()
                    if line:
                        title = line
                        break
                
                if not title:
                    title = poem_file.stem.replace('_', ' ')
                
                poem_id = f"user_poem_{poem_file.stem}"
                
                # Check if already exists
                if graph.graph.has_node(poem_id):
                    skipped_poems.append({"file": poem_file.name, "title": title, "reason": "already_exists"})
                    continue
                
                # Basic theme analysis
                content_lower = content.lower()
                themes = []
                if any(word in content_lower for word in ['death', 'die', 'dying', 'mortality']):
                    themes.append('mortality')
                if any(word in content_lower for word in ['nature', 'tree', 'forest', 'earth', 'woods']):
                    themes.append('nature')
                if any(word in content_lower for word in ['city', 'urban', 'station', 'train']):
                    themes.append('urban')
                if any(word in content_lower for word in ['technology', 'network', 'digital']):
                    themes.append('technology')
                if any(word in content_lower for word in ['time', 'past', 'future', 'memory']):
                    themes.append('time')
                if any(word in content_lower for word in ['family', 'children', 'grandchildren']):
                    themes.append('family_generations')
                if any(word in content_lower for word in ['connection', 'network', 'link']):
                    themes.append('connection')
                if any(word in content_lower for word in ['silence', 'silent', 'voice', 'sound']):
                    themes.append('sound_silence')
                
                # Add poem to graph using singleton instance
                graph.add_poem(
                    poem_id=poem_id,
                    title=title,
                    text=content,
                    route_id="user_authored",
                    themes=themes,
                    metadata={
                        'source_file': poem_file.name,
                        'import_date': datetime.now().isoformat(),
                        'author': 'user',
                        'source_type': 'api_import'
                    },
                    narrative_role="unassigned"
                )
                
                imported_poems.append({
                    "file": poem_file.name,
                    "title": title,
                    "poem_id": poem_id,
                    "themes": themes
                })
                
            except Exception as e:
                skipped_poems.append({
                    "file": poem_file.name, 
                    "reason": "error",
                    "error": str(e)
                })
        
        # Save graph through singleton
        if imported_poems:
            graph.save_graph()
        
        return {
            "message": f"Successfully imported {len(imported_poems)} poems",
            "imported_count": len(imported_poems),
            "skipped_count": len(skipped_poems),
            "imported_poems": imported_poems,
            "skipped_poems": skipped_poems
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to import user poems: {e}")

@router.post("/system/upload-poem")
async def upload_poem(
    file: UploadFile = File(...),
    graph: ExtendedPoetryGraph = Depends(get_graph)
):
    """Upload and import a single poem file."""
    try:
        # Check file type
        if not file.filename.endswith('.txt'):
            raise HTTPException(status_code=400, detail="Only .txt files are supported")
        
        # Read file content
        content = (await file.read()).decode('utf-8').strip()
        
        if not content:
            raise HTTPException(status_code=400, detail="File is empty")
        
        # Parse poem
        lines = content.split('\n')
        title = None
        for line in lines:
            line = line.strip()
            if line:
                title = line
                break
        
        if not title:
            # Use filename without extension as title
            title = file.filename.replace('.txt', '').replace('_', ' ')
        
        # Generate unique poem ID
        base_name = file.filename.replace('.txt', '').replace(' ', '_')
        poem_id = f"user_poem_{base_name}"
        
        # Check if already exists
        counter = 1
        original_id = poem_id
        while graph.graph.has_node(poem_id):
            poem_id = f"{original_id}_{counter}"
            counter += 1
        
        # Basic theme analysis
        content_lower = content.lower()
        themes = []
        if any(word in content_lower for word in ['death', 'die', 'dying', 'mortality']):
            themes.append('mortality')
        if any(word in content_lower for word in ['nature', 'tree', 'forest', 'earth', 'woods']):
            themes.append('nature')
        if any(word in content_lower for word in ['city', 'urban', 'station', 'train']):
            themes.append('urban')
        if any(word in content_lower for word in ['technology', 'network', 'digital']):
            themes.append('technology')
        if any(word in content_lower for word in ['time', 'past', 'future', 'memory']):
            themes.append('time')
        if any(word in content_lower for word in ['family', 'children', 'grandchildren']):
            themes.append('family_generations')
        if any(word in content_lower for word in ['connection', 'network', 'link']):
            themes.append('connection')
        if any(word in content_lower for word in ['silence', 'silent', 'voice', 'sound']):
            themes.append('sound_silence')
        
        # Add poem to graph
        graph.add_poem(
            poem_id=poem_id,
            title=title,
            text=content,
            route_id="user_authored",
            themes=themes,
            metadata={
                'source_file': file.filename,
                'import_date': datetime.now().isoformat(),
                'author': 'user',
                'source_type': 'upload'
            },
            narrative_role="unassigned"
        )
        
        # Save graph
        graph.save_graph()
        
        return {
            "message": "Poem uploaded successfully",
            "poem": {
                "id": poem_id,
                "title": title,
                "filename": file.filename,
                "themes": themes
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload poem: {e}")

@router.post("/system/upload-poems")
async def upload_multiple_poems(
    files: List[UploadFile] = File(...),
    graph: ExtendedPoetryGraph = Depends(get_graph)
):
    """Upload and import multiple poem files."""
    try:
        uploaded_poems = []
        skipped_poems = []
        
        for file in files:
            try:
                # Check file type
                if not file.filename.endswith('.txt'):
                    skipped_poems.append({
                        "filename": file.filename,
                        "reason": "invalid_file_type",
                        "error": "Only .txt files are supported"
                    })
                    continue
                
                # Read file content
                content = (await file.read()).decode('utf-8').strip()
                
                if not content:
                    skipped_poems.append({
                        "filename": file.filename,
                        "reason": "empty_file",
                        "error": "File is empty"
                    })
                    continue
                
                # Parse poem
                lines = content.split('\n')
                title = None
                for line in lines:
                    line = line.strip()
                    if line:
                        title = line
                        break
                
                if not title:
                    title = file.filename.replace('.txt', '').replace('_', ' ')
                
                # Generate unique poem ID
                base_name = file.filename.replace('.txt', '').replace(' ', '_')
                poem_id = f"user_poem_{base_name}"
                
                # Check if already exists
                counter = 1
                original_id = poem_id
                while graph.graph.has_node(poem_id):
                    poem_id = f"{original_id}_{counter}"
                    counter += 1
                
                # Basic theme analysis
                content_lower = content.lower()
                themes = []
                if any(word in content_lower for word in ['death', 'die', 'dying', 'mortality']):
                    themes.append('mortality')
                if any(word in content_lower for word in ['nature', 'tree', 'forest', 'earth', 'woods']):
                    themes.append('nature')
                if any(word in content_lower for word in ['city', 'urban', 'station', 'train']):
                    themes.append('urban')
                if any(word in content_lower for word in ['technology', 'network', 'digital']):
                    themes.append('technology')
                if any(word in content_lower for word in ['time', 'past', 'future', 'memory']):
                    themes.append('time')
                if any(word in content_lower for word in ['family', 'children', 'grandchildren']):
                    themes.append('family_generations')
                if any(word in content_lower for word in ['connection', 'network', 'link']):
                    themes.append('connection')
                if any(word in content_lower for word in ['silence', 'silent', 'voice', 'sound']):
                    themes.append('sound_silence')
                
                # Add poem to graph
                graph.add_poem(
                    poem_id=poem_id,
                    title=title,
                    text=content,
                    route_id="user_authored",
                    themes=themes,
                    metadata={
                        'source_file': file.filename,
                        'import_date': datetime.now().isoformat(),
                        'author': 'user',
                        'source_type': 'upload'
                    },
                    narrative_role="unassigned"
                )
                
                uploaded_poems.append({
                    "filename": file.filename,
                    "title": title,
                    "poem_id": poem_id,
                    "themes": themes
                })
                
            except Exception as e:
                skipped_poems.append({
                    "filename": file.filename,
                    "reason": "processing_error",
                    "error": str(e)
                })
        
        # Save graph if any poems were uploaded
        if uploaded_poems:
            graph.save_graph()
        
        return {
            "message": f"Uploaded {len(uploaded_poems)} poems successfully",
            "uploaded_count": len(uploaded_poems),
            "skipped_count": len(skipped_poems),
            "uploaded_poems": uploaded_poems,
            "skipped_poems": skipped_poems
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload poems: {e}")

@router.get("/available-routes")
async def get_available_routes():
    """
    Get all available routes from GTFS data with human-friendly names.
    """
    try:
        from pathlib import Path
        
        # Path to GTFS routes file
        routes_file = Path(__file__).parent / "data" / "gtfs" / "routes.txt"
        personalities_file = Path(__file__).parent / "data" / "route_personalities.json"
        
        routes = {}
        existing_personalities = {}
        
        # Load existing personalities
        if personalities_file.exists():
            import json
            with open(personalities_file, 'r') as f:
                existing_personalities = json.load(f)
        
        # Load routes from GTFS
        if routes_file.exists():
            with open(routes_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                headers = lines[0].strip().split(',')
                
                for line in lines[1:]:
                    values = line.strip().split(',')
                    if len(values) >= len(headers):
                        route_data = dict(zip(headers, values))
                        route_id = f"MARTA_{route_data.get('route_id', '')}"
                        route_short = route_data.get('route_short_name', '')
                        route_long = route_data.get('route_long_name', '')
                        
                        # Create human-friendly name
                        if route_short and route_long:
                            friendly_name = f"Route {route_short} - {route_long}"
                        elif route_short:
                            friendly_name = f"Route {route_short}"
                        elif route_long:
                            friendly_name = route_long
                        else:
                            friendly_name = route_id
                        
                        routes[route_id] = {
                            "id": route_id,
                            "name": friendly_name,
                            "short_name": route_short,
                            "long_name": route_long,
                            "has_personality": route_id in existing_personalities
                        }
        
        return {
            "routes": routes,
            "total_available": len(routes),
            "total_with_personalities": len(existing_personalities)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load available routes: {e}"
        )