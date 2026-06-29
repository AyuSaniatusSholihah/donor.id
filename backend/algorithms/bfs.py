"""
Implementasi BFS (Breadth-First Search) untuk sistem DonorinSolo.

BFS standar:
  - FIFO Queue
  - Level-order traversal (tanpa heuristik)
  - Berhenti di node PERTAMA yang memenuhi:
      1. Stok golongan darah yang diminta >= qty
      2. Sedang buka pada current_time

BFS mengunjungi lebih BANYAK node dibanding A* karena tidak memiliki panduan
heuristik — perbedaan ini terlihat jelas pada animasi Leaflet.
"""

from collections import deque
from typing import Any, Dict, List, Optional, Tuple

from models.graph import GrafDonorDarah
from algorithms.heuristic import path_distance


# Alias tipe untuk konsistensi dengan A*
HeuristicDetails = Dict[str, Dict[str, Any]]


def bfs_search(
    graph: GrafDonorDarah,
    start_id: str,
    blood_type: str,
    qty: int,
    current_time: str,
) -> Tuple[Optional[List[str]], List[str], float, Optional[str], HeuristicDetails]:
    """
    BFS Search — FIFO Queue murni.

    Returns:
        path             : daftar node_id dari start ke target (None jika tidak ditemukan)
        visited_list     : urutan node_id yang dikunjungi (level-order)
        total_distance   : total jarak aktual sepanjang path (km)
        target_id        : node_id tujuan (None jika tidak ditemukan)
        heuristic_details: dict {node_id: {node, g, h=null, f}} untuk animasi Leaflet
                           BFS tidak menggunakan heuristik, jadi h=null dan f=g.
    """
    if start_id not in graph.nodes:
        return None, [], 0.0, None, {}

    bt = blood_type.upper()

    # FIFO queue: setiap entry adalah path lengkap dari start ke node saat ini
    queue: deque[List[str]] = deque([[start_id]])
    visited_set = {start_id}
    visited_list: List[str] = []

    # Jarak aktual dari start ke setiap node (diupdate saat enqueue)
    dist_from_start: Dict[str, float] = {start_id: 0.0}

    # Detail g/h/f untuk visualisasi Leaflet (h=None karena BFS tidak pakai heuristik)
    heuristic_details: HeuristicDetails = {}

    while queue:
        path = queue.popleft()
        curr_id = path[-1]

        visited_list.append(curr_id)
        curr_node = graph.get_node(curr_id)
        g = dist_from_start[curr_id]

        # Catat detail node untuk Leaflet (h=None karena tidak ada heuristik di BFS)
        heuristic_details[curr_id] = {
            "node": curr_node.name,
            "g": round(g, 4),
            "h": None,       # BFS tidak menggunakan heuristik
            "f": round(g, 4),  # f = g (tanpa h)
        }

        # ✅ Cek goal: stok cukup DAN sedang buka (kriteria sama dengan A*), tapi bukan titik asal
        if (
            curr_id != start_id
            and curr_node.stock.get(bt, 0) >= qty
            and curr_node.operational_hours.is_open(current_time)
        ):
            total_dist = path_distance(graph, path)
            return path, visited_list, total_dist, curr_id, heuristic_details

        # Ekspansi tetangga — murni FIFO, tanpa prioritas apapun
        for neighbor_id, edge_dist in graph.get_neighbors(curr_id):
            if neighbor_id not in visited_set:
                visited_set.add(neighbor_id)
                dist_from_start[neighbor_id] = g + edge_dist
                queue.append(path + [neighbor_id])

    # Tidak ditemukan node yang memenuhi syarat
    return None, visited_list, 0.0, None, heuristic_details