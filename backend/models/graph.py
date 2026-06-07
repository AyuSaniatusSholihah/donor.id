from typing import Dict, List, Tuple
from .nodes import BaseNode, RS, UTD_PMI, DonorSukarela

class GrafDonorDarah:
    def __init__(self):
        self.nodes: Dict[str, BaseNode] = {}
        # adjacency list: node_id -> list of tuple (neighbor_node_id, distance)
        self.adjacency: Dict[str, List[Tuple[str, float]]] = {}

    def add_node(self, node: BaseNode):
        self.nodes[node.id] = node
        if node.id not in self.adjacency:
            self.adjacency[node.id] = []

    def add_edge(self, from_id: str, to_id: str, distance: float):
        if from_id in self.nodes and to_id in self.nodes:
            # Add bidirectional edge (undirected graph representation)
            if not any(neighbor == to_id for neighbor, _ in self.adjacency[from_id]):
                self.adjacency[from_id].append((to_id, distance))
            if not any(neighbor == from_id for neighbor, _ in self.adjacency[to_id]):
                self.adjacency[to_id].append((from_id, distance))

    def get_node(self, node_id: str) -> BaseNode:
        return self.nodes[node_id]

    def get_neighbors(self, node_id: str) -> List[Tuple[str, float]]:
        return self.adjacency.get(node_id, [])
