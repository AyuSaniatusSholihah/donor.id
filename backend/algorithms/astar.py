import heapq
from typing import Dict, List, Optional, Tuple, Set
from models.graph import GrafDonorDarah
from .heuristic import haversine_distance

def astar_search(
    graph: GrafDonorDarah,
    start_id: str,
    blood_type: str,
    qty: int,
    current_time: str
) -> Tuple[Optional[List[str]], List[str], float, Optional[str]]:
    """
    A* Search algorithm using Haversine distance heuristic.
    Finds the shortest path to the nearest node matching stock and operational time criteria.
    Returns: (path, visited, total_distance, target_id)
    """
    if start_id not in graph.nodes:
        return None, [], 0.0, None

    # Step 1: Identify all valid target nodes
    targets = []
    for node_id, node in graph.nodes.items():
        if node.has_stock(blood_type, qty) and node.operational_hours.is_open(current_time):
            targets.append(node)

    if not targets:
        return None, [], 0.0, None

    # If start node itself is a target
    start_node = graph.get_node(start_id)
    if start_node in targets:
        return [start_id], [start_id], 0.0, start_id

    # Step 2: Define Heuristic h(n) as min distance to any target
    def get_heuristic(node_id: str) -> float:
        node = graph.get_node(node_id)
        if not node:
            return float('inf')
        return min(haversine_distance(node.lat, node.lon, t.lat, t.lon) for t in targets)

    # Priority queue stores tuples of: (f_score, g_score, current_id, path)
    # Using python's heapq
    pq = []
    # g_score maps node_id -> shortest distance from start to node_id found so far
    g_score = {start_id: 0.0}
    h_start = get_heuristic(start_id)
    heapq.heappush(pq, (h_start, 0.0, start_id, [start_id]))

    visited_list = []
    closed_set = set()

    while pq:
        f, g, curr_id, path = heapq.heappop(pq)

        if curr_id in closed_set:
            continue
        
        closed_set.add(curr_id)
        visited_list.append(curr_id)

        curr_node = graph.get_node(curr_id)
        # Check if reached target
        if curr_node in targets:
            return path, visited_list, g, curr_id

        for neighbor_id, dist in graph.get_neighbors(curr_id):
            if neighbor_id in closed_set:
                continue
            
            tentative_g = g + dist
            if neighbor_id not in g_score or tentative_g < g_score[neighbor_id]:
                g_score[neighbor_id] = tentative_g
                f_score = tentative_g + get_heuristic(neighbor_id)
                new_path = list(path)
                new_path.append(neighbor_id)
                heapq.heappush(pq, (f_score, tentative_g, neighbor_id, new_path))

    return None, visited_list, 0.0, None
