"""
Modul heuristik untuk algoritma A* pada sistem DonorinSolo.

Spesifikasi heuristik:

    h(n) = 0.6 × Haversine(n → target terdekat yang valid)
           + 0.3 × (1 − skor_stok)
           + 0.1 × (1 − skor_jam)

Keterangan komponen:
  - Haversine(n → target terdekat) : jarak garis lurus (km) ke node tujuan terdekat
                                     yang memiliki stok cukup DAN sedang buka.
  - skor_stok   = stok_node / max(stok seluruh node) ∈ [0, 1]
  - skor_jam    = 1.0  jika buka 24 jam
                  0.5  jika jam operasional terbatas
"""

import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.nodes import BaseNode
    from models.graph import GrafDonorDarah


# ---------------------------------------------------------------------------
# Haversine
# ---------------------------------------------------------------------------

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Menghitung jarak lingkaran besar antara dua titik koordinat (dalam km)
    menggunakan rumus Haversine.
    """
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(max(0.0, a)))  # clamp untuk menghindari domain error
    return 6371.0 * c


# ---------------------------------------------------------------------------
# Skor komponen heuristik
# ---------------------------------------------------------------------------

def get_operational_score(node: "BaseNode") -> float:
    """
    Skor jam operasional:
      1.0  → buka 24 jam
      0.5  → jam terbatas
    """
    return 1.0 if node.operational_hours.is_24h else 0.5


def get_nearest_valid_distance(
    node: "BaseNode",
    graph: "GrafDonorDarah",
    blood_type: str,
    qty: int,
    current_time: str,
) -> float:
    """
    Menghitung jarak Haversine (km) dari node saat ini ke node tujuan terdekat
    yang memenuhi syarat: stok >= qty DAN sedang buka.

    Jika tidak ada node valid sama sekali, kembalikan nilai sangat besar (100 km)
    agar heuristik tetap deterministik.
    """
    bt = blood_type.upper()
    min_dist = float("inf")

    for candidate in graph.nodes.values():
        if (
            candidate.stock.get(bt, 0) >= qty
            and candidate.operational_hours.is_open(current_time)
        ):
            d = haversine_distance(node.lat, node.lon, candidate.lat, candidate.lon)
            if d < min_dist:
                min_dist = d

    return min_dist if min_dist != float("inf") else 100.0


# ---------------------------------------------------------------------------
# Fungsi heuristik utama
# ---------------------------------------------------------------------------

def compute_heuristic(
    node: "BaseNode",
    graph: "GrafDonorDarah",
    blood_type: str,
    qty: int,
    current_time: str,
    max_stock: int,
) -> float:
    """
    Multi-criteria heuristic h(n) untuk A*:

        h(n) = 0.6 × Haversine(n → target terdekat)
               + 0.3 × (1 − skor_stok)
               + 0.1 × (1 − skor_jam)

    Nilai h(n) yang lebih kecil → node lebih diprioritaskan oleh A*.
    """
    bt = blood_type.upper()

    # --- 60%: Jarak ke target valid terdekat (km) ---
    dist_to_target = get_nearest_valid_distance(node, graph, bt, qty, current_time)

    # --- 30%: Skor stok ---
    node_stock = node.stock.get(bt, 0)
    stock_score = node_stock / max_stock if max_stock > 0 else 0.0

    # --- 10%: Skor jam operasional ---
    operational_score = get_operational_score(node)

    return (
        0.6 * dist_to_target
        + 0.3 * (1.0 - stock_score)
        + 0.1 * (1.0 - operational_score)
    )


# ---------------------------------------------------------------------------
# Helper: total jarak sepanjang path
# ---------------------------------------------------------------------------

def path_distance(graph: "GrafDonorDarah", path: list) -> float:
    """Hitung total jarak (km) sepanjang daftar node_id berdasarkan adjacency list."""
    total = 0.0
    for i in range(len(path) - 1):
        u, v = path[i], path[i + 1]
        for neighbor_id, dist in graph.get_neighbors(u):
            if neighbor_id == v:
                total += dist
                break
    return total
