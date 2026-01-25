#!/usr/bin/env python3
"""
Graph Export Utility

Export the poetry graph in various formats for analysis and backup.
"""

import sys
import os
import json
import csv
import argparse
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from poetry.graph.extended_poetry_graph import ExtendedPoetryGraph


class GraphExporter:
    """Exports graph data in various formats."""
    
    def __init__(self):
        """Initialize the exporter."""
        self.graph_path = backend_dir / "data" / "poetry_graph.json"
        self.exports_dir = backend_dir / "exports"
        self.exports_dir.mkdir(exist_ok=True)
        self.graph = None
    
    def load_graph(self) -> ExtendedPoetryGraph:
        """Load the graph."""
        if self.graph is None:
            if not self.graph_path.exists():
                raise FileNotFoundError(f"Graph file not found: {self.graph_path}")
            self.graph = ExtendedPoetryGraph(str(self.graph_path))
        return self.graph
    
    def export_poems_csv(self) -> str:
        """Export poems to CSV format."""
        graph = self.load_graph()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_file = self.exports_dir / f"poems_{timestamp}.csv"
        
        poems = [(node_id, data) for node_id, data in graph.graph.nodes(data=True) 
                if data.get("type") == "poem"]
        
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Headers
            writer.writerow([
                'poem_id', 'title', 'route_id', 'created_at', 'text_length',
                'line_count', 'form', 'themes', 'imagery', 'emotions', 'sound_devices'
            ])
            
            for poem_id, poem_data in poems:
                full_data = graph.get_poem(poem_id)
                
                # Basic info
                title = poem_data.get('title', '')
                route_id = poem_data.get('route_id', '')
                created_at = poem_data.get('created_at', '')
                text = poem_data.get('text', '')
                text_length = len(text)
                
                # Structure info
                metadata = poem_data.get('metadata', {})
                structure = metadata.get('structure', {})
                line_count = structure.get('line_count', '')
                form = structure.get('form', '')
                
                # Connected elements
                themes = '; '.join(full_data.get('themes', []))
                imagery = '; '.join(full_data.get('imagery', []))
                emotions = '; '.join(full_data.get('emotions', []))
                sound_devices = '; '.join(full_data.get('sound_devices', []))
                
                writer.writerow([
                    poem_id, title, route_id, created_at, text_length,
                    line_count, form, themes, imagery, emotions, sound_devices
                ])
        
        return str(csv_file)
    
    def export_connections_csv(self) -> str:
        """Export connections/relationships to CSV."""
        graph = self.load_graph()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_file = self.exports_dir / f"connections_{timestamp}.csv"
        
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Headers
            writer.writerow([
                'source_id', 'target_id', 'source_type', 'target_type',
                'connection_type', 'source_name', 'target_name'
            ])
            
            for source, target, edge_data in graph.graph.edges(data=True):
                source_data = graph.graph.nodes[source]
                target_data = graph.graph.nodes[target]
                
                source_type = source_data.get('type', 'unknown')
                target_type = target_data.get('type', 'unknown')
                connection_type = edge_data.get('type', 'unknown')
                
                source_name = source_data.get('name', source_data.get('title', source))
                target_name = target_data.get('name', target_data.get('title', target))
                
                writer.writerow([
                    source, target, source_type, target_type,
                    connection_type, source_name, target_name
                ])
        
        return str(csv_file)
    
    def export_summary_json(self) -> str:
        """Export a summary of the graph in JSON format."""
        graph = self.load_graph()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_file = self.exports_dir / f"graph_summary_{timestamp}.json"
        
        # Collect summary data
        summary = graph.get_graph_summary()
        route_stats = graph.get_all_routes_statistics()
        
        # Get element counts
        elements_by_type = {}
        for node_id, node_data in graph.graph.nodes(data=True):
            node_type = node_data.get('type', 'unknown')
            if node_type not in elements_by_type:
                elements_by_type[node_type] = []
            
            if node_type != 'poem':
                elements_by_type[node_type].append({
                    'id': node_id,
                    'name': node_data.get('name', node_id),
                    'connections': len(list(graph.graph.neighbors(node_id)))
                })
        
        # Get co-occurrence data
        theme_emotion = graph.get_entity_co_occurrence("theme", "emotion")
        imagery_emotion = graph.get_entity_co_occurrence("imagery", "emotion")
        
        # Convert tuple keys to strings for JSON serialization
        theme_emotion_str = {f"{k[0]}+{k[1]}": v for k, v in theme_emotion.items()}
        imagery_emotion_str = {f"{k[0]}+{k[1]}": v for k, v in imagery_emotion.items()}
        
        export_data = {
            'generated_at': datetime.now().isoformat(),
            'graph_summary': summary,
            'route_statistics': route_stats,
            'elements_by_type': elements_by_type,
            'co_occurrences': {
                'theme_emotion': theme_emotion_str,
                'imagery_emotion': imagery_emotion_str
            }
        }
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        return str(json_file)
    
    def export_poems_text(self) -> str:
        """Export all poems as a single text file."""
        graph = self.load_graph()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        text_file = self.exports_dir / f"all_poems_{timestamp}.txt"
        
        poems = [(node_id, data) for node_id, data in graph.graph.nodes(data=True) 
                if data.get("type") == "poem"]
        
        # Sort by creation date
        poems_with_dates = []
        for poem_id, poem_data in poems:
            created_at = poem_data.get("created_at", "")
            try:
                dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                poems_with_dates.append((dt, poem_id, poem_data))
            except:
                poems_with_dates.append((datetime.min, poem_id, poem_data))
        
        poems_with_dates.sort(key=lambda x: x[0])
        
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write("MARTA POETRY PROJECT - COMPLETE COLLECTION\n")
            f.write("=" * 60 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Poems: {len(poems)}\n")
            f.write("=" * 60 + "\n\n")
            
            for i, (dt, poem_id, poem_data) in enumerate(poems_with_dates, 1):
                title = poem_data.get('title', 'Untitled')
                route_id = poem_data.get('route_id', 'Unknown')
                text = poem_data.get('text', '')
                
                f.write(f"{i}. {title}\n")
                f.write(f"Route: {route_id}\n")
                if dt != datetime.min:
                    f.write(f"Created: {dt.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("-" * 40 + "\n")
                f.write(text + "\n")
                f.write("=" * 60 + "\n\n")
        
        return str(text_file)
    
    def export_all(self) -> Dict[str, str]:
        """Export in all formats."""
        exports = {}
        
        print("📤 Exporting poems CSV...")
        exports['poems_csv'] = self.export_poems_csv()
        
        print("📤 Exporting connections CSV...")
        exports['connections_csv'] = self.export_connections_csv()
        
        print("📤 Exporting summary JSON...")
        exports['summary_json'] = self.export_summary_json()
        
        print("📤 Exporting poems text...")
        exports['poems_text'] = self.export_poems_text()
        
        return exports


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Poetry Graph Export Utility")
    parser.add_argument("--poems-csv", action="store_true", help="Export poems to CSV")
    parser.add_argument("--connections-csv", action="store_true", help="Export connections to CSV")
    parser.add_argument("--summary-json", action="store_true", help="Export summary to JSON")
    parser.add_argument("--poems-text", action="store_true", help="Export all poems to text file")
    parser.add_argument("--all", action="store_true", help="Export in all formats")
    
    args = parser.parse_args()
    
    exporter = GraphExporter()
    
    try:
        if args.all:
            exports = exporter.export_all()
            print("\n✅ All exports completed:")
            for export_type, file_path in exports.items():
                print(f"   • {export_type}: {file_path}")
        
        elif args.poems_csv:
            file_path = exporter.export_poems_csv()
            print(f"✅ Poems CSV exported: {file_path}")
        
        elif args.connections_csv:
            file_path = exporter.export_connections_csv()
            print(f"✅ Connections CSV exported: {file_path}")
        
        elif args.summary_json:
            file_path = exporter.export_summary_json()
            print(f"✅ Summary JSON exported: {file_path}")
        
        elif args.poems_text:
            file_path = exporter.export_poems_text()
            print(f"✅ Poems text exported: {file_path}")
        
        else:
            print("Poetry Graph Export Utility")
            print("Use --help for options")
            print("\nAvailable exports:")
            print("  --poems-csv       Export poems to CSV format")
            print("  --connections-csv Export connections to CSV format")
            print("  --summary-json    Export graph summary to JSON")
            print("  --poems-text      Export all poems to single text file")
            print("  --all            Export in all formats")
    
    except Exception as e:
        print(f"❌ Export error: {e}")


if __name__ == "__main__":
    main()