#!/usr/bin/env python3
"""
Narrative Management Tool

This script helps you designate and manage core narrative poems vs route-generated content.
"""

import sys
import os
import argparse
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from poetry.graph.extended_poetry_graph import ExtendedPoetryGraph


class NarrativeManager:
    """Manages narrative designation and connections in the poetry graph."""
    
    def __init__(self):
        """Initialize the narrative manager."""
        self.graph_path = backend_dir / "data" / "poetry_graph.json"
        self.graph = None
    
    def load_graph(self) -> ExtendedPoetryGraph:
        """Load the graph."""
        if self.graph is None:
            if not self.graph_path.exists():
                raise FileNotFoundError(f"Graph file not found: {self.graph_path}")
            self.graph = ExtendedPoetryGraph(str(self.graph_path))
        return self.graph
    
    def show_narrative_status(self):
        """Show current narrative structure."""
        graph = self.load_graph()
        
        print("=" * 80)
        print("📖 NARRATIVE STRUCTURE OVERVIEW")
        print("=" * 80)
        
        summary = graph.get_narrative_summary()
        
        print(f"📊 Summary:")
        print(f"   • Core narrative poems: {summary['core_poems']}")
        print(f"   • Extension poems: {summary['extension_poems']}")
        print(f"   • Route-generated poems: {summary['route_generated_poems']}")
        print(f"   • Variation poems: {summary['variation_poems']}")
        print(f"   • Narrative connections: {summary['narrative_connections']}")
        print(f"   • Total narrative framework: {summary['total_narrative_poems']} poems")
        
        if summary['core_poem_titles']:
            print(f"\n🎯 Core Poems:")
            for title in summary['core_poem_titles']:
                print(f"   • {title}")
        
        if summary['latest_core_poem']:
            latest = summary['latest_core_poem']
            print(f"\n📅 Latest Core Poem: {latest.get('title', 'Untitled')}")
        
        # Show all poems by narrative role
        print(f"\n📚 All Poems by Narrative Role:")
        
        all_poems = [(node_id, data) for node_id, data in graph.graph.nodes(data=True) 
                    if data.get("type") == "poem"]
        
        # Group by narrative role
        by_role = {}
        for poem_id, poem_data in all_poems:
            role = poem_data.get("narrative_role", "unassigned")
            if role not in by_role:
                by_role[role] = []
            by_role[role].append((poem_id, poem_data))
        
        role_order = ["core", "extension", "variation", "route_generated", "unassigned"]
        role_icons = {
            "core": "🎯",
            "extension": "🔗",
            "variation": "🔄",
            "route_generated": "🚌",
            "unassigned": "❓"
        }
        
        for role in role_order:
            if role in by_role:
                poems = by_role[role]
                icon = role_icons.get(role, "•")
                print(f"\n{icon} {role.replace('_', ' ').title()} ({len(poems)} poems):")
                
                for poem_id, poem_data in poems:
                    title = poem_data.get("title", "Untitled")[:50]
                    route_id = poem_data.get("route_id", "Unknown")
                    created = poem_data.get("created_at", "")[:10]  # Just date
                    print(f"   • [{poem_id}] {title}")
                    print(f"     Route: {route_id} | Created: {created}")
    
    def mark_poems_as_core(self, poem_ids: List[str]):
        """Mark specific poems as core narrative."""
        graph = self.load_graph()
        
        print("🎯 MARKING POEMS AS CORE NARRATIVE")
        print("-" * 40)
        
        success_count = 0
        for poem_id in poem_ids:
            if graph.mark_poem_as_core(poem_id):
                poem_data = graph.graph.nodes[poem_id]
                title = poem_data.get("title", "Untitled")
                print(f"✅ Marked as core: {title}")
                success_count += 1
            else:
                print(f"❌ Failed to mark: {poem_id} (not found)")
        
        if success_count > 0:
            graph.save_graph()
            print(f"\n💾 Saved {success_count} changes to graph")
    
    def mark_poems_as_core_interactive(self):
        """Interactive interface to mark poems as core narrative."""
        graph = self.load_graph()
        
        print("🎯 MARK POEMS AS CORE NARRATIVE")
        print("-" * 40)
        
        # Show available poems
        all_poems = [(node_id, data) for node_id, data in graph.graph.nodes(data=True) 
                    if data.get("type") == "poem"]
        
        if not all_poems:
            print("❌ No poems found in graph")
            return
        
        print("Available poems:")
        for i, (poem_id, poem_data) in enumerate(all_poems, 1):
            title = poem_data.get("title", "Untitled")[:50]
            role = poem_data.get("narrative_role", "unassigned")
            route_id = poem_data.get("route_id", "Unknown")
            print(f"  {i:2}. [{poem_id[:20]}...] {title}")
            print(f"      Role: {role} | Route: {route_id}")
        
        try:
            selections = input("\nEnter poem numbers to mark as CORE (comma-separated): ").strip()
            if not selections:
                print("❌ No selection made")
                return
            
            selected_indices = [int(x.strip()) - 1 for x in selections.split(",")]
            
            print("\n" + "="*50)
            print("⚠️  CONFIRM CORE NARRATIVE DESIGNATION")
            print("="*50)
            
            poems_to_mark = []
            for idx in selected_indices:
                if 0 <= idx < len(all_poems):
                    poem_id, poem_data = all_poems[idx]
                    title = poem_data.get("title", "Untitled")
                    poems_to_mark.append((poem_id, title))
                    print(f"  → {title}")
            
            if not poems_to_mark:
                print("❌ No valid poems selected")
                return
            
            confirm = input(f"\nMark {len(poems_to_mark)} poems as CORE narrative? (y/n): ").lower()
            if confirm != 'y':
                print("❌ Cancelled")
                return
            
            # Mark the poems
            poem_ids = [poem_id for poem_id, _ in poems_to_mark]
            self.mark_poems_as_core(poem_ids)
            
        except (ValueError, EOFError) as e:
            print(f"❌ Invalid input: {e}")

    def mark_poems_as_extension_interactive(self):
        """Interactive interface to mark poems as narrative extensions.""" 
        graph = self.load_graph()
        
        print("🔗 MARK POEMS AS NARRATIVE EXTENSIONS")
        print("-" * 40)
        
        # Show available poems
        all_poems = [(node_id, data) for node_id, data in graph.graph.nodes(data=True) 
                    if data.get("type") == "poem"]
        
        if not all_poems:
            print("❌ No poems found in graph")
            return
        
        print("Available poems:")
        for i, (poem_id, poem_data) in enumerate(all_poems, 1):
            title = poem_data.get("title", "Untitled")[:50]
            role = poem_data.get("narrative_role", "unassigned")
            route_id = poem_data.get("route_id", "Unknown")
            print(f"  {i:2}. [{poem_id[:20]}...] {title}")
            print(f"      Role: {role} | Route: {route_id}")
        
        try:
            selections = input("\nEnter poem numbers to mark as EXTENSIONS (comma-separated): ").strip()
            if not selections:
                print("❌ No selection made")
                return
            
            selected_indices = [int(x.strip()) - 1 for x in selections.split(",")]
            
            poems_to_mark = []
            for idx in selected_indices:
                if 0 <= idx < len(all_poems):
                    poem_id, poem_data = all_poems[idx]
                    title = poem_data.get("title", "Untitled")
                    poems_to_mark.append((poem_id, title))
                    print(f"  → {title}")
            
            if not poems_to_mark:
                print("❌ No valid poems selected")
                return
            
            confirm = input(f"\nMark {len(poems_to_mark)} poems as EXTENSIONS? (y/n): ").lower()
            if confirm != 'y':
                print("❌ Cancelled")
                return
            
            # Mark the poems
            poem_ids = [poem_id for poem_id, _ in poems_to_mark]
            self.mark_poems_as_extension(poem_ids)
            
        except (ValueError, EOFError) as e:
            print(f"❌ Invalid input: {e}")
    
    def mark_poems_as_extension(self, poem_ids: List[str]):
        """Mark specific poems as narrative extensions."""
        graph = self.load_graph()
        
        print("🔗 MARKING POEMS AS NARRATIVE EXTENSIONS")
        print("-" * 40)
        
        success_count = 0
        for poem_id in poem_ids:
            if graph.mark_poem_as_extension(poem_id):
                poem_data = graph.graph.nodes[poem_id]
                title = poem_data.get("title", "Untitled")
                print(f"✅ Marked as extension: {title}")
                success_count += 1
            else:
                print(f"❌ Failed to mark: {poem_id} (not found)")
        
        if success_count > 0:
            graph.save_graph()
            print(f"\n💾 Saved {success_count} changes to graph")
    
    def create_narrative_connections(self):
        """Interactively create connections between poems."""
        graph = self.load_graph()
        
        print("🔗 CREATE NARRATIVE CONNECTIONS")
        print("-" * 40)
        
        # Show available poems
        all_poems = [(node_id, data) for node_id, data in graph.graph.nodes(data=True) 
                    if data.get("type") == "poem"]
        
        print("Available poems:")
        for i, (poem_id, poem_data) in enumerate(all_poems, 1):
            title = poem_data.get("title", "Untitled")[:40]
            role = poem_data.get("narrative_role", "unassigned")
            print(f"  {i:2}. [{poem_id}] {title} ({role})")
        
        try:
            print("\n" + "="*50)
            source_id = input("Source poem ID (often core poem): ").strip()
            target_id = input("Target poem ID (extension/response): ").strip()
            
            if not source_id or not target_id:
                print("❌ Both poem IDs are required")
                return
            
            connection_types = [
                "narrative_extension", "thematic_echo", "response", 
                "variation", "contrast", "development"
            ]
            
            print(f"\\nConnection types:")
            for i, conn_type in enumerate(connection_types, 1):
                print(f"  {i}. {conn_type}")
            
            try:
                choice = int(input("Choose connection type (1-6): "))
                connection_type = connection_types[choice - 1]
            except (ValueError, IndexError):
                connection_type = "narrative_extension"
                print(f"Using default: {connection_type}")
            
            try:
                strength = float(input("Connection strength (0.0-1.0, default 0.8): ") or "0.8")
            except ValueError:
                strength = 0.8
            
            notes = input("Notes (optional): ").strip() or None
            
            if graph.create_narrative_connection(source_id, target_id, connection_type, strength, notes):
                print(f"✅ Created connection: {source_id} → {target_id}")
                graph.save_graph()
                print("💾 Saved changes")
            else:
                print("❌ Failed to create connection")
        
        except EOFError:
            print("\\n❌ Cancelled")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def convert_route_poems_to_extensions(self):
        """Convert selected route poems to narrative extensions."""
        graph = self.load_graph()
        
        print("🔄 CONVERT ROUTE POEMS TO EXTENSIONS")
        print("-" * 40)
        
        route_poems = graph.get_route_generated_poems()
        
        if not route_poems:
            print("❌ No route-generated poems found")
            return
        
        print("Route-generated poems:")
        for i, poem in enumerate(route_poems, 1):
            title = poem.get("title", "Untitled")[:50]
            route_id = poem.get("route_id", "Unknown")
            poem_id = None
            # Find the poem ID
            for node_id, node_data in graph.graph.nodes(data=True):
                if (node_data.get("type") == "poem" and 
                    node_data.get("title") == poem.get("title")):
                    poem_id = node_id
                    break
            
            print(f"  {i:2}. [{poem_id}] {title} (Route: {route_id})")
        
        try:
            selections = input("\\nEnter poem numbers to convert (comma-separated): ").strip()
            if not selections:
                print("❌ No selection made")
                return
            
            selected_indices = [int(x.strip()) - 1 for x in selections.split(",")]
            
            success_count = 0
            for idx in selected_indices:
                if 0 <= idx < len(route_poems):
                    poem = route_poems[idx]
                    # Find poem ID
                    poem_id = None
                    for node_id, node_data in graph.graph.nodes(data=True):
                        if (node_data.get("type") == "poem" and 
                            node_data.get("title") == poem.get("title")):
                            poem_id = node_id
                            break
                    
                    if poem_id and graph.mark_poem_as_extension(poem_id):
                        print(f"✅ Converted: {poem.get('title', 'Untitled')}")
                        success_count += 1
            
            if success_count > 0:
                graph.save_graph()
                print(f"\\n💾 Converted {success_count} poems to extensions")
        
        except (ValueError, EOFError) as e:
            print(f"❌ Invalid input: {e}")
    
    def remove_poems(self):
        """Interactively remove poems from the graph."""
        graph = self.load_graph()
        
        print("🗑️  REMOVE POEMS FROM GRAPH")
        print("-" * 40)
        
        # Show available poems
        all_poems = [(node_id, data) for node_id, data in graph.graph.nodes(data=True) 
                    if data.get("type") == "poem"]
        
        if not all_poems:
            print("❌ No poems found in graph")
            return
        
        print("Available poems:")
        for i, (poem_id, poem_data) in enumerate(all_poems, 1):
            title = poem_data.get("title", "Untitled")[:50]
            role = poem_data.get("narrative_role", "unassigned")
            route_id = poem_data.get("route_id", "Unknown")
            print(f"  {i:2}. [{poem_id}] {title}")
            print(f"      Role: {role} | Route: {route_id}")
        
        try:
            selections = input("\\nEnter poem numbers to remove (comma-separated): ").strip()
            if not selections:
                print("❌ No selection made")
                return
            
            selected_indices = [int(x.strip()) - 1 for x in selections.split(",")]
            cleanup = input("\\nRemove orphaned themes/imagery? (y/n) [y]: ").lower().strip()
            cleanup_orphans = cleanup != 'n'
            
            print("\\n" + "="*50)
            print("⚠️  CONFIRM DELETION")
            print("="*50)
            
            poems_to_remove = []
            for idx in selected_indices:
                if 0 <= idx < len(all_poems):
                    poem_id, poem_data = all_poems[idx]
                    title = poem_data.get("title", "Untitled")
                    role = poem_data.get("narrative_role", "unassigned")
                    poems_to_remove.append((poem_id, title, role))
            
            if not poems_to_remove:
                print("❌ No valid poems selected")
                return
            
            print("Poems to be removed:")
            for poem_id, title, role in poems_to_remove:
                print(f"  • {title} ({role}) [{poem_id}]")
            
            confirm = input(f"\\nConfirm removal of {len(poems_to_remove)} poem(s)? (yes/no): ").lower().strip()
            if confirm != "yes":
                print("❌ Removal cancelled")
                return
            
            removed_count = 0
            for poem_id, title, role in poems_to_remove:
                if graph.remove_poem(poem_id, cleanup_orphaned_entities=cleanup_orphans):
                    print(f"✅ Removed: {title}")
                    removed_count += 1
                else:
                    print(f"❌ Failed to remove: {title}")
            
            if removed_count > 0:
                graph.save_graph()
                print(f"\\n💾 Removed {removed_count} poems from graph")
        
        except (ValueError, EOFError) as e:
            print(f"❌ Invalid input: {e}")
    
    def clear_narrative_roles(self):
        """Clear narrative roles from selected poems."""
        graph = self.load_graph()
        
        print("🔄 CLEAR NARRATIVE ROLES")
        print("-" * 40)
        
        # Show poems with assigned roles
        assigned_poems = [(node_id, data) for node_id, data in graph.graph.nodes(data=True) 
                         if (data.get("type") == "poem" and 
                             data.get("narrative_role") and 
                             data.get("narrative_role") != "unassigned")]
        
        if not assigned_poems:
            print("❌ No poems with assigned narrative roles found")
            return
        
        print("Poems with narrative roles:")
        for i, (poem_id, poem_data) in enumerate(assigned_poems, 1):
            title = poem_data.get("title", "Untitled")[:50]
            role = poem_data.get("narrative_role", "unassigned")
            print(f"  {i:2}. [{poem_id}] {title} ({role})")
        
        try:
            selections = input("\\nEnter poem numbers to clear roles (comma-separated): ").strip()
            if not selections:
                print("❌ No selection made")
                return
            
            selected_indices = [int(x.strip()) - 1 for x in selections.split(",")]
            
            success_count = 0
            for idx in selected_indices:
                if 0 <= idx < len(assigned_poems):
                    poem_id, poem_data = assigned_poems[idx]
                    title = poem_data.get("title", "Untitled")
                    
                    if graph.clear_narrative_role(poem_id):
                        print(f"✅ Cleared role: {title}")
                        success_count += 1
                    else:
                        print(f"❌ Failed to clear: {title}")
            
            if success_count > 0:
                graph.save_graph()
                print(f"\\n💾 Cleared {success_count} narrative roles")
        
        except (ValueError, EOFError) as e:
            print(f"❌ Invalid input: {e}")
    
    def remove_narrative_connections(self):
        """Remove narrative connections between poems."""
        graph = self.load_graph()
        
        print("🔗❌ REMOVE NARRATIVE CONNECTIONS")
        print("-" * 40)
        
        # Find all narrative connections
        connections = []
        for u, v, data in graph.graph.edges(data=True):
            if data.get("type") == "narrative_connection":
                source_title = graph.graph.nodes[u].get("title", u)
                target_title = graph.graph.nodes[v].get("title", v)
                conn_type = data.get("connection_type", "unknown")
                connections.append((u, v, source_title, target_title, conn_type))
        
        if not connections:
            print("❌ No narrative connections found")
            return
        
        print("Current narrative connections:")
        for i, (source_id, target_id, source_title, target_title, conn_type) in enumerate(connections, 1):
            print(f"  {i:2}. {source_title[:30]} → {target_title[:30]} ({conn_type})")
            print(f"      {source_id} → {target_id}")
        
        try:
            selections = input("\\nEnter connection numbers to remove (comma-separated): ").strip()
            if not selections:
                print("❌ No selection made")
                return
            
            selected_indices = [int(x.strip()) - 1 for x in selections.split(",")]
            
            removed_count = 0
            for idx in selected_indices:
                if 0 <= idx < len(connections):
                    source_id, target_id, source_title, target_title, conn_type = connections[idx]
                    
                    if graph.remove_narrative_connection(source_id, target_id):
                        print(f"✅ Removed connection: {source_title[:30]} → {target_title[:30]}")
                        removed_count += 1
                    else:
                        print(f"❌ Failed to remove: {source_title[:30]} → {target_title[:30]}")
            
            if removed_count > 0:
                graph.save_graph()
                print(f"\\n💾 Removed {removed_count} narrative connections")
        
        except (ValueError, EOFError) as e:
            print(f"❌ Invalid input: {e}")
    
    def remove_by_narrative_role(self):
        """Remove all poems of a specific narrative role."""
        graph = self.load_graph()
        
        print("🎯❌ REMOVE POEMS BY NARRATIVE ROLE")
        print("-" * 40)
        
        # Count poems by role
        role_counts = {}
        for node_id, node_data in graph.graph.nodes(data=True):
            if node_data.get("type") == "poem":
                role = node_data.get("narrative_role", "unassigned")
                role_counts[role] = role_counts.get(role, 0) + 1
        
        if not role_counts:
            print("❌ No poems found")
            return
        
        print("Available narrative roles:")
        roles = list(role_counts.keys())
        for i, role in enumerate(roles, 1):
            count = role_counts[role]
            print(f"  {i}. {role}: {count} poem(s)")
        
        try:
            choice = int(input("\\nChoose role to remove (number): ")) - 1
            if choice < 0 or choice >= len(roles):
                print("❌ Invalid choice")
                return
            
            role_to_remove = roles[choice]
            count = role_counts[role_to_remove]
            
            print(f"\\n⚠️  This will remove ALL {count} poem(s) with role '{role_to_remove}'")
            confirm = input("Type 'DELETE' to confirm: ").strip()
            
            if confirm != "DELETE":
                print("❌ Removal cancelled")
                return
            
            def confirm_each_removal(poem_id, title, role):
                response = input(f"Remove '{title}' ({role})? (y/n) [y]: ").lower().strip()
                return response != 'n'
            
            confirm_each = input("\\nConfirm each removal individually? (y/n) [n]: ").lower().strip()
            callback = confirm_each_removal if confirm_each == 'y' else None
            
            removed_count = graph.remove_poems_by_narrative_role(role_to_remove, callback)
            
            if removed_count > 0:
                graph.save_graph()
                print(f"\\n💾 Removed {removed_count} poems with role '{role_to_remove}'")
            else:
                print("❌ No poems were removed")
        
        except (ValueError, EOFError) as e:
            print(f"❌ Invalid input: {e}")
    
    def interactive_menu(self):
        """Show an interactive menu for narrative management."""
        print("🎭 NARRATIVE MANAGER - Interactive Mode")
        print("=" * 50)
        
        while True:
            print("\\n📋 MAIN MENU")
            print("=" * 20)
            print("1. View narrative status")
            print("2. Mark poems as core narrative")
            print("3. Mark poems as extensions")
            print("4. Create narrative connections")
            print("5. Show detailed narrative tree")
            print("6. Export narrative report")
            print("7. Remove individual poems")
            print("8. Clear narrative roles")
            print("9. Remove narrative connections")
            print("10. Remove poems by narrative role")
            print("0. Exit")
            
            try:
                choice = input("\\nChoose an option (0-10): ").strip()
                
                if choice == "0":
                    print("👋 Goodbye!")
                    break
                elif choice == "1":
                    self.show_narrative_status()
                elif choice == "2":
                    self.mark_poems_as_core_interactive()
                elif choice == "3":
                    self.mark_poems_as_extension_interactive()
                elif choice == "4":
                    self.create_narrative_connections()
                elif choice == "5":
                    self.show_detailed_narrative_tree()
                elif choice == "6":
                    self.export_narrative_report()
                elif choice == "7":
                    self.remove_poems()
                elif choice == "8":
                    self.clear_narrative_roles()
                elif choice == "9":
                    self.remove_narrative_connections()
                elif choice == "10":
                    self.remove_by_narrative_role()
                else:
                    print("❌ Invalid choice. Please try again.")
                    
                if choice != "0":
                    input("\\nPress Enter to continue...")
                    
            except (KeyboardInterrupt, EOFError):
                print("\\n\\n👋 Goodbye!")
                break


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Narrative Management Tool")
    parser.add_argument("--status", action="store_true", help="Show narrative status")
    parser.add_argument("--mark-core", nargs="+", help="Mark poems as core narrative")
    parser.add_argument("--mark-extension", nargs="+", help="Mark poems as extensions")
    parser.add_argument("--interactive", action="store_true", help="Interactive menu")
    parser.add_argument("--remove-poem", help="Remove specific poem by ID")
    parser.add_argument("--clear-role", help="Clear narrative role for specific poem by ID")
    parser.add_argument("--remove-role", help="Remove all poems with specific narrative role")
    parser.add_argument("--export-report", help="Export narrative report to file")
    
    args = parser.parse_args()
    
    manager = NarrativeManager()
    
    try:
        if args.status:
            manager.show_narrative_status()
        elif args.mark_core:
            manager.mark_poems_as_core(args.mark_core)
        elif args.mark_extension:
            manager.mark_poems_as_extension(args.mark_extension)
        elif args.remove_poem:
            graph = manager.load_graph()
            if graph.remove_poem(args.remove_poem):
                graph.save_graph()
                print(f"✅ Removed poem: {args.remove_poem}")
            else:
                print(f"❌ Failed to remove poem: {args.remove_poem}")
        elif args.clear_role:
            graph = manager.load_graph()
            if graph.clear_narrative_role(args.clear_role):
                graph.save_graph()
                print(f"✅ Cleared narrative role for: {args.clear_role}")
            else:
                print(f"❌ Failed to clear role for: {args.clear_role}")
        elif args.remove_role:
            graph = manager.load_graph()
            removed_count = graph.remove_poems_by_narrative_role(args.remove_role)
            graph.save_graph()
            print(f"✅ Removed {removed_count} poems with role '{args.remove_role}'")
        elif args.export_report:
            graph = manager.load_graph()
            graph.export_narrative_report(args.export_report)
            print(f"✅ Exported narrative report to: {args.export_report}")
        elif args.interactive:
            manager.interactive_menu()
        else:
            print("Narrative Management Tool")
            print("Use --help for options or --interactive for menu")
            print("\\nQuick commands:")
            print("  --status                        Show narrative structure")
            print("  --mark-core POEM_ID...          Mark poems as core narrative")
            print("  --mark-extension POEM_ID...     Mark poems as extensions")
            print("  --remove-poem POEM_ID           Remove specific poem")
            print("  --clear-role POEM_ID            Clear narrative role for poem")
            print("  --remove-role ROLE              Remove all poems with role")
            print("  --export-report FILE            Export narrative report")
            print("  --interactive                   Interactive menu")
    
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()