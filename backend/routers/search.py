"""
Router FastAPI untuk pencarian donor darah menggunakan A* dan BFS.
"""

import os
import time
from typing import Any, Dict, List, Optional

# pyrefly: ignore [missing-import]
from fastapi import APIRouter, HTTPException, Query
# pyrefly: ignore [missing-import]
from pydantic import BaseModel

# pyrefly: ignore [missing-import]
from models.graph import GrafDonorDarah
# pyrefly: ignore [missing-import]
from data.loader import load_graph_from_json
# pyrefly: ignore [missing-import]
from algorithms.bfs import bfs_search
# pyrefly: ignore [missing-import]
from algorithms.astar import astar_search

router = APIRouter()

# Path ke data JSON relatif terhadap folder backend
JSON_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "nodes.json")

# Muat graph sekali saat modul diimpor (k-NN k=3, Haversine)
graph: GrafDonorDarah = load_graph_from_json(JSON_PATH, k=3)


# ---------------------------------------------------------------------------
# Response Models
# ---------------------------------------------------------------------------

class OperationalHoursDetail(BaseModel):
    is_24h: bool
    open: str
    close: str


class NodeDetail(BaseModel):
    id: str
    name: str
    type: str
    lat: float
    lon: float
    stock: Dict[str, int]
    operational_hours: Dict[str, Any]


class SearchResult(BaseModel):
    algorithm: str
    path: Optional[List[NodeDetail]]
    visited_nodes: List[NodeDetail]
    visited_count: int                          # jumlah node yang dikunjungi
    distance: float                             # km, total jarak sepanjang path
    execution_time_ms: float                    # waktu eksekusi dalam milidetik
    recommended_node: Optional[NodeDetail]      # node tujuan yang direkomendasikan
    heuristic_details: Dict[str, Any]           # {node_id: {node, g, h, f}}
    success: bool
    message: str


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _node_to_detail(node_id: str) -> NodeDetail:
    n = graph.get_node(node_id)
    return NodeDetail(
        id=n.id,
        name=n.name,
        type=n.type,
        lat=n.lat,
        lon=n.lon,
        stock=n.stock,
        operational_hours=n.operational_hours.model_dump(),
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/nodes")
def get_all_nodes():
    """
    Mengembalikan semua node beserta edge-nya untuk rendering peta Leaflet.
    """
    nodes_list = [node.model_dump() for node in graph.nodes.values()]

    edges = []
    seen: set = set()
    for from_id, neighbors in graph.adjacency.items():
        for to_id, dist in neighbors:
            edge_key = tuple(sorted([from_id, to_id]))
            if edge_key not in seen:
                seen.add(edge_key)
                edges.append({"from": from_id, "to": to_id, "distance": round(dist, 4)})

    return {"nodes": nodes_list, "edges": edges}


@router.get("/search", response_model=SearchResult)
def search_blood(
    start_id: str = Query(..., description="ID node awal (contoh: node_1)"),
    blood_type: str = Query(..., description="Golongan darah yang dibutuhkan: A, B, AB, O"),
    qty: int = Query(1, ge=1, description="Jumlah kantong darah yang dibutuhkan"),
    current_time: str = Query("12:00", description="Waktu saat ini format HH:MM"),
    algorithm: str = Query("astar", description="Algoritma pencarian: 'astar' atau 'bfs'"),
):
    """
    Mencari fasilitas donor darah yang memenuhi syarat stok dan jam buka.

    ---
    **Perbedaan A* vs BFS pada visualisasi Leaflet:**

    | Aspek | BFS | A* |
    |---|---|---|
    | Urutan eksplorasi | Level-order / FIFO | Dipandu heuristik |
    | `visited_count` | Lebih banyak | Lebih sedikit |
    | `heuristic_details.h` | `null` (tidak ada heuristik) | Nilai h(n) nyata |
    | Kualitas path | Node pertama yang cocok | Node terbaik (stok+jarak+jam) |

    ---
    **Format `heuristic_details`:**
    ```json
    {
      "node_1": {"node": "PMI Kota Surakarta", "g": 0.0, "h": 0.72, "f": 0.72},
      "node_9": {"node": "RS Hermina Solo",    "g": 2.31, "h": 1.44, "f": 3.75}
    }
    ```
    Gunakan urutan `visited_nodes` untuk menganimasikan eksplorasi langkah demi langkah.
    """
    blood_type = blood_type.strip().upper()
    algorithm  = algorithm.strip().lower()

    # --- Validasi input ---
    if start_id not in graph.nodes:
        raise HTTPException(status_code=400, detail=f"Node '{start_id}' tidak ditemukan.")
    if blood_type not in ("A", "B", "AB", "O"):
        raise HTTPException(status_code=400, detail="Golongan darah harus A, B, AB, atau O.")
    if algorithm not in ("astar", "bfs"):
        raise HTTPException(status_code=400, detail="Algoritma harus 'astar' atau 'bfs'.")

    # --- Jalankan algoritma & ukur waktu eksekusi ---
    t_start = time.perf_counter()

    if algorithm == "astar":
        path_ids, visited_ids, total_distance, target_id, h_details = astar_search(
            graph, start_id, blood_type, qty, current_time
        )
    else:  # bfs
        path_ids, visited_ids, total_distance, target_id, h_details = bfs_search(
            graph, start_id, blood_type, qty, current_time
        )

    execution_time_ms = (time.perf_counter() - t_start) * 1000

    # --- Bangun response ---
    visited_nodes_detail = [_node_to_detail(nid) for nid in visited_ids]
    path_detail          = [_node_to_detail(nid) for nid in path_ids] if path_ids else None
    recommended          = _node_to_detail(target_id) if target_id else None

    if not target_id:
        return SearchResult(
            algorithm=algorithm,
            path=None,
            visited_nodes=visited_nodes_detail,
            visited_count=len(visited_ids),
            distance=0.0,
            execution_time_ms=round(execution_time_ms, 4),
            recommended_node=None,
            heuristic_details=h_details,
            success=False,
            message=(
                f"Tidak ditemukan fasilitas dengan stok darah {blood_type} ≥ {qty} "
                f"yang sedang buka pada pukul {current_time}."
            ),
        )

    target_name = graph.get_node(target_id).name
    return SearchResult(
        algorithm=algorithm,
        path=path_detail,
        visited_nodes=visited_nodes_detail,
        visited_count=len(visited_ids),
        distance=round(total_distance, 4),
        execution_time_ms=round(execution_time_ms, 4),
        recommended_node=recommended,
        heuristic_details=h_details,
        success=True,
        message=(
            f"[{algorithm.upper()}] Ditemukan: {target_name} | "
            f"Jarak: {round(total_distance, 2)} km | "
            f"Node dikunjungi: {len(visited_ids)} | "
            f"Waktu: {round(execution_time_ms, 3)} ms"
        ),
    )
