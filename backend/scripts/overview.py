#!/usr/bin/env python3
"""
MARTA Poetry Project - Manual Graph Management Overview

This script provides an overview of all available tools for managing your poetry graph manually.
"""

from pathlib import Path
from datetime import datetime


def show_overview():
    """Show overview of available tools and files."""
    backend_dir = Path(__file__).parent.parent
    
    print("=" * 80)
    print("📊 MARTA POETRY PROJECT - MANUAL GRAPH MANAGEMENT")
    print("=" * 80)
    print(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Backend directory: {backend_dir}")
    
    # Check graph file
    graph_path = backend_dir / "data" / "poetry_graph.json"
    if graph_path.exists():
        file_size = graph_path.stat().st_size
        print(f"✅ Graph file exists: {graph_path} ({file_size:,} bytes)")
    else:
        print(f"❌ Graph file not found: {graph_path}")
    
    print("\n🛠️  AVAILABLE TOOLS:")
    print("-" * 40)
    
    tools = [
        {
            "script": "scripts/graph_initializer.py",
            "description": "Main graph management tool",
            "commands": [
                "--examine      View current graph state",
                "--initialize   Initialize from poem files", 
                "--add-poem     Add a poem interactively",
                "--analyze      Deep analysis of relationships"
            ]
        },
        {
            "script": "scripts/poem_explorer.py", 
            "description": "Explore individual poems",
            "commands": [
                "--list        List all poems",
                "--show ID     Show detailed poem information",
                "--related ID  Find related poems"
            ]
        },
        {
            "script": "scripts/generate_report.py",
            "description": "Generate comprehensive reports",
            "commands": [
                "--full-report Generate complete analysis report",
                "--print       Print to console instead of saving"
            ]
        },
        {
            "script": "scripts/export_graph.py",
            "description": "Export data for external analysis",
            "commands": [
                "--poems-csv      Export poems to CSV",
                "--connections-csv Export relationships to CSV",
                "--summary-json   Export summary to JSON", 
                "--poems-text     Export all poems to text file",
                "--all           Export in all formats"
            ]
        },
        {
            "script": "scripts/narrative_manager.py",
            "description": "Manage core narrative designation",
            "commands": [
                "--status         Show narrative structure",
                "--mark-core ID   Mark poems as core narrative",
                "--mark-extension ID Mark poems as extensions",
                "--interactive    Interactive narrative management"
            ]
        }
    ]
    
    for tool in tools:
        script_path = backend_dir / tool["script"]
        exists = "✅" if script_path.exists() else "❌"
        print(f"\n{exists} {tool['script']}")
        print(f"   {tool['description']}")
        for cmd in tool["commands"]:
            print(f"   python3 {tool['script']} {cmd}")
    
    print(f"\n📁 OUTPUT DIRECTORIES:")
    print("-" * 40)
    
    output_dirs = [
        ("reports/", "Detailed analysis reports"),
        ("exports/", "Data exports (CSV, JSON, TXT)"),
        ("poems/", "Poem source files (for initialization)"),
    ]
    
    for dir_name, description in output_dirs:
        dir_path = backend_dir / dir_name
        if dir_path.exists():
            file_count = len(list(dir_path.glob("*")))
            print(f"✅ {dir_name:<12} {description} ({file_count} files)")
        else:
            print(f"📁 {dir_name:<12} {description} (create as needed)")
    
    print(f"\n📊 CURRENT GRAPH STATUS:")
    print("-" * 40)
    
    try:
        # Quick graph check
        import sys
        sys.path.insert(0, str(backend_dir))
        from poetry.graph.extended_poetry_graph import ExtendedPoetryGraph
        
        if graph_path.exists():
            graph = ExtendedPoetryGraph(str(graph_path))
            summary = graph.get_graph_summary()
            
            print(f"Poems: {summary['total_poems']}")
            print(f"Routes: {summary['contributing_routes']}")
            print(f"Themes: {summary['total_themes']}")
            print(f"Imagery: {summary['total_imagery']}")
            print(f"Emotions: {summary['total_emotions']}")
            print(f"Sound Devices: {summary['total_sound_devices']}")
            print(f"Connections: {summary['total_connections']}")
            
            # Show latest poems
            poems = [(node_id, data) for node_id, data in graph.graph.nodes(data=True) 
                    if data.get("type") == "poem"]
            
            if poems:
                # Sort by creation date
                poems_with_dates = []
                for poem_id, poem_data in poems:
                    created_at = poem_data.get("created_at", "")
                    try:
                        dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                        poems_with_dates.append((dt, poem_id, poem_data))
                    except:
                        pass
                
                if poems_with_dates:
                    poems_with_dates.sort(key=lambda x: x[0], reverse=True)
                    print(f"\n📚 Latest Poems:")
                    for dt, poem_id, poem_data in poems_with_dates[:3]:
                        title = poem_data.get('title', 'Untitled')[:40]
                        route_id = poem_data.get('route_id', 'Unknown')
                        print(f"   • {title} (Route: {route_id})")
        else:
            print("Graph file not found - run initialization first")
    
    except Exception as e:
        print(f"Error reading graph: {e}")
    
    print(f"\n🚀 GETTING STARTED:")
    print("-" * 40)
    print("1. Examine current graph:     python3 scripts/graph_initializer.py --examine")
    print("2. Check narrative structure: python3 scripts/narrative_manager.py --status")
    print("3. Generate full report:      python3 scripts/generate_report.py --full-report")
    print("4. List all poems:            python3 scripts/poem_explorer.py --list")
    print("5. Export all data:           python3 scripts/export_graph.py --all")
    print("6. Add poems from files:      python3 scripts/graph_initializer.py --initialize")
    
    print(f"\n💡 TIPS:")
    print("-" * 40)
    print("• Place poem files (.txt, .md, .json) in the poems/ directory for batch import")
    print("• Manual poems (route_id='MANUAL') are automatically marked as 'core' narrative")
    print("• Use scripts/narrative_manager.py to designate core vs route-generated poems")
    print("• Create narrative connections between core poems and route extensions")
    print("• Use --related POEM_ID to find poems with similar themes/imagery/emotions")
    print("• Reports and exports are timestamped for version tracking")
    print("• The graph automatically saves after changes")
    print("• All tools work with the current graph state in data/poetry_graph.json")
    
    print("=" * 80)


if __name__ == "__main__":
    show_overview()