import os
import json
import logging
from models.nodes import BDRS, UTD_PMI, DonorSukarela, BaseNode
from models.graph import GrafDonorDarah
from algorithms.heuristic import haversine_distance
from data.osrm_router import build_distance_matrix, get_road_distance

logger = logging.getLogger(__name__)


def load_graph_from_json(json_path: str, k: int = 3) -> GrafDonorDarah:
    """
    Memuat node dari file JSON dan membangun graph berdasarkan
    k-Nearest Neighbors (k=3).

    Bobot edge menggunakan jarak jalan nyata dari OSRM (OpenStreetMap Routing Machine).
    OSRM dipanggil sekali dalam mode batch (Table API) saat startup,
    kemudian di-cache. Fallback ke Haversine jika OSRM tidak tersedia.

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

    # --- Pass 2: Bangun distance matrix (1 batch request ke OSRM) ---
    node_list = [
        {"id": nid, "lat": n.lat, "lon": n.lon}
        for nid, n in graph.nodes.items()
    ]
    distance_matrix = build_distance_matrix(node_list)

    # --- Pass 3: Bangun edge k-Nearest Neighbors (k=3) ---
    _build_knn_graph(graph, k=k, distance_matrix=distance_matrix)

    return graph


def _build_knn_graph(
    graph: GrafDonorDarah,
    k: int = 3,
    distance_matrix: dict | None = None,
) -> None:
    """
    Membangun koneksi k-nearest neighbors pada graph yang sudah terisi node.

    Algoritma:
      Untuk setiap node n:
        1. Hitung jarak Haversine (garis lurus) ke semua node lain untuk menentukan k tetangga terdekat
        2. Urutkan dari terdekat
        3. Hubungkan n ke k node terdekat dengan bobot = jarak jalan nyata dari OSRM
           (dari distance_matrix jika tersedia, fallback ke get_road_distance per-pair)

    Duplikasi edge dicegah oleh GrafDonorDarah.add_edge().
    """
    if distance_matrix is None:
        distance_matrix = {}

    node_ids = list(graph.nodes.keys())
    total_nodes = len(node_ids)

    logger.info(
        "[OSRM] Membangun k-NN graph (k=%d) untuk %d node...",
        k, total_nodes
    )

    for node_id in node_ids:
        node = graph.get_node(node_id)

        # --- Langkah 1: Gunakan Haversine untuk menentukan kandidat k tetangga ---
        haversine_distances = []
        for other_id in node_ids:
            if other_id == node_id:
                continue
            other = graph.get_node(other_id)
            h_dist = haversine_distance(node.lat, node.lon, other.lat, other.lon)
            haversine_distances.append((other_id, h_dist))

        haversine_distances.sort(key=lambda x: x[1])
        candidates = haversine_distances[:k]

        # --- Langkah 2: Ambil jarak jalan nyata untuk k kandidat ---
        for neighbor_id, h_dist in candidates:
            neighbor = graph.get_node(neighbor_id)

            # Prioritas: distance_matrix (batch OSRM) → get_road_distance (single OSRM) → Haversine
            if (node_id, neighbor_id) in distance_matrix:
                road_dist = distance_matrix[(node_id, neighbor_id)]
            else:
                road_dist = get_road_distance(
                    node.lat, node.lon,
                    neighbor.lat, neighbor.lon
                )

            graph.add_edge(node_id, neighbor_id, road_dist)

    logger.info("[OSRM] Graph selesai. %d node, edge menggunakan jarak jalan nyata.", total_nodes)
