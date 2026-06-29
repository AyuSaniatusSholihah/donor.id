"""
CLI INTERAKTIF — Pencarian Layanan Darah Terdekat (BFS vs A*)

Program ini akan menanyakan input satu per satu (golongan darah, RS asal,
jumlah kantong, waktu pencarian), lalu menjalankan BFS dan A* pada graf
yang sama dan membandingkan hasilnya.

Cara pakai:
    cd backend
    python run_interactive.py
"""
import sys
import time

from data.loader import load_graph_from_json
from algorithms.bfs import bfs_search
from algorithms.astar import astar_search

JSON_PATH = "data/nodes.json"


def cetak_header(judul: str):
    print()
    print("=" * 72)
    print(judul.center(72))
    print("=" * 72)


def tampilkan_daftar_node(graph):
    print("\nDaftar fasilitas (node) yang tersedia:\n")
    print(f"  {'No':<4}{'ID':<10}{'Nama':<32}{'Tipe':<14}{'Jam Operasional'}")
    print(f"  {'-'*4}{'-'*10}{'-'*32}{'-'*14}{'-'*16}")
    id_list = list(graph.nodes.keys())
    for i, nid in enumerate(id_list, start=1):
        n = graph.get_node(nid)
        jam = "24 jam" if n.operational_hours.is_24h else f"{n.operational_hours.open}-{n.operational_hours.close}"
        print(f"  {i:<4}{nid:<10}{n.name:<32}{n.type:<14}{jam}")
    print()
    return id_list


def pilih_node(graph, id_list, prompt="Pilih RS asal (masukkan nomor atau ID)"):
    while True:
        jawab = input(f"{prompt}: ").strip()
        if not jawab:
            continue
        # Boleh masukkan nomor urut atau ID langsung
        if jawab.isdigit():
            idx = int(jawab) - 1
            if 0 <= idx < len(id_list):
                return id_list[idx]
            print(f"  Nomor harus antara 1 dan {len(id_list)}. Coba lagi.")
            continue
        if jawab in graph.nodes:
            return jawab
        print("  ID tidak ditemukan. Coba lagi (lihat daftar di atas).")


def input_golongan_darah():
    valid = {"A", "B", "AB", "O"}
    while True:
        jawab = input("Golongan darah dibutuhkan (A/B/AB/O): ").strip().upper()
        if jawab in valid:
            return jawab
        print("  Golongan darah harus salah satu dari: A, B, AB, O.")


def input_jumlah_kantong():
    while True:
        jawab = input("Jumlah kantong dibutuhkan (angka, default 1): ").strip()
        if not jawab:
            return 1
        if jawab.isdigit() and int(jawab) > 0:
            return int(jawab)
        print("  Masukkan angka bulat positif.")


def input_waktu():
    import re
    while True:
        jawab = input("Waktu pencarian, format HH:MM (default 12:00): ").strip()
        if not jawab:
            return "12:00"
        if re.match(r"^([01]\d|2[0-3]):([0-5]\d)$", jawab):
            return jawab
        print("  Format waktu salah. Contoh yang benar: 09:30 atau 23:15.")


