import os
import json
from models.nodes import RS, UTD_PMI, DonorSukarela, BaseNode
from models.graph import GrafDonorDarah

def load_graph_from_json(json_path: str) -> GrafDonorDarah:
    graph = GrafDonorDarah()
    
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"JSON file not found at: {json_path}")
        
    with open(json_path, 'r') as file:
        data = json.load(file)
        
    # First pass: load nodes
    for item in data:
        node_type = item.get("type")
        node_data = {
            "id": item["id"],
            "name": item["name"],
            "lat": item["lat"],
            "lon": item["lon"],
            "stock": item["stock"],
            "operational_hours": item["operational_hours"]
        }
        
        if node_type == "RS":
            node = RS(**node_data)
        elif node_type == "UTD_PMI":
            node = UTD_PMI(**node_data)
        elif node_type == "DonorSukarela":
            node = DonorSukarela(**node_data)
        else:
            node = BaseNode(**node_data)
            
        graph.add_node(node)
        
    # Second pass: establish connections
    for item in data:
        from_id = item["id"]
        connections = item.get("connections", [])
        for conn in connections:
            to_id = conn["to"]
            distance = conn["distance"]
            graph.add_edge(from_id, to_id, distance)
            
    return graph
