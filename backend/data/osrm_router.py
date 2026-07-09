"""
Modul integrasi OSRM (OpenStreetMap Routing Machine) untuk DonorinSolo.

Menggunakan OSRM Demo Server (gratis, tanpa API key, data OpenStreetMap):
  Base URL: http://router.project-osrm.org

Strategi:
  1. Saat startup: gunakan OSRM /table API (BATCH) → 1 request untuk semua pasang node
  2. Saat ambil geometry path: gunakan OSRM /route API per segmen (di-cache)
  3. Fallback ke Haversine jika OSRM gagal/timeout

Fungsi utama:
  - build_distance_matrix(nodes) -> Dict[Tuple[str,str], float]  [km]
  - get_road_distance(lat1, lon1, lat2, lon2) -> float  [km]
  - get_road_geometry(lat1, lon1, lat2, lon2) -> List[[lat, lon]]
  - get_path_geometry(waypoints) -> List[[lat, lon]]
"""

import math
import time
import logging
from functools import lru_cache
from typing import Dict, List, Tuple, Optional, Any

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Konfigurasi
# ---------------------------------------------------------------------------

OSRM_BASE_URL   = "http://router.project-osrm.org"
OSRM_TIMEOUT    = 15    # detik per request
OSRM_RETRIES    = 2     # jumlah retry jika gagal
OSRM_RETRY_WAIT = 1.0   # detik antar retry
EARTH_RADIUS_KM = 6371.0

# Cache in-memory untuk jarak jalan: (lat1,lon1,lat2,lon2) -> km
_distance_cache: Dict[Tuple[float, float, float, float], float] = {}


# ---------------------------------------------------------------------------
# Haversine (fallback)
# ---------------------------------------------------------------------------

def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Jarak garis lurus (km) antara dua koordinat menggunakan rumus Haversine."""
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(max(0.0, a)))
    return EARTH_RADIUS_KM * c


# ---------------------------------------------------------------------------
# OSRM HTTP helpers
# ---------------------------------------------------------------------------

def _get_with_retry(url: str) -> Optional[dict]:
    """
    GET ke OSRM dengan retry sederhana.
    Returns dict JSON jika berhasil, None jika gagal.
    """
    if not REQUESTS_AVAILABLE:
        return None

    for attempt in range(OSRM_RETRIES):
        try:
            resp = requests.get(url, timeout=OSRM_TIMEOUT)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == "Ok":
                    return data
        except Exception as exc:  # noqa: BLE001
            logger.debug("OSRM attempt %d gagal: %s", attempt + 1, exc)
            if attempt < OSRM_RETRIES - 1:
                time.sleep(OSRM_RETRY_WAIT)

    return None


# ---------------------------------------------------------------------------
# OSRM Table API — batch distance matrix
# ---------------------------------------------------------------------------

def build_distance_matrix(
    nodes: List[Dict[str, Any]]
) -> Dict[Tuple[str, str], float]:
    """
    Membangun distance matrix jarak jalan nyata untuk semua pasang node
    menggunakan OSRM /table API (1 batch request).

    Args:
        nodes: List of dict dengan keys 'id', 'lat', 'lon'

    Returns:
        Dict {(id_from, id_to): distance_km}
        Jika OSRM gagal, kembalikan dict kosong (caller akan fallback ke Haversine)
    """
    if not nodes or not REQUESTS_AVAILABLE:
        return {}

    # Format koordinat: lon,lat;lon,lat;...
    coords_str = ";".join(f"{n['lon']},{n['lat']}" for n in nodes)
    url = f"{OSRM_BASE_URL}/table/v1/driving/{coords_str}?annotations=distance"

    logger.info("[OSRM] Membangun distance matrix untuk %d node (1 batch request)...", len(nodes))

    data = _get_with_retry(url)
    if not data:
        logger.warning("[OSRM] Table API gagal. Akan menggunakan Haversine untuk semua edge.")
        return {}

    try:
        distance_matrix = data["distances"]  # matriks NxN dalam meter
        result: Dict[Tuple[str, str], float] = {}

        for i, from_node in enumerate(nodes):
            for j, to_node in enumerate(nodes):
                if i == j:
                    continue
                dist_m = distance_matrix[i][j]
                if dist_m is None or dist_m < 0:
                    # Fallback ke Haversine untuk pasang ini
                    dist_km = _haversine(
                        from_node["lat"], from_node["lon"],
                        to_node["lat"], to_node["lon"]
                    )
                else:
                    dist_km = dist_m / 1000.0
                    # Sanity check
                    h_dist = _haversine(
                        from_node["lat"], from_node["lon"],
                        to_node["lat"], to_node["lon"]
                    )
                    if dist_km <= 0 or dist_km > h_dist * 15:
                        dist_km = h_dist

                result[(from_node["id"], to_node["id"])] = round(dist_km, 6)

                # Simpan ke cache single-pair juga
                key = (
                    round(from_node["lat"], 6), round(from_node["lon"], 6),
                    round(to_node["lat"], 6), round(to_node["lon"], 6)
                )
                _distance_cache[key] = dist_km

        logger.info("[OSRM] Distance matrix berhasil dibangun untuk %d pasang node.", len(result))
        return result

    except (KeyError, IndexError, TypeError) as exc:
        logger.warning("[OSRM] Error parsing table response: %s", exc)
        return {}


# ---------------------------------------------------------------------------
# Single-pair distance (dengan cache)
# ---------------------------------------------------------------------------

def get_road_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Jarak jalan nyata (km) antara dua koordinat.
    Cek cache dulu (diisi oleh build_distance_matrix saat startup).
    Jika tidak ada di cache, panggil OSRM /route API langsung.
    Fallback ke Haversine jika OSRM tidak tersedia.
    """
    key = (round(lat1, 6), round(lon1, 6), round(lat2, 6), round(lon2, 6))

    if key in _distance_cache:
        return _distance_cache[key]

    # Tidak ada di cache → panggil OSRM /route
    url = (
        f"{OSRM_BASE_URL}/route/v1/driving/"
        f"{lon1},{lat1};{lon2},{lat2}"
        f"?overview=false"
    )
    data = _get_with_retry(url)
    if data:
        try:
            dist_m = data["routes"][0]["distance"]
            dist_km = round(dist_m / 1000.0, 6)
            h_dist = _haversine(lat1, lon1, lat2, lon2)
            if dist_km > 0 and dist_km < h_dist * 10:
                _distance_cache[key] = dist_km
                return dist_km
        except (KeyError, IndexError, TypeError):
            pass

    # Fallback
    fallback = _haversine(lat1, lon1, lat2, lon2)
    _distance_cache[key] = fallback
    logger.debug("[OSRM] Fallback Haversine: (%.5f,%.5f) → (%.5f,%.5f)", lat1, lon1, lat2, lon2)
    return fallback