def jalankan_dan_tampilkan(graph, start_id, blood_type, qty, current_time):
    start_node = graph.get_node(start_id)

    cetak_header("INPUT PENCARIAN")
    print(f"  RS asal           : {start_node.name} ({start_id})")
    print(f"  Golongan darah    : {blood_type}")
    print(f"  Jumlah dibutuhkan : {qty} kantong")
    print(f"  Waktu pencarian   : {current_time}")

    hasil = {}

    for nama_algo, fungsi in [("BFS", bfs_search), ("A*", astar_search)]:
        t0 = time.perf_counter()
        path, visited, dist, target, h_detail = fungsi(
            graph, start_id, blood_type, qty, current_time
        )
        elapsed_ms = (time.perf_counter() - t0) * 1000
        hasil[nama_algo] = {
            "path": path,
            "visited": visited,
            "dist": dist,
            "target": target,
            "h_detail": h_detail,
            "time_ms": elapsed_ms,
        }

    for nama_algo, r in hasil.items():
        cetak_header(f"HASIL {nama_algo}")
        if not r["target"]:
            print("  Tidak ditemukan fasilitas yang memenuhi kriteria.")
            continue

        target_node = graph.get_node(r["target"])
        path_names = [graph.get_node(nid).name for nid in r["path"]]
        jam = "24 jam" if target_node.operational_hours.is_24h else f"{target_node.operational_hours.open}-{target_node.operational_hours.close}"

        print(f"  Fasilitas terpilih : {target_node.name} ({r['target']})")
        print(f"  Tipe               : {target_node.type}")
        print(f"  Stok {blood_type:<3}             : {target_node.stock.get(blood_type, 0)} kantong")
        print(f"  Jam operasional    : {jam}")
        print(f"  Jalur              : {' -> '.join(path_names)}")
        print(f"  Total jarak        : {r['dist']:.2f} km")
        print(f"  Node dikunjungi    : {len(r['visited'])} -> {r['visited']}")
        print(f"  Waktu eksekusi     : {r['time_ms']:.4f} ms")

        # Tampilkan detail f(n) = g(n) + h(n) untuk node yang dikunjungi
        if any(v["h"] is not None for v in r["h_detail"].values()):
            print(f"\n  Rincian g(n)/h(n)/f(n) per node yang dikunjungi:")
            print(f"  {'Node':<28}{'g(n)':<10}{'h(n)':<10}{'f(n)':<10}")
            for nid in r["visited"]:
                d = r["h_detail"].get(nid, {})
                h_val = f"{d.get('h'):.3f}" if d.get("h") is not None else "-"
                print(f"  {d.get('node', nid):<28}{d.get('g', 0):<10.3f}{h_val:<10}{d.get('f', 0):<10.3f}")

    cetak_header("PERBANDINGAN BFS vs A*")
    bfs_r, astar_r = hasil["BFS"], hasil["A*"]
    bfs_name = graph.get_node(bfs_r["target"]).name if bfs_r["target"] else "-"
    astar_name = graph.get_node(astar_r["target"]).name if astar_r["target"] else "-"
    bfs_dist_str = f"{bfs_r['dist']:.2f}" if bfs_r["target"] else "-"
    astar_dist_str = f"{astar_r['dist']:.2f}" if astar_r["target"] else "-"

    print(f"  {'Metrik':<22}{'BFS':<28}{'A*':<28}")
    print(f"  {'-'*22}{'-'*28}{'-'*28}")
    print(f"  {'Fasilitas terpilih':<22}{bfs_name:<28}{astar_name:<28}")
    print(f"  {'Total jarak (km)':<22}{bfs_dist_str:<28}{astar_dist_str:<28}")
    print(f"  {'Node dikunjungi':<22}{len(bfs_r['visited']):<28}{len(astar_r['visited']):<28}")
    print(f"  {'Waktu eksekusi (ms)':<22}{bfs_r['time_ms']:<28.4f}{astar_r['time_ms']:<28.4f}")

    print()
    if bfs_r["target"] == astar_r["target"]:
        print("  >> Kedua algoritma memilih fasilitas yang SAMA.")
    else:
        print("  >> Kedua algoritma memilih fasilitas yang BERBEDA.")
        print("     (A* mempertimbangkan stok & jam operasional dalam heuristik, BFS tidak)")

    if bfs_r["target"] and astar_r["target"]:
        if len(astar_r["visited"]) < len(bfs_r["visited"]):
            print(f"  >> A* lebih efisien: {len(astar_r['visited'])} vs {len(bfs_r['visited'])} node dikunjungi.")
        elif len(bfs_r["visited"]) < len(astar_r["visited"]):
            print(f"  >> BFS lebih sedikit mengunjungi node kali ini: {len(bfs_r['visited'])} vs {len(astar_r['visited'])}.")
        else:
            print("  >> Jumlah node yang dikunjungi SAMA pada skenario ini.")
    print("=" * 72)


def main():
    print("Memuat graf dari data/nodes.json ...")
    try:
        graph = load_graph_from_json(JSON_PATH, k=3)
    except FileNotFoundError:
        print(f"Error: file '{JSON_PATH}' tidak ditemukan.")
        print("Pastikan kamu menjalankan script ini dari dalam folder 'backend'.")
        sys.exit(1)

    print(f"Graf berhasil dimuat: {len(graph.nodes)} node.\n")

    while True:
        id_list = tampilkan_daftar_node(graph)
        start_id = pilih_node(graph, id_list)
        blood_type = input_golongan_darah()
        qty = input_jumlah_kantong()
        current_time = input_waktu()

        jalankan_dan_tampilkan(graph, start_id, blood_type, qty, current_time)

        print()
        lagi = input("Cari lagi dengan skenario lain? (y/n): ").strip().lower()
        if lagi != "y":
            print("Selesai. Terima kasih!")
            break


if __name__ == "__main__":
    main()
