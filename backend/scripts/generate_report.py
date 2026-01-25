#!/usr/bin/env python3
"""
Graph Summary Report Generator

This script creates detailed reports about your poetry graph that you can save and review.
"""

import sys
import os
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
from collections import Counter, defaultdict

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from poetry.graph.extended_poetry_graph import ExtendedPoetryGraph


class GraphReportGenerator:
    """Generates comprehensive reports about the poetry graph."""
    
    def __init__(self):
        """Initialize the report generator."""
        self.graph_path = backend_dir / "data" / "poetry_graph.json"
        self.graph = None
        self.reports_dir = backend_dir / "reports"
        self.reports_dir.mkdir(exist_ok=True)
    
    def load_graph(self) -> ExtendedPoetryGraph:
        """Load the graph."""
        if self.graph is None:
            if not self.graph_path.exists():
                raise FileNotFoundError(f"Graph file not found: {self.graph_path}")
            self.graph = ExtendedPoetryGraph(str(self.graph_path))
        return self.graph
    
    def generate_full_report(self, save_to_file: bool = True) -> str:
        """Generate a comprehensive report of the entire graph."""
        graph = self.load_graph()
        
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("📊 MARTA POETRY PROJECT - COMPLETE GRAPH REPORT")
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("=" * 80)
        
        # 1. Executive Summary
        report_lines.extend(self._generate_executive_summary(graph))
        
        # 2. Route Analysis
        report_lines.extend(self._generate_route_analysis(graph))
        
        # 3. Thematic Analysis
        report_lines.extend(self._generate_thematic_analysis(graph))
        
        # 4. Literary Analysis
        report_lines.extend(self._generate_literary_analysis(graph))
        
        # 5. Temporal Analysis
        report_lines.extend(self._generate_temporal_analysis(graph))
        
        # 6. Network Analysis
        report_lines.extend(self._generate_network_analysis(graph))
        
        # 7. Individual Poem Details
        report_lines.extend(self._generate_poem_catalog(graph))
        
        report_content = "\n".join(report_lines)
        
        if save_to_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = self.reports_dir / f"graph_report_{timestamp}.txt"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report_content)
            print(f"📁 Report saved to: {report_file}")
        
        return report_content
    
    def _generate_executive_summary(self, graph: ExtendedPoetryGraph) -> List[str]:
        """Generate executive summary section."""
        lines = []
        lines.append("\n" + "🎯 EXECUTIVE SUMMARY")
        lines.append("-" * 40)
        
        summary = graph.get_graph_summary()
        poems = [(node_id, data) for node_id, data in graph.graph.nodes(data=True) 
                if data.get("type") == "poem"]
        
        lines.append(f"Total Poems: {summary['total_poems']}")
        lines.append(f"Contributing Routes: {summary['contributing_routes']}")
        lines.append(f"Unique Themes: {summary['total_themes']}")
        lines.append(f"Imagery Elements: {summary['total_imagery']}")
        lines.append(f"Emotional Range: {summary['total_emotions']}")
        lines.append(f"Sound Devices: {summary['total_sound_devices']}")
        lines.append(f"Graph Connections: {summary['total_connections']}")
        
        # Calculate average elements per poem
        if poems:
            avg_themes = summary['total_themes'] / len(poems)
            avg_imagery = summary['total_imagery'] / len(poems)
            avg_emotions = summary['total_emotions'] / len(poems)
            
            lines.append(f"\nAverages per Poem:")
            lines.append(f"  • Themes: {avg_themes:.1f}")
            lines.append(f"  • Imagery: {avg_imagery:.1f}")
            lines.append(f"  • Emotions: {avg_emotions:.1f}")
        
        return lines
    
    def _generate_route_analysis(self, graph: ExtendedPoetryGraph) -> List[str]:
        """Generate route analysis section."""
        lines = []
        lines.append("\n" + "🚌 ROUTE ANALYSIS")
        lines.append("-" * 40)
        
        route_stats = graph.get_all_routes_statistics()
        
        lines.append(f"Active Routes: {len(route_stats)}")
        lines.append("\nRoute Productivity:")
        
        # Sort by poem count
        route_stats.sort(key=lambda x: x['poem_count'], reverse=True)
        
        for stats in route_stats:
            route_id = stats['route_id']
            poem_count = stats['poem_count']
            avg_themes = stats.get('avg_themes_per_poem', 0)
            avg_imagery = stats.get('avg_imagery_per_poem', 0)
            
            lines.append(f"  • {route_id}:")
            lines.append(f"    - {poem_count} poems")
            lines.append(f"    - {avg_themes:.1f} avg themes per poem")
            lines.append(f"    - {avg_imagery:.1f} avg imagery per poem")
            
            # Get route's dominant themes
            dominant_themes = stats.get('dominant_themes', [])
            if dominant_themes:
                theme_str = ", ".join(dominant_themes[:3])
                lines.append(f"    - Dominant themes: {theme_str}")
        
        return lines
    
    def _generate_thematic_analysis(self, graph: ExtendedPoetryGraph) -> List[str]:
        """Generate thematic analysis section."""
        lines = []
        lines.append("\n" + "🎭 THEMATIC ANALYSIS")
        lines.append("-" * 40)
        
        # Get theme co-occurrences
        theme_emotion = graph.get_entity_co_occurrence("theme", "emotion")
        
        lines.append("Most Common Theme-Emotion Combinations:")
        if theme_emotion:
            sorted_pairs = sorted(theme_emotion.items(), key=lambda x: x[1], reverse=True)
            for i, ((theme, emotion), count) in enumerate(sorted_pairs[:10], 1):
                lines.append(f"  {i:2}. {theme} + {emotion}: {count} occurrences")
        
        # Get imagery-emotion pairs
        imagery_emotion = graph.get_entity_co_occurrence("imagery", "emotion")
        
        lines.append("\nMost Common Imagery-Emotion Combinations:")
        if imagery_emotion:
            sorted_pairs = sorted(imagery_emotion.items(), key=lambda x: x[1], reverse=True)
            for i, ((imagery, emotion), count) in enumerate(sorted_pairs[:10], 1):
                lines.append(f"  {i:2}. {imagery} + {emotion}: {count} occurrences")
        
        return lines
    
    def _generate_literary_analysis(self, graph: ExtendedPoetryGraph) -> List[str]:
        """Generate literary analysis section."""
        lines = []
        lines.append("\n" + "🎨 LITERARY ANALYSIS")
        lines.append("-" * 40)
        
        poems = [(node_id, data) for node_id, data in graph.graph.nodes(data=True) 
                if data.get("type") == "poem"]
        
        # Analyze structures
        line_counts = []
        forms = []
        enjambments = []
        caesuras = []
        sound_patterns = defaultdict(int)
        
        for poem_id, poem_data in poems:
            metadata = poem_data.get("metadata", {})
            structure = metadata.get("structure", {})
            sound_data = metadata.get("sound_patterns", {})
            
            if structure:
                line_count = structure.get("line_count", 0)
                form = structure.get("form", "unknown")
                enjambment_lines = structure.get("enjambment_lines", [])
                caesura_lines = structure.get("caesura_lines", [])
                
                if line_count > 0:
                    line_counts.append(line_count)
                if form != "unknown":
                    forms.append(form)
                if enjambment_lines:
                    enjambments.append(len(enjambment_lines))
                if caesura_lines:
                    caesuras.append(len(caesura_lines))
            
            # Count sound patterns
            for pattern, value in sound_data.items():
                if isinstance(value, str) and value in ['high', 'moderate', 'low']:
                    sound_patterns[f"{pattern}_{value}"] += 1
                elif isinstance(value, (int, float)):
                    sound_patterns[pattern] += value
        
        lines.append("Structural Patterns:")
        if line_counts:
            avg_lines = sum(line_counts) / len(line_counts)
            min_lines = min(line_counts)
            max_lines = max(line_counts)
            lines.append(f"  • Line count: avg={avg_lines:.1f}, range={min_lines}-{max_lines}")
        
        if enjambments:
            avg_enj = sum(enjambments) / len(enjambments)
            lines.append(f"  • Enjambment: avg={avg_enj:.1f} lines per poem")
        
        if caesuras:
            avg_caesura = sum(caesuras) / len(caesuras)
            lines.append(f"  • Caesura: avg={avg_caesura:.1f} lines per poem")
        
        if forms:
            form_counts = Counter(forms)
            lines.append("  • Forms used:")
            for form, count in form_counts.most_common():
                lines.append(f"    - {form}: {count} poems")
        
        if sound_patterns:
            lines.append("\nSound Pattern Distribution:")
            for pattern, count in sorted(sound_patterns.items())[:10]:
                lines.append(f"  • {pattern}: {count}")
        
        return lines
    
    def _generate_temporal_analysis(self, graph: ExtendedPoetryGraph) -> List[str]:
        """Generate temporal analysis section."""
        lines = []
        lines.append("\n" + "⏰ TEMPORAL ANALYSIS")
        lines.append("-" * 40)
        
        poems = [(node_id, data) for node_id, data in graph.graph.nodes(data=True) 
                if data.get("type") == "poem"]
        
        # Parse dates
        poem_dates = []
        for poem_id, poem_data in poems:
            created_at = poem_data.get("created_at")
            if created_at:
                try:
                    # Parse ISO format
                    dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                    poem_dates.append((dt, poem_id, poem_data))
                except:
                    continue
        
        if not poem_dates:
            lines.append("No temporal data available.")
            return lines
        
        # Sort by date
        poem_dates.sort(key=lambda x: x[0])
        
        lines.append(f"Composition Timeline ({len(poem_dates)} poems):")
        lines.append(f"First poem: {poem_dates[0][0].strftime('%Y-%m-%d %H:%M')}")
        lines.append(f"Latest poem: {poem_dates[-1][0].strftime('%Y-%m-%d %H:%M')}")
        
        # Group by day
        daily_counts = defaultdict(int)
        hourly_counts = defaultdict(int)
        
        for dt, poem_id, poem_data in poem_dates:
            daily_counts[dt.date()] += 1
            hourly_counts[dt.hour] += 1
        
        if len(daily_counts) > 1:
            lines.append(f"\nDaily distribution:")
            for date, count in sorted(daily_counts.items()):
                lines.append(f"  • {date}: {count} poems")
        
        if hourly_counts:
            lines.append(f"\nHourly distribution:")
            peak_hours = sorted(hourly_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            for hour, count in peak_hours:
                lines.append(f"  • {hour:02d}:00: {count} poems")
        
        return lines
    
    def _generate_network_analysis(self, graph: ExtendedPoetryGraph) -> List[str]:
        """Generate network analysis section."""
        lines = []
        lines.append("\n" + "🕸️  NETWORK ANALYSIS")
        lines.append("-" * 40)
        
        # Count connections by type
        connection_types = defaultdict(int)
        for u, v, data in graph.graph.edges(data=True):
            edge_type = data.get('type', 'unknown')
            connection_types[edge_type] += 1
        
        lines.append("Connection Types:")
        for conn_type, count in sorted(connection_types.items()):
            lines.append(f"  • {conn_type}: {count}")
        
        # Find most connected poems
        poem_connections = defaultdict(int)
        for node_id, node_data in graph.graph.nodes(data=True):
            if node_data.get("type") == "poem":
                connections = len(list(graph.graph.neighbors(node_id)))
                poem_connections[node_id] = connections
        
        if poem_connections:
            lines.append("\nMost Connected Poems:")
            top_connected = sorted(poem_connections.items(), key=lambda x: x[1], reverse=True)[:5]
            for poem_id, conn_count in top_connected:
                poem_data = graph.graph.nodes[poem_id]
                title = poem_data.get("title", "Untitled")[:40]
                lines.append(f"  • {title}: {conn_count} connections")
        
        return lines
    
    def _generate_poem_catalog(self, graph: ExtendedPoetryGraph) -> List[str]:
        """Generate detailed poem catalog."""
        lines = []
        lines.append("\n" + "📚 COMPLETE POEM CATALOG")
        lines.append("-" * 40)
        
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
                # Put undated poems at the end
                poems_with_dates.append((datetime.min, poem_id, poem_data))
        
        poems_with_dates.sort(key=lambda x: x[0])
        
        for i, (dt, poem_id, poem_data) in enumerate(poems_with_dates, 1):
            lines.append(f"\n{i:2}. {poem_data.get('title', 'Untitled')}")
            lines.append(f"    ID: {poem_id}")
            lines.append(f"    Route: {poem_data.get('route_id', 'Unknown')}")
            
            if dt != datetime.min:
                lines.append(f"    Created: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Get connected elements
            full_poem_data = graph.get_poem(poem_id)
            themes = full_poem_data.get('themes', [])
            imagery = full_poem_data.get('imagery', [])
            emotions = full_poem_data.get('emotions', [])
            sound_devices = full_poem_data.get('sound_devices', [])
            
            if themes:
                lines.append(f"    Themes: {', '.join(themes[:5])}{'...' if len(themes) > 5 else ''}")
            if imagery:
                lines.append(f"    Imagery: {', '.join(imagery[:5])}{'...' if len(imagery) > 5 else ''}")
            if emotions:
                lines.append(f"    Emotions: {', '.join(emotions[:3])}")
            if sound_devices:
                lines.append(f"    Sound: {', '.join(sound_devices[:3])}")
            
            # Show first line of poem
            text = poem_data.get("text", "")
            if text:
                first_line = text.split('\n')[0][:60]
                if len(text.split('\n')[0]) > 60:
                    first_line += "..."
                lines.append(f"    \"{first_line}\"")
        
        return lines


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Poetry Graph Report Generator")
    parser.add_argument("--full-report", action="store_true", help="Generate complete report")
    parser.add_argument("--print", action="store_true", help="Print to console instead of saving")
    
    args = parser.parse_args()
    
    generator = GraphReportGenerator()
    
    if args.full_report:
        try:
            report = generator.generate_full_report(save_to_file=not args.print)
            if args.print:
                print(report)
        except Exception as e:
            print(f"❌ Error generating report: {e}")
    else:
        print("Poetry Graph Report Generator")
        print("Use --help for options")
        print("\nAvailable commands:")
        print("  --full-report    Generate a complete graph report")
        print("  --print          Print to console instead of saving to file")


if __name__ == "__main__":
    main()