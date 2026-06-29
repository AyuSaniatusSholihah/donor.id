"""
Implementasi algoritma A* untuk sistem DonorinSolo.

f(n) = g(n) + h(n)

  g(n) : biaya nyata dari start ke node n
         (akumulasi jarak Haversine edge yang telah dilalui, dalam km)+
  h(n) : estimasi multi-criteria dari node n ke goal
         0.6 × Haversine(n → target terdekat yang valid)
         + 0.3 × (1 − skor_stok)
         + 0.1 × (1 − skor_jam)

Kriteria goal node:
  1. Stok golongan darah yang diminta >= qty
  2. Sedang buka pada current_time

A* mengunjungi jauh LEBIH SEDIKIT node dibanding BFS karena dipandu heuristik —
perbedaan ini terlihat jelas pada animasi Leaflet.
"""

import heapq
from typing import Any, Dict, List, Optional, Tuple

from models.graph import GrafDonorDarah
from algorithms.heuristic import compute_heuristic, path_distance


# Alias tipe untuk detail g/h/f per node
HeuristicDetails = Dict[str, Dict[str, Any]]


def astar_search(
    graph: GrafDonorDarah,
    start_id: str,
    blood_type: str,
    qty: int,
    current_time: str,
) -> Tuple[Optional[List[str]], List[str], float, Optional[str], HeuristicDetails]:
    """
    A* Search.

    Returns:
        path             : daftar node_id dari start ke target (None jika tidak ditemukan)
        visited_list     : urutan node_id yang di-expand (di-pop dari priority queue)
        total_distance   : total jarak aktual sepanjang path (km)
        target_id        : node_id tujuan (None jika tidak ditemukan)
        heuristic_details: dict {node_id: {node, g, h, f}} untuk animasi Leaflet
    """
    if start_id not in graph.nodes:
        return None, [], 0.0, None, {}

    bt = blood_type.upper()

    # Pre-compute max_stock untuk normalisasi skor_stok
    max_stock = max(
        (node.stock.get(bt, 0) for node in graph.nodes.values()), default=1
    )
    if max_stock == 0:
        max_stock = 1

    # g_score: jarak aktual terbaik yang diketahui dari start ke tiap node
    g_score: Dict[str, float] = {start_id: 0.0}

    # Detail g/h/f untuk setiap node yang di-expand (untuk Leaflet)
    heuristic_details: HeuristicDetails = {}

    start_node = graph.get_node(start_id)
    h_start = compute_heuristic(start_node, graph, bt, qty, current_time, max_stock)

    # Priority Queue: (f_score, counter, g_score, node_id, path)
    # counter sebagai tie-breaker agar heapq tidak membandingkan List secara langsung
    counter = 0
    pq: List[Tuple[float, int, float, str, List[str]]] = []
    heapq.heappush(pq, (h_start, counter, 0.0, start_id, [start_id]))

    visited_list: List[str] = []
    closed_set: set = set()

    while pq:
        f, _, g, curr_id, path = heapq.heappop(pq)

        # Lewati node yang sudah di-expand sebelumnya
        if curr_id in closed_set:
            continue

        closed_set.add(curr_id)
        visited_list.append(curr_id)

        curr_node = graph.get_node(curr_id)

        # Hitung h aktual saat di-expand (untuk pencatatan yang akurat)
        h_curr = compute_heuristic(curr_node, graph, bt, qty, current_time, max_stock)

        # Catat detail g/h/f node ini untuk visualisasi Leaflet
        heuristic_details[curr_id] = {
            "node": curr_node.name,
            "g": round(g, 4),
            "h": round(h_curr, 4),
            "f": round(g + h_curr, 4),
        }

        # ✅ Cek goal: stok cukup DAN sedang buka, tapi bukan titik asal
        if (
            curr_id != start_id
            and curr_node.stock.get(bt, 0) >= qty
            and curr_node.operational_hours.is_open(current_time)
        ):
            total_dist = path_distance(graph, path)
            return path, visited_list, total_dist, curr_id, heuristic_details

        # Ekspansi tetangga
        for neighbor_id, edge_dist in graph.get_neighbors(curr_id):
            if neighbor_id in closed_set:
                continue

            tentative_g = g + edge_dist

            if neighbor_id not in g_score or tentative_g < g_score[neighbor_id]:
                g_score[neighbor_id] = tentative_g
                neighbor_node = graph.get_node(neighbor_id)
                h = compute_heuristic(
                    neighbor_node, graph, bt, qty, current_time, max_stock
                )
                f_new = tentative_g + h
                counter += 1
                heapq.heappush(
                    pq,
                    (f_new, counter, tentative_g, neighbor_id, path + [neighbor_id]),
                )

    # Tidak ditemukan node yang memenuhi syarat
    return None, visited_list, 0.0, None, heuristic_details