"""
Extended Poetry Knowledge Graph Manager for Tranait Project

This module extends the base poetry graph with support for:
- Sound devices (alliteration, rhyme, repetition, assonance, consonance)
- Free verse structure metrics
- Rhythmic and flow patterns

Designed for poets who work in free verse with heavy use of sound devices.
"""

import json
import pickle
from typing import List, Dict, Any, Optional, Set, Tuple
from datetime import datetime
from pathlib import Path
import networkx as nx
from collections import Counter, defaultdict


class ExtendedPoetryGraph:
    """
    Extended poetry knowledge graph with support for structural and sonic elements.
    
    The graph contains nodes of different types:
    - poem: Individual poems with metadata
    - theme: Thematic concepts (e.g., "loss", "hope", "transition")
    - imagery: Visual/sensory elements (e.g., "water", "dawn", "concrete")
    - emotion: Emotional states (e.g., "melancholic", "peaceful", "anxious")
    - sound_device: Sound patterns (e.g., "alliteration", "internal_rhyme", "repetition")
    
    Edges represent relationships:
    - poem -> theme: "has_theme"
    - poem -> imagery: "contains_imagery"
    - poem -> emotion: "conveys_emotion"
    - poem -> sound_device: "uses_sound_device"
    - poem -> poem: "narrative_connection"
    
    Additionally, poems store detailed structural metadata for free verse metrics.
    """
    
    def __init__(self, graph_path: Optional[str] = None):
        """
        Initialize the extended poetry graph.
        
        Args:
            graph_path: Path to load existing graph from (JSON or pickle)
        """
        self.graph = nx.MultiDiGraph()
        self.graph_path = graph_path
        
        if graph_path and Path(graph_path).exists():
            self.load_graph(graph_path)
    
    # ==================== CORE CRUD OPERATIONS ====================
    
    def add_poem(
        self,
        poem_id: str,
        title: str,
        text: str,
        route_id: str,
        themes: List[str] = None,
        imagery: List[str] = None,
        emotions: List[str] = None,
        sound_devices: List[str] = None,
        structure_metadata: Dict[str, Any] = None,
        sound_metadata: Dict[str, Any] = None,
        metadata: Dict[str, Any] = None,
        narrative_role: str = "route_generated"
    ) -> None:
        """
        Add a poem to the graph with its associated elements.
        
        Args:
            poem_id: Unique identifier for the poem
            title: Poem title
            text: Full text of the poem
            route_id: MARTA route that created this poem
            themes: List of themes present in the poem
            imagery: List of imagery/symbols present
            emotions: List of emotions conveyed
            sound_devices: List of sound devices used (alliteration, rhyme, etc.)
            structure_metadata: Free verse structure metrics
            sound_metadata: Detailed sound pattern information
            metadata: Additional metadata (timestamp, etc.)
            narrative_role: Role in narrative ("core", "route_generated", "extension", "variation")
        """
        # Combine all metadata
        full_metadata = metadata or {}
        if structure_metadata:
            full_metadata["structure"] = structure_metadata
        if sound_metadata:
            full_metadata["sound_patterns"] = sound_metadata
        
        # Add poem node
        self.graph.add_node(
            poem_id,
            type="poem",
            title=title,
            text=text,
            route_id=route_id,
            created_at=datetime.now().isoformat(),
            narrative_role=narrative_role,
            metadata=full_metadata
        )
        
        # Add and connect themes
        for theme in (themes or []):
            theme_id = f"theme_{theme.lower().replace(' ', '_')}"
            self._add_or_update_entity(theme_id, "theme", theme)
            self.graph.add_edge(poem_id, theme_id, type="has_theme")
        
        # Add and connect imagery
        for image in (imagery or []):
            image_id = f"img_{image.lower().replace(' ', '_')}"
            self._add_or_update_entity(image_id, "imagery", image)
            self.graph.add_edge(poem_id, image_id, type="contains_imagery")
        
        # Add and connect emotions
        for emotion in (emotions or []):
            emotion_id = f"emo_{emotion.lower().replace(' ', '_')}"
            self._add_or_update_entity(emotion_id, "emotion", emotion)
            self.graph.add_edge(poem_id, emotion_id, type="conveys_emotion")
        
        # Add and connect sound devices (NEW)
        for sound_device in (sound_devices or []):
            device_id = f"sound_{sound_device.lower().replace(' ', '_')}"
            self._add_or_update_entity(device_id, "sound_device", sound_device)
            self.graph.add_edge(poem_id, device_id, type="uses_sound_device")
    
    def _add_or_update_entity(self, entity_id: str, entity_type: str, name: str) -> None:
        """Add an entity node or update its usage count if it exists."""
        if self.graph.has_node(entity_id):
            self.graph.nodes[entity_id]["usage_count"] += 1
        else:
            self.graph.add_node(
                entity_id,
                type=entity_type,
                name=name,
                usage_count=1,
                created_at=datetime.now().isoformat()
            )
    
    def add_narrative_connection(
        self,
        poem_id_1: str,
        poem_id_2: str,
        connection_type: str = "narrative",
        strength: float = 1.0,
        notes: str = None
    ) -> None:
        """Create a narrative connection between two poems."""
        self.graph.add_edge(
            poem_id_1,
            poem_id_2,
            type="narrative_connection",
            connection_type=connection_type,
            strength=strength,
            notes=notes,
            created_at=datetime.now().isoformat()
        )
    
    def get_poem(self, poem_id: str) -> Optional[Dict[str, Any]]:
        """Get full poem data including all connections."""
        if not self.graph.has_node(poem_id):
            return None
        
        node_data = dict(self.graph.nodes[poem_id])
        
        # Get connected entities
        node_data["themes"] = self._get_connected_entities(poem_id, "theme")
        node_data["imagery"] = self._get_connected_entities(poem_id, "imagery")
        node_data["emotions"] = self._get_connected_entities(poem_id, "emotion")
        node_data["sound_devices"] = self._get_connected_entities(poem_id, "sound_device")
        node_data["narrative_connections"] = self._get_narrative_connections(poem_id)
        
        return node_data
    
    def _get_connected_entities(self, poem_id: str, entity_type: str) -> List[str]:
        """Get all entities of a specific type connected to a poem."""
        entities = []
        for neighbor in self.graph.neighbors(poem_id):
            if self.graph.nodes[neighbor].get("type") == entity_type:
                entities.append(self.graph.nodes[neighbor]["name"])
        return entities
    
    def _get_narrative_connections(self, poem_id: str) -> List[Dict[str, Any]]:
        """Get all narrative connections for a poem."""
        connections = []
        for successor in self.graph.successors(poem_id):
            if self.graph.nodes[successor].get("type") == "poem":
                edge_data = self.graph.get_edge_data(poem_id, successor)
                for key, data in edge_data.items():
                    if data.get("type") == "narrative_connection":
                        connections.append({
                            "target_poem_id": successor,
                            "connection_type": data.get("connection_type"),
                            "strength": data.get("strength"),
                            "notes": data.get("notes")
                        })
        return connections
    
    # ==================== QUERY OPERATIONS (BASE) ====================
    
    def get_canonical_themes(self, min_frequency: int = 3) -> List[Dict[str, Any]]:
        """Get themes used frequently across the corpus."""
        return self._get_entities_by_frequency("theme", min_frequency, None)
    
    def get_rare_imagery(self, max_frequency: int = 2) -> List[Dict[str, Any]]:
        """Get imagery that's rarely used."""
        return self._get_entities_by_frequency("imagery", 0, max_frequency)
    
    def get_rare_themes(self, max_frequency: int = 2) -> List[Dict[str, Any]]:
        """Get themes that are underutilized."""
        return self._get_entities_by_frequency("theme", 0, max_frequency)
    
    def _get_entities_by_frequency(
        self,
        entity_type: str,
        min_freq: Optional[int] = None,
        max_freq: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Generic method to filter entities by usage frequency."""
        entities = []
        
        for node_id, node_data in self.graph.nodes(data=True):
            if node_data.get("type") != entity_type:
                continue
            
            usage_count = node_data.get("usage_count", 0)
            
            if min_freq is not None and usage_count < min_freq:
                continue
            if max_freq is not None and usage_count > max_freq:
                continue
            
            using_routes = self._get_routes_using_entity(node_id)
            
            entities.append({
                "id": node_id,
                "name": node_data["name"],
                "usage_count": usage_count,
                "used_by_routes": using_routes,
                "created_at": node_data.get("created_at")
            })
        
        return sorted(entities, key=lambda x: x["usage_count"], reverse=True)
    
    def _get_routes_using_entity(self, entity_id: str) -> List[str]:
        """Get list of route IDs that have used this entity."""
        routes = set()
        for predecessor in self.graph.predecessors(entity_id):
            if self.graph.nodes[predecessor].get("type") == "poem":
                route_id = self.graph.nodes[predecessor].get("route_id")
                if route_id:
                    routes.add(route_id)
        return list(routes)
    
    def get_unexplored_combinations(
        self,
        entity_type_1: str = "theme",
        entity_type_2: str = "imagery",
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Find combinations of entities that have never appeared together."""
        # Get all existing combinations
        existing_combos = set()
        for node_id, node_data in self.graph.nodes(data=True):
            if node_data.get("type") != "poem":
                continue
            
            entities_1 = [n for n in self.graph.neighbors(node_id)
                         if self.graph.nodes[n].get("type") == entity_type_1]
            entities_2 = [n for n in self.graph.neighbors(node_id)
                         if self.graph.nodes[n].get("type") == entity_type_2]
            
            for e1 in entities_1:
                for e2 in entities_2:
                    existing_combos.add((e1, e2))
        
        # Find all possible entities of each type
        all_entities_1 = [n for n, d in self.graph.nodes(data=True)
                         if d.get("type") == entity_type_1]
        all_entities_2 = [n for n, d in self.graph.nodes(data=True)
                         if d.get("type") == entity_type_2]
        
        # Find unexplored combinations
        unexplored = []
        for e1 in all_entities_1:
            for e2 in all_entities_2:
                if (e1, e2) not in existing_combos:
                    unexplored.append({
                        entity_type_1: self.graph.nodes[e1]["name"],
                        entity_type_1 + "_id": e1,
                        entity_type_2: self.graph.nodes[e2]["name"],
                        entity_type_2 + "_id": e2,
                        entity_type_1 + "_usage": self.graph.nodes[e1]["usage_count"],
                        entity_type_2 + "_usage": self.graph.nodes[e2]["usage_count"]
                    })
                    
                    if len(unexplored) >= limit:
                        return unexplored
        
        return unexplored
    
    def get_inverse_pattern(
        self,
        entity_id: str,
        pattern_type: str = "emotion"
    ) -> List[Dict[str, Any]]:
        """Find entities that could create an inversion of typical patterns."""
        if not self.graph.has_node(entity_id):
            return []
        
        # Get all patterns currently associated with this entity
        current_patterns = set()
        for predecessor in self.graph.predecessors(entity_id):
            if self.graph.nodes[predecessor].get("type") == "poem":
                for neighbor in self.graph.neighbors(predecessor):
                    if self.graph.nodes[neighbor].get("type") == pattern_type:
                        current_patterns.add(neighbor)
        
        # Get all possible patterns
        all_patterns = [n for n, d in self.graph.nodes(data=True)
                       if d.get("type") == pattern_type]
        
        # Return patterns NOT currently used
        inverse_patterns = []
        for pattern_id in all_patterns:
            if pattern_id not in current_patterns:
                inverse_patterns.append({
                    "id": pattern_id,
                    "name": self.graph.nodes[pattern_id]["name"],
                    "usage_count": self.graph.nodes[pattern_id]["usage_count"]
                })
        
        return sorted(inverse_patterns, key=lambda x: x["usage_count"], reverse=True)
    
    # ==================== SOUND DEVICE QUERIES (NEW) ====================
    
    def get_canonical_sound_devices(self, min_frequency: int = 3) -> List[Dict[str, Any]]:
        """
        Get sound devices used frequently across the corpus.
        Reveals the dominant sonic patterns in the collection.
        """
        return self._get_entities_by_frequency("sound_device", min_frequency, None)
    
    def get_rare_sound_devices(self, max_frequency: int = 2) -> List[Dict[str, Any]]:
        """
        Get rarely used sound devices.
        Useful for routes wanting to explore underutilized sonic techniques.
        """
        return self._get_entities_by_frequency("sound_device", 0, max_frequency)
    
    def get_poems_with_sound_device(
        self,
        sound_device: str
    ) -> List[Dict[str, Any]]:
        """
        Get all poems that use a specific sound device.
        
        Args:
            sound_device: Name of the sound device (e.g., "alliteration", "internal_rhyme")
        
        Returns:
            List of poem dictionaries
        """
        device_id = f"sound_{sound_device.lower().replace(' ', '_')}"
        
        if not self.graph.has_node(device_id):
            return []
        
        poems = []
        for predecessor in self.graph.predecessors(device_id):
            if self.graph.nodes[predecessor].get("type") == "poem":
                poems.append(self.get_poem(predecessor))
        
        return poems
    
    def get_poems_without_sound_device(
        self,
        sound_device: str
    ) -> List[Dict[str, Any]]:
        """
        Get all poems that DON'T use a specific sound device.
        Useful for rebellious routes wanting to avoid certain patterns.
        """
        device_id = f"sound_{sound_device.lower().replace(' ', '_')}"
        
        # Get all poems with this device
        poems_with = set()
        if self.graph.has_node(device_id):
            for predecessor in self.graph.predecessors(device_id):
                if self.graph.nodes[predecessor].get("type") == "poem":
                    poems_with.add(predecessor)
        
        # Get all poems without it
        poems_without = []
        for node_id, node_data in self.graph.nodes(data=True):
            if node_data.get("type") == "poem" and node_id not in poems_with:
                poems_without.append(self.get_poem(node_id))
        
        return poems_without
    
    def get_sound_device_co_occurrence_with_theme(
        self,
        theme: str
    ) -> Dict[str, int]:
        """
        Find which sound devices typically appear with a given theme.
        
        Example: Does "alliteration" often appear with "urban_life" theme?
        """
        theme_id = f"theme_{theme.lower().replace(' ', '_')}"
        
        if not self.graph.has_node(theme_id):
            return {}
        
        sound_devices = Counter()
        
        # Get all poems with this theme
        for predecessor in self.graph.predecessors(theme_id):
            if self.graph.nodes[predecessor].get("type") == "poem":
                # Get sound devices for this poem
                for neighbor in self.graph.neighbors(predecessor):
                    if self.graph.nodes[neighbor].get("type") == "sound_device":
                        device_name = self.graph.nodes[neighbor]["name"]
                        sound_devices[device_name] += 1
        
        return dict(sound_devices)
    
    def get_common_sound_patterns(self) -> Dict[str, Any]:
        """
        Analyze the most common sound device combinations.
        
        Returns:
            Dictionary with canonical sound patterns
        """
        # Track which sound devices appear together in poems
        device_pairs = Counter()
        
        for node_id, node_data in self.graph.nodes(data=True):
            if node_data.get("type") != "poem":
                continue
            
            devices = [
                self.graph.nodes[n]["name"]
                for n in self.graph.neighbors(node_id)
                if self.graph.nodes[n].get("type") == "sound_device"
            ]
            
            # Count pairs
            for i, d1 in enumerate(devices):
                for d2 in devices[i+1:]:
                    pair = tuple(sorted([d1, d2]))
                    device_pairs[pair] += 1
        
        return {
            "common_pairs": dict(device_pairs.most_common(10)),
            "canonical_devices": [d["name"] for d in self.get_canonical_sound_devices(min_frequency=3)]
        }
    
    # ==================== STRUCTURE QUERIES (NEW) ====================
    
    def get_free_verse_metrics_by_route(self, route_id: str) -> Dict[str, Any]:
        """
        Analyze free verse structural patterns for a specific route.
        
        Returns metrics like:
        - Average line count
        - Line length variation
        - Stanza break patterns
        - Enjambment frequency
        """
        poems = [
            (node_id, node_data)
            for node_id, node_data in self.graph.nodes(data=True)
            if node_data.get("type") == "poem" and node_data.get("route_id") == route_id
        ]
        
        if not poems:
            return {"route_id": route_id, "poem_count": 0}
        
        metrics = {
            "route_id": route_id,
            "poem_count": len(poems),
            "line_counts": [],
            "avg_line_length": [],
            "stanza_patterns": [],
            "enjambment_usage": []
        }
        
        for poem_id, poem_data in poems:
            structure = poem_data.get("metadata", {}).get("structure", {})
            
            if "line_count" in structure:
                metrics["line_counts"].append(structure["line_count"])
            
            if "line_lengths" in structure:
                avg_len = sum(structure["line_lengths"]) / len(structure["line_lengths"])
                metrics["avg_line_length"].append(avg_len)
            
            if "stanza_breaks" in structure:
                metrics["stanza_patterns"].append(tuple(structure["stanza_breaks"]))
        
        # Calculate averages
        if metrics["line_counts"]:
            metrics["avg_line_count"] = sum(metrics["line_counts"]) / len(metrics["line_counts"])
        
        if metrics["avg_line_length"]:
            metrics["overall_avg_line_length"] = sum(metrics["avg_line_length"]) / len(metrics["avg_line_length"])
        
        return metrics
    
    def get_structural_diversity_score(self, route_id: str) -> float:
        """
        Calculate how structurally diverse a route's poems are.
        
        Returns:
            Score from 0.0 (all poems identical structure) to 1.0 (maximally diverse)
        """
        metrics = self.get_free_verse_metrics_by_route(route_id)
        
        if metrics["poem_count"] < 2:
            return 0.0
        
        # Measure variation in line counts
        line_counts = metrics.get("line_counts", [])
        if len(line_counts) < 2:
            return 0.0
        
        # Calculate coefficient of variation
        mean_lines = sum(line_counts) / len(line_counts)
        variance = sum((x - mean_lines) ** 2 for x in line_counts) / len(line_counts)
        std_dev = variance ** 0.5
        
        if mean_lines == 0:
            return 0.0
        
        coefficient_of_variation = std_dev / mean_lines
        
        # Normalize to 0-1 range (assuming CoV rarely exceeds 0.5 in poetry)
        return min(coefficient_of_variation * 2, 1.0)
    
    # ==================== ROUTE STATISTICS (EXTENDED) ====================
    
    def get_route_statistics(self, route_id: str) -> Dict[str, Any]:
        """Get comprehensive statistics about a route's contributions."""
        poems = [n for n, d in self.graph.nodes(data=True)
                if d.get("type") == "poem" and d.get("route_id") == route_id]
        
        if not poems:
            return {
                "route_id": route_id,
                "poem_count": 0,
                "themes": {},
                "imagery": {},
                "emotions": {},
                "sound_devices": {}
            }
        
        themes = Counter()
        imagery = Counter()
        emotions = Counter()
        sound_devices = Counter()
        
        for poem_id in poems:
            for neighbor in self.graph.neighbors(poem_id):
                node_type = self.graph.nodes[neighbor].get("type")
                name = self.graph.nodes[neighbor]["name"]
                
                if node_type == "theme":
                    themes[name] += 1
                elif node_type == "imagery":
                    imagery[name] += 1
                elif node_type == "emotion":
                    emotions[name] += 1
                elif node_type == "sound_device":
                    sound_devices[name] += 1
        
        # Add structural metrics
        structure_metrics = self.get_free_verse_metrics_by_route(route_id)
        
        return {
            "route_id": route_id,
            "poem_count": len(poems),
            "themes": dict(themes.most_common()),
            "imagery": dict(imagery.most_common()),
            "emotions": dict(emotions.most_common()),
            "sound_devices": dict(sound_devices.most_common()),
            "structure_metrics": structure_metrics,
            "structural_diversity": self.get_structural_diversity_score(route_id)
        }
    
    # ==================== PERSISTENCE ====================
    
    def save_graph(self, path: Optional[str] = None, format: str = "json") -> None:
        """Save the graph to disk."""
        save_path = path or self.graph_path
        if not save_path:
            raise ValueError("No path provided and no default path set")
        
        if format == "json":
            data = nx.node_link_data(self.graph)
            with open(save_path, 'w') as f:
                json.dump(data, f, indent=2)
        elif format == "pickle":
            with open(save_path, 'wb') as f:
                pickle.dump(self.graph, f)
        else:
            raise ValueError(f"Unknown format: {format}")
    
    def load_graph(self, path: str, format: str = None) -> None:
        """Load graph from disk."""
        if format is None:
            format = "pickle" if path.endswith(".pkl") else "json"
        
        if format == "json":
            with open(path, 'r') as f:
                data = json.load(f)
            self.graph = nx.node_link_graph(data, directed=True, multigraph=True)
        elif format == "pickle":
            with open(path, 'rb') as f:
                self.graph = pickle.load(f)
        else:
            raise ValueError(f"Unknown format: {format}")
        
        self.graph_path = path
    
    def export_to_dict(self) -> Dict[str, Any]:
        """Export graph to a simple dictionary format for API responses."""
        return {
            "nodes": [
                {
                    "id": node_id,
                    **node_data
                }
                for node_id, node_data in self.graph.nodes(data=True)
            ],
            "edges": [
                {
                    "source": source,
                    "target": target,
                    **edge_data
                }
                for source, target, edge_data in self.graph.edges(data=True)
            ],
            "stats": {
                "total_nodes": self.graph.number_of_nodes(),
                "total_edges": self.graph.number_of_edges(),
                "poem_count": len([n for n, d in self.graph.nodes(data=True)
                                  if d.get("type") == "poem"]),
                "theme_count": len([n for n, d in self.graph.nodes(data=True)
                                   if d.get("type") == "theme"]),
                "imagery_count": len([n for n, d in self.graph.nodes(data=True)
                                     if d.get("type") == "imagery"]),
                "emotion_count": len([n for n, d in self.graph.nodes(data=True)
                                     if d.get("type") == "emotion"]),
                "sound_device_count": len([n for n, d in self.graph.nodes(data=True)
                                          if d.get("type") == "sound_device"])
            }
        }
    
    def get_graph_summary(self) -> Dict[str, Any]:
        """Get a high-level summary of the graph."""
        poems = [n for n, d in self.graph.nodes(data=True) if d.get("type") == "poem"]
        themes = [n for n, d in self.graph.nodes(data=True) if d.get("type") == "theme"]
        imagery = [n for n, d in self.graph.nodes(data=True) if d.get("type") == "imagery"]
        emotions = [n for n, d in self.graph.nodes(data=True) if d.get("type") == "emotion"]
        sound_devices = [n for n, d in self.graph.nodes(data=True) if d.get("type") == "sound_device"]
        
        routes = set()
        for node_id in poems:
            route_id = self.graph.nodes[node_id].get("route_id")
            if route_id:
                routes.add(route_id)
        
        return {
            "total_poems": len(poems),
            "total_themes": len(themes),
            "total_imagery": len(imagery),
            "total_emotions": len(emotions),
            "total_sound_devices": len(sound_devices),
            "contributing_routes": len(routes),
            "total_connections": self.graph.number_of_edges(),
            **self.get_narrative_summary()  # Include narrative breakdown
        }
    
    def get_entity_co_occurrence(
        self,
        entity_type_1: str,
        entity_type_2: str
    ) -> Dict[Tuple[str, str], int]:
        """Get co-occurrence counts for pairs of entity types."""
        co_occurrences = defaultdict(int)
        
        for node_id, node_data in self.graph.nodes(data=True):
            if node_data.get("type") != "poem":
                continue
            
            entities_1 = [self.graph.nodes[n]["name"] for n in self.graph.neighbors(node_id)
                         if self.graph.nodes[n].get("type") == entity_type_1]
            entities_2 = [self.graph.nodes[n]["name"] for n in self.graph.neighbors(node_id)
                         if self.graph.nodes[n].get("type") == entity_type_2]
            
            for e1 in entities_1:
                for e2 in entities_2:
                    co_occurrences[(e1, e2)] += 1
        
        return dict(co_occurrences)
    
    # ==================== NARRATIVE MANAGEMENT ====================
    
    def mark_poem_as_core(self, poem_id: str) -> bool:
        """Mark a poem as part of the core narrative."""
        return self._set_narrative_role(poem_id, "core")
    
    def mark_poem_as_extension(self, poem_id: str) -> bool:
        """Mark a poem as an extension of the core narrative."""
        return self._set_narrative_role(poem_id, "extension")
    
    def mark_poem_as_variation(self, poem_id: str) -> bool:
        """Mark a poem as a variation on existing themes."""
        return self._set_narrative_role(poem_id, "variation")
    
    def _set_narrative_role(self, poem_id: str, role: str) -> bool:
        """Set the narrative role for a poem."""
        if not self.graph.has_node(poem_id):
            return False
        
        node_data = self.graph.nodes[poem_id]
        if node_data.get("type") != "poem":
            return False
        
        self.graph.nodes[poem_id]["narrative_role"] = role
        return True
    
    def get_core_poems(self) -> List[Dict[str, Any]]:
        """Get all poems marked as core narrative."""
        return self._get_poems_by_narrative_role("core")
    
    def get_extension_poems(self) -> List[Dict[str, Any]]:
        """Get all poems that extend the core narrative."""
        return self._get_poems_by_narrative_role("extension")
    
    def get_route_generated_poems(self) -> List[Dict[str, Any]]:
        """Get all route-generated poems."""
        return self._get_poems_by_narrative_role("route_generated")
    
    def _get_poems_by_narrative_role(self, role: str) -> List[Dict[str, Any]]:
        """Get poems by their narrative role."""
        poems = []
        for node_id, node_data in self.graph.nodes(data=True):
            if (node_data.get("type") == "poem" and 
                node_data.get("narrative_role") == role):
                
                full_poem_data = self.get_poem(node_id)
                poems.append(full_poem_data)
        
        # Sort by creation date
        poems.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return poems
    
    def create_narrative_connection(
        self,
        source_poem_id: str,
        target_poem_id: str,
        connection_type: str = "narrative_extension",
        strength: float = 1.0,
        notes: str = None
    ) -> bool:
        """
        Create a narrative connection between poems.
        
        Args:
            source_poem_id: Source poem (often core narrative)
            target_poem_id: Target poem (often extension/variation)
            connection_type: Type of connection ("narrative_extension", "thematic_echo", "response", etc.)
            strength: Connection strength (0.0 to 1.0)
            notes: Optional notes about the connection
        """
        if not (self.graph.has_node(source_poem_id) and self.graph.has_node(target_poem_id)):
            return False
        
        self.graph.add_edge(
            source_poem_id,
            target_poem_id,
            type="narrative_connection",
            connection_type=connection_type,
            strength=strength,
            notes=notes,
            created_at=datetime.now().isoformat()
        )
        return True
    
    def get_narrative_summary(self) -> Dict[str, Any]:
        """Get a summary of the narrative structure."""
        core_poems = self.get_core_poems()
        extension_poems = self.get_extension_poems()
        route_poems = self.get_route_generated_poems()
        variation_poems = self._get_poems_by_narrative_role("variation")
        
        # Count narrative connections
        narrative_connections = 0
        for u, v, data in self.graph.edges(data=True):
            if data.get("type") == "narrative_connection":
                narrative_connections += 1
        
        return {
            "core_poems": len(core_poems),
            "extension_poems": len(extension_poems),
            "route_generated_poems": len(route_poems),
            "variation_poems": len(variation_poems),
            "narrative_connections": narrative_connections,
            "core_poem_titles": [p.get("title", "Untitled") for p in core_poems],
            "latest_core_poem": core_poems[0] if core_poems else None,
            "total_narrative_poems": len(core_poems) + len(extension_poems)
        }
    
    def remove_poem(self, poem_id: str, cleanup_orphaned_entities: bool = True) -> bool:
        """
        Remove a poem and optionally clean up orphaned entities.
        
        Args:
            poem_id: ID of the poem to remove
            cleanup_orphaned_entities: Remove themes/imagery/etc that become unused
        
        Returns:
            True if poem was removed, False if not found
        """
        if not self.graph.has_node(poem_id):
            return False
        
        node_data = self.graph.nodes[poem_id]
        if node_data.get("type") != "poem":
            return False
        
        # Get connected entities before removing poem
        connected_entities = []
        if cleanup_orphaned_entities:
            for neighbor in list(self.graph.neighbors(poem_id)):
                neighbor_data = self.graph.nodes[neighbor]
                entity_type = neighbor_data.get("type")
                if entity_type in ["theme", "imagery", "emotion", "sound_device"]:
                    connected_entities.append((neighbor, entity_type))
        
        # Remove the poem node (automatically removes all edges)
        self.graph.remove_node(poem_id)
        
        # Clean up orphaned entities if requested
        if cleanup_orphaned_entities:
            for entity_id, entity_type in connected_entities:
                if self.graph.has_node(entity_id):
                    # Check if any other poems are connected to this entity
                    has_poem_connections = any(
                        self.graph.nodes[n].get("type") == "poem" 
                        for n in self.graph.neighbors(entity_id)
                    )
                    
                    # Remove entity if no poems use it
                    if not has_poem_connections:
                        self.graph.remove_node(entity_id)
        
        return True
    
    def remove_narrative_connection(self, source_poem_id: str, target_poem_id: str) -> bool:
        """Remove narrative connection between two poems."""
        if not (self.graph.has_node(source_poem_id) and self.graph.has_node(target_poem_id)):
            return False
        
        # Remove narrative connection edges
        if self.graph.has_edge(source_poem_id, target_poem_id):
            edge_data = self.graph.get_edge_data(source_poem_id, target_poem_id)
            edges_to_remove = []
            
            for key, data in edge_data.items():
                if data.get("type") == "narrative_connection":
                    edges_to_remove.append(key)
            
            for key in edges_to_remove:
                self.graph.remove_edge(source_poem_id, target_poem_id, key)
                
            return len(edges_to_remove) > 0
        
        return False
    
    def clear_narrative_role(self, poem_id: str) -> bool:
        """Clear/reset the narrative role of a poem to unassigned."""
        if not self.graph.has_node(poem_id):
            return False
        
        node_data = self.graph.nodes[poem_id]
        if node_data.get("type") != "poem":
            return False
        
        # Remove narrative_role or set to None
        if "narrative_role" in self.graph.nodes[poem_id]:
            del self.graph.nodes[poem_id]["narrative_role"]
        
        return True
    
    def remove_poems_by_narrative_role(self, role: str, confirm_callback=None) -> int:
        """
        Remove all poems with a specific narrative role.
        
        Args:
            role: Narrative role to remove ("core", "extension", etc.)
            confirm_callback: Optional function to confirm each removal
        
        Returns:
            Number of poems removed
        """
        poems_to_remove = []
        
        for node_id, node_data in self.graph.nodes(data=True):
            if (node_data.get("type") == "poem" and 
                node_data.get("narrative_role") == role):
                poems_to_remove.append((node_id, node_data))
        
        removed_count = 0
        for poem_id, poem_data in poems_to_remove:
            should_remove = True
            
            if confirm_callback:
                title = poem_data.get("title", "Untitled")
                should_remove = confirm_callback(poem_id, title, role)
            
            if should_remove and self.remove_poem(poem_id):
                removed_count += 1
        
        return removed_count
    
    # ==================== PATH AND NETWORK ANALYSIS ====================
    
    def find_shortest_path_poems(
        self,
        poem_id_1: str,
        poem_id_2: str
    ) -> Optional[List[str]]:
        """Find the shortest path between two poems through shared entities."""
        try:
            undirected = self.graph.to_undirected()
            path = nx.shortest_path(undirected, poem_id_1, poem_id_2)
            return path
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None
    
    def get_all_routes_statistics(self) -> List[Dict[str, Any]]:
        """Get statistics for all routes that have contributed poems."""
        route_ids = set()
        for node_id, node_data in self.graph.nodes(data=True):
            if node_data.get("type") == "poem":
                route_id = node_data.get("route_id")
                if route_id:
                    route_ids.add(route_id)
        
        return [self.get_route_statistics(route_id) for route_id in sorted(route_ids)]
