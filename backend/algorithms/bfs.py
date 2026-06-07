from collections import deque
from typing import Dict, List, Optional, Tuple, Set
from models.graph import GrafDonorDarah

def bfs_search(
    graph: GrafDonorDarah,
    start_id: str,
    blood_type: str,
    qty: int,
    current_time: str
) -> Tuple[Optional[List[str]], List[str], float, Optional[str]]:
    """
    Breadth-First Search to find the nearest blood donor node matching stock and time criteria.
    Returns: (path, visited, total_distance, target_id)
    """
    if start_id not in graph.nodes:
        return None, [], 0.0, None

    visited_list = []
    visited_set = {start_id}
    queue = deque([[start_id]])
    
    # Trace path distance
    # We will map child_id -> parent_id to reconstruct path and also store distance
    parent_map: Dict[str, Tuple[Optional[str], float]] = {start_id: (None, 0.0)}

    target_id = None
    final_path = None

    while queue:
        path = queue.popleft()
        current_node_id = path[-1]
        
        visited_list.append(current_node_id)
        current_node = graph.get_node(current_node_id)

        # Check if current node satisfies search criteria
        if current_node.has_stock(blood_type, qty) and current_node.operational_hours.is_open(current_time):
            target_id = current_node_id
            final_path = path
            break

        for neighbor_id, dist in graph.get_neighbors(current_node_id):
            if neighbor_id not in visited_set:
                visited_set.add(neighbor_id)
                parent_map[neighbor_id] = (current_node_id, dist)
                new_path = list(path)
                new_path.append(neighbor_id)
                queue.append(new_path)

    if not final_path:
        return None, visited_list, 0.0, None

    # Calculate total path distance
    total_dist = 0.0
    for i in range(len(final_path) - 1):
        u = final_path[i]
        v = final_path[i+1]
        # find weight from u to v
        for neighbor, weight in graph.get_neighbors(u):
            if neighbor == v:
                total_dist += weight
                break

    return final_path, visited_list, total_dist, target_id
