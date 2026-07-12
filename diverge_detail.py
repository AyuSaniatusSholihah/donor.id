import sys
sys.path.insert(0, 'backend')
from data.loader import load_graph_from_json
from algorithms.astar import astar_search
from algorithms.bfs import bfs_search
from collections import defaultdict

graph = load_graph_from_json('backend/data/nodes.json', k=3)
node_ids = list(graph.nodes.keys())
BLOOD_TYPES = ['A', 'B', 'AB', 'O']
QTY_VALUES = [1, 5, 10]
TIMES = ['08:00', '12:00', '20:00', '23:00']

by_bt_qty = defaultdict(lambda: {'total': 0, 'beda': 0})
details = []

for sid in node_ids:
    sname = graph.get_node(sid).name
    for bt in BLOOD_TYPES:
        for qty in QTY_VALUES:
            for t in TIMES:
                _, _, _, at, _ = astar_search(graph, sid, bt, qty, t)
                _, _, _, bt2, _ = bfs_search(graph, sid, bt, qty, t)
                key = (bt, qty)
                by_bt_qty[key]['total'] += 1
                if at != bt2:
                    by_bt_qty[key]['beda'] += 1
                    aname = graph.get_node(at).name if at else '-'
                    bname = graph.get_node(bt2).name if bt2 else '-'
                    details.append((sname, bt, qty, t, aname, bname))

print("Divergensi per Golongan Darah x Jumlah Kantong:")
print(f"{'Gol':>4} {'Qty':>4}  {'Beda':>5} / {'Total':>5}  %")
print("-" * 35)
for bt in BLOOD_TYPES:
    for qty in QTY_VALUES:
        d = by_bt_qty[(bt, qty)]
        pct = d['beda'] / d['total'] * 100 if d['total'] else 0
        print(f"{bt:>4} {qty:>4}  {d['beda']:>5} / {d['total']:>5}  {pct:.0f}%")
    print()

print()
print("Contoh skenario beda (waktu 08:00):")
seen = set()
for sname, bt, qty, t, aname, bname in details:
    if t != '08:00':
        continue
    k = (sname, bt, qty)
    if k in seen:
        continue
    seen.add(k)
    print(f"  Start={sname}, Gol={bt}, Qty={qty} -> A*={aname} | BFS={bname}")