# ---------------------------------------------------------------------------
# Route geometry (untuk visualisasi Leaflet)
# ---------------------------------------------------------------------------

@lru_cache(maxsize=512)
def _cached_osrm_geometry(
    lat1: float, lon1: float, lat2: float, lon2: float
) -> Tuple[Tuple[float, float], ...]:
    """
    Koordinat rute jalan nyata (tuple of (lat, lon)).
    Di-cache oleh lru_cache agar setiap pasang hanya dipanggil sekali.
    Fallback ke garis lurus jika OSRM tidak tersedia.
    """
    url = (
        f"{OSRM_BASE_URL}/route/v1/driving/"
        f"{lon1},{lat1};{lon2},{lat2}"
        f"?overview=full&geometries=geojson&steps=false"
    )
    data = _get_with_retry(url)
    if data:
        try:
            coords = data["routes"][0]["geometry"]["coordinates"]
            # OSRM mengembalikan [lon, lat] → konversi ke (lat, lon)
            result = tuple((c[1], c[0]) for c in coords)
            if len(result) >= 2:
                return result
        except (KeyError, IndexError, TypeError):
            pass

    # Fallback: garis lurus 2 titik
    return ((lat1, lon1), (lat2, lon2))


def get_road_geometry(lat1: float, lon1: float, lat2: float, lon2: float) -> List[List[float]]:
    """
    Koordinat rute jalan nyata sebagai list of [lat, lon].
    Digunakan frontend Leaflet untuk menggambar polyline mengikuti jalan.
    """
    result = _cached_osrm_geometry(
        round(lat1, 6), round(lon1, 6),
        round(lat2, 6), round(lon2, 6),
    )
    return [list(point) for point in result]


def get_path_geometry(waypoints: List[Tuple[float, float]]) -> List[List[float]]:
    """
    Menggabungkan geometry rute untuk seluruh path (multi-segmen).

    Args:
        waypoints: List of (lat, lon) dari titik-titik path

    Returns:
        List of [lat, lon] yang membentuk rute lengkap mengikuti jalan.
        Titik duplikat di perbatasan segmen dihilangkan.
    """
    if len(waypoints) < 2:
        return [list(wp) for wp in waypoints]

    full_geometry: List[List[float]] = []

    for i in range(len(waypoints) - 1):
        lat1, lon1 = waypoints[i]
        lat2, lon2 = waypoints[i + 1]
        segment = get_road_geometry(lat1, lon1, lat2, lon2)

        if full_geometry and segment:
            # Hilangkan titik duplikat di sambungan segmen
            full_geometry.extend(segment[1:])
        else:
            full_geometry.extend(segment)

    return full_geometry
