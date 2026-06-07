import os
# pyrefly: ignore [missing-import]
from fastapi import APIRouter, HTTPException, Query
# pyrefly: ignore [missing-import]
from pydantic import BaseModel
# pyrefly: ignore [missing-import]
from typing import List, Optional, Dict

# pyrefly: ignore [missing-import]
from models.graph import GrafDonorDarah
# pyrefly: ignore [missing-import]
from data.loader import load_graph_from_json
# pyrefly: ignore [missing-import]
from algorithms.bfs import bfs_search
from algorithms.astar import astar_search

router = APIRouter()

# Path to the JSON data relative to backend folder
JSON_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "nodes.json")

# Load graph once on module load (or reload)
graph: GrafDonorDarah = load_graph_from_json(JSON_PATH)

class SearchResponse(BaseModel):
    success: bool
    message: str
    path: Optional[List[dict]] = None
    visited: List[dict]
    total_distance: float
    target_id: Optional[str] = None
    algorithm_used: str

@router.get("/nodes")
def get_all_nodes():
    """
    Get all nodes and their connections for map rendering.
    """
    # Build list of nodes
    nodes_list = []
    for node_id, node in graph.nodes.items():
        nodes_list.append(node.model_dump())
        
    # Build list of links (unique edges)
    edges = []
    seen = set()
    for from_id, neighbors in graph.adjacency.items():
        for to_id, dist in neighbors:
            edge_key = tuple(sorted([from_id, to_id]))
            if edge_key not in seen:
                seen.add(edge_key)
                edges.append({
                    "from": from_id,
                    "to": to_id,
                    "distance": dist
                })
                
    return {
        "nodes": nodes_list,
        "edges": edges
    }

@router.get("/search", response_model=SearchResponse)
def search_blood(
    start_id: str = Query(..., description="ID of the starting node"),
    blood_type: str = Query(..., description="Blood type required (A, B, AB, O)"),
    qty: int = Query(1, description="Required blood quantity"),
    current_time: str = Query("12:00", description="Current time in HH:MM format"),
    algorithm: str = Query("astar", description="Pathfinding algorithm: 'astar' or 'bfs'")
):
    # Normalize input
    blood_type = blood_type.upper()
    algorithm = algorithm.lower()

    if start_id not in graph.nodes:
        raise HTTPException(status_code=400, detail="Start node not found")
    
    if blood_type not in ["A", "B", "AB", "O"]:
        raise HTTPException(status_code=400, detail="Invalid blood type. Must be A, B, AB, or O")

    if algorithm == "astar":
        path_ids, visited_ids, total_distance, target_id = astar_search(
            graph, start_id, blood_type, qty, current_time
        )
    elif algorithm == "bfs":
        path_ids, visited_ids, total_distance, target_id = bfs_search(
            graph, start_id, blood_type, qty, current_time
        )
    else:
        raise HTTPException(status_code=400, detail="Invalid algorithm. Choose 'astar' or 'bfs'")

    # Convert node IDs to full Node dicts for response
    path_nodes = None
    if path_ids:
        path_nodes = [graph.get_node(nid).model_dump() for nid in path_ids]
        
    visited_nodes = [graph.get_node(nid).model_dump() for nid in visited_ids]

    if not path_ids:
        return SearchResponse(
            success=False,
            message="No suitable blood donor location found matching the criteria.",
            path=None,
            visited=visited_nodes,
            total_distance=0.0,
            target_id=None,
            algorithm_used=algorithm
        )

    target_name = graph.get_node(target_id).name
    return SearchResponse(
        success=True,
        message=f"Path found to {target_name} using {algorithm.upper()}.",
        path=path_nodes,
        visited=visited_nodes,
        total_distance=round(total_distance, 2),
        target_id=target_id,
        algorithm_used=algorithm
    )
