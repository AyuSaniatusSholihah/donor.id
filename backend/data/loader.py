import os
import json
from models.nodes import BDRS, UTD_PMI, DonorSukarela, BaseNode
from models.graph import GrafDonorDarah
from algorithms.heuristic import haversine_distance


def load_graph_from_json(json_path: str, k: int = 3) -> GrafDonorDarah:
    """
    Memuat node dari file JSON dan membangun graph berdasarkan
    k-Nearest Neighbors (k=3) menggunakan jarak Haversine.

    Setiap node dihubungkan ke k tetangga terdekat secara geografis
    (bidirectional edge). Pendekatan ini menghasilkan graph yang lebih
    realistis dan membuat perbedaan BFS vs A* terlihat jelas pada
    visualisasi (BFS menelusuri lebih banyak node karena tidak memiliki
    panduan heuristic).
    """
    graph = GrafDonorDarah()

    if not os.path.exists(json_path):
        raise FileNotFoundError(f"JSON file not found at: {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # --- Pass 1: Muat semua node ---
    for item in data:
        node_type = item.get("type")
        node_data = {
            "id": item["id"],
            "name": item["name"],
            "lat": item["lat"],
            "lon": item["lon"],
            "stock": item["stock"],
            "operational_hours": item["operational_hours"],
        }

        if node_type == "BDRS":
            node = BDRS(**node_data)
        elif node_type == "UTD_PMI":
            node = UTD_PMI(**node_data)
        elif node_type == "DonorSukarela":
            node = DonorSukarela(**node_data)
        else:
            node = BaseNode(type=node_type, **node_data)

        graph.add_node(node)

    # --- Pass 2: Bangun edge k-Nearest Neighbors (k=3) ---
    _build_knn_graph(graph, k=k)

    return graph


def _build_knn_graph(graph: GrafDonorDarah, k: int = 3) -> None:
    """
    Membangun koneksi k-nearest neighbors pada graph yang sudah terisi node.

    Algoritma:
      Untuk setiap node n:
        1. Hitung jarak Haversine ke semua node lain
        2. Urutkan dari terdekat
        3. Hubungkan n ke k node terdekat (bidirectional)

    Duplikasi edge dicegah oleh GrafDonorDarah.add_edge().
    """
    node_ids = list(graph.nodes.keys())

    for node_id in node_ids:
        node = graph.get_node(node_id)

        # Hitung jarak ke semua node lain
        distances = []
        for other_id in node_ids:
            if other_id == node_id:
                continue
            other = graph.get_node(other_id)
            dist = haversine_distance(node.lat, node.lon, other.lat, other.lon)
            distances.append((other_id, dist))

        # Urutkan berdasarkan jarak terkecil, ambil k terdekat
        distances.sort(key=lambda x: x[1])
        for neighbor_id, dist in distances[:k]:
            graph.add_edge(node_id, neighbor_id, dist)
