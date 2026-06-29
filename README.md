# DarahNet - Sistem Pencarian Donor Darah

DarahNet adalah aplikasi web untuk mencari fasilitas donor darah terdekat berdasarkan lokasi awal, golongan darah, jumlah kantong, dan waktu pencarian. Aplikasi ini memakai FastAPI sebagai backend dan Leaflet sebagai peta interaktif di frontend.

## Fitur Utama

- Pencarian dengan algoritma A* saja.
- Pencarian dengan algoritma BFS saja.
- Mode perbandingan A* vs BFS dengan panel map, tree eksplorasi, dan tabel metrik.
- Visualisasi node fasilitas donor pada peta global.
- Animasi eksplorasi node sebelum rute hasil ditampilkan.
- Panel tree untuk melihat proses eksplorasi algoritma.
- Checklist untuk menampilkan struktur graf atau edge antar node.
- Filter berdasarkan golongan darah, stok kantong, dan jam operasional.

## Teknologi

- Backend: Python, FastAPI, Pydantic, Uvicorn.
- Frontend: HTML, CSS, JavaScript.
- Peta: Leaflet dan CartoDB Dark Matter tiles.
- Visualisasi tree: D3.js.

## Struktur Project

```text
donor_darah/
  backend/
    algorithms/
      astar.py
      bfs.py
      heuristic.py
    data/
      loader.py
      nodes.json
    models/
      graph.py
      nodes.py
    routers/
      search.py
    main.py
    requirements.txt
    run_interactive.py
  frontend/
    index.html
    style.css
    app.js
  .gitignore
  README.md
```

Catatan kebersihan project: folder virtual environment seperti `backend/venv/` dan folder cache Python seperti `__pycache__/` tidak perlu masuk repository. File `.gitignore` sudah disiapkan untuk mencegah file seperti itu ikut tercatat ke depannya.

## Cara Menjalankan

Masuk ke folder backend:

```bash
cd backend
```

Buat dan aktifkan virtual environment jika belum ada:

```bash
python -m venv venv
.\venv\Scripts\activate
```

Install dependency:

```bash
pip install -r requirements.txt
```

Jalankan server:

```bash
uvicorn main:app --reload
```

Buka aplikasi di browser:

```text
http://localhost:8000
```

Dokumentasi API otomatis tersedia di:

```text
http://localhost:8000/docs
```

## Endpoint API

### GET `/api/nodes`

Mengambil data node fasilitas dan edge graf.

Response utama:

```json
{
  "nodes": [],
  "edges": []
}
```

### GET `/api/search`

Menjalankan pencarian rute donor darah.

Query parameter:

- `start_id`: ID node awal.
- `blood_type`: golongan darah, misalnya `A`, `B`, `AB`, atau `O`.
- `qty`: jumlah kantong darah yang dibutuhkan.
- `current_time`: waktu pencarian dalam format `HH:MM`.
- `algorithm`: `astar` atau `bfs`.

Contoh:

```text
/api/search?start_id=rs1&blood_type=A&qty=1&current_time=09:00&algorithm=astar
```

## Data Lokasi

Data fasilitas donor berada di:

```text
backend/data/nodes.json
```

Setiap node berisi informasi seperti ID, nama fasilitas, tipe, koordinat, stok darah, dan jam operasional. Edge graf dibentuk oleh backend dari data node untuk kebutuhan visualisasi dan pencarian.

## Catatan Pengembangan

- Jalankan perintah backend dari folder `backend/` karena import modul lokal disusun untuk konteks folder tersebut.
- Jika mengubah frontend, refresh browser dengan hard reload agar asset versi terbaru dimuat.
- Untuk menambah algoritma baru, letakkan implementasi di `backend/algorithms/` lalu hubungkan melalui `backend/routers/search.py`.
- Untuk mengubah tampilan peta dan panel visualisasi, edit `frontend/style.css` dan `frontend/app.js`.
- `backend/run_interactive.py` dapat dipakai sebagai helper CLI untuk membandingkan BFS dan A* tanpa membuka browser.
