# DonorinSolo — Sistem Pencarian Donor Darah

DonorinSolo adalah aplikasi web untuk mencari fasilitas donor darah terdekat berdasarkan lokasi awal, golongan darah, jumlah kantong, dan waktu pencarian. Backend menggunakan FastAPI + algoritma A* / BFS, frontend menggunakan Leaflet dengan visualisasi rute **jalan nyata** dari OpenStreetMap (via OSRM).

---

## Fitur Utama

- Pencarian dengan **A*** (dipandu heuristik multi-criteria).
- Pencarian dengan **BFS** (level-order).
- Mode **perbandingan A* vs BFS** dengan animasi eksplorasi, pohon traversal, dan tabel metrik.
- Visualisasi rute mengikuti **jalan nyata** (data OpenStreetMap, tanpa API key berbayar).
- Animasi eksplorasi node langkah demi langkah di peta.
- Panel tree untuk melihat proses eksplorasi algoritma.
- Checklist untuk menampilkan edge antar node pada graf.
- Filter berdasarkan golongan darah, stok kantong, dan jam operasional.

---

## Teknologi

| Komponen | Teknologi |
|----------|-----------|
| Backend | Python 3.10+, FastAPI, Pydantic, Uvicorn |
| Routing | OSRM Demo Server (OpenStreetMap, gratis, tanpa API key) |
| Frontend | HTML, CSS, Vanilla JavaScript |
| Peta | Leaflet.js, CartoDB Dark Matter tiles |
| Visualisasi tree | D3.js |

---

## Struktur Project

```text
donor_darah/
  backend/
    algorithms/
      astar.py          ← Implementasi A*
      bfs.py            ← Implementasi BFS
      heuristic.py      ← Fungsi heuristik h(n)
    data/
      loader.py         ← Loader graph + integrasi OSRM
      nodes.json        ← Data 14 fasilitas donor di Solo
      osrm_router.py    ← Modul OSRM (jarak & geometry rute jalan nyata)
    models/
      graph.py          ← Model graph adjacency list
      nodes.py          ← Model node (PMI, BDRS, DonorSukarela)
    routers/
      search.py         ← Endpoint API /search dan /nodes
    main.py             ← Entry point FastAPI + static files
    requirements.txt    ← Daftar dependency Python
    run_interactive.py  ← CLI helper (tanpa browser)
  frontend/
    index.html          ← Halaman utama
    style.css           ← Stylesheet
    app.js              ← Logika frontend + Leaflet
  .gitignore
  README.md
```

---

## Download & Install yang Dibutuhkan

Sebelum menjalankan project, pastikan semua software berikut sudah didownload dan diinstall.

---

### 1. Python 3.10 atau Lebih Baru

Python adalah runtime utama untuk backend.

**Download:**
> 🔗 https://www.python.org/downloads/

**Langkah install (Windows):**
1. Buka link di atas, klik **Download Python 3.x.x** (versi terbaru).
2. Jalankan installer `.exe`.
3. ✅ **Centang "Add Python to PATH"** sebelum klik Install.
4. Klik **Install Now**.

**Verifikasi setelah install:**
```bash
python --version
# Output yang diharapkan: Python 3.10.x atau lebih tinggi

pip --version
# Output yang diharapkan: pip 23.x.x ...
```

> **pip** sudah otomatis terinstall bersama Python. pip digunakan untuk menginstall library Python yang dibutuhkan project ini.

---

### 2. Git *(Opsional — hanya jika ingin clone via Git)*

Jika kamu mendapat project dalam bentuk ZIP, bagian ini bisa dilewati.

**Download:**
> 🔗 https://git-scm.com/downloads

**Langkah install (Windows):**
1. Download installer untuk Windows.
2. Jalankan dan ikuti wizard (klik Next terus, pengaturan default sudah cukup).

**Verifikasi:**
```bash
git --version
# Output: git version 2.x.x
```

---

### 3. Browser Modern

Tidak perlu install tambahan jika sudah ada salah satu:
- Google Chrome (direkomendasikan)
- Mozilla Firefox
- Microsoft Edge

---

### 4. Library Python (Diinstall Otomatis via pip)

Setelah Python terinstall, library berikut akan diinstall otomatis dengan perintah `pip install -r requirements.txt`:

| Library | Versi Minimum | Fungsi |
|---------|---------------|--------|
| `fastapi` | 0.110.0 | Framework backend API |
| `uvicorn` | 0.28.0 | ASGI server untuk menjalankan FastAPI |
| `pydantic` | 2.6.0 | Validasi dan serialisasi data |
| `requests` | 2.31.0 | HTTP client untuk memanggil OSRM routing |

> Semua library di atas akan diinstall dari file `backend/requirements.txt` — **tidak perlu download manual**.

---

### Ringkasan: Apa yang Perlu Didownload?

| Software | Wajib? | Link Download |
|----------|--------|---------------|
| Python 3.10+ | ✅ Ya | https://www.python.org/downloads/ |
| Git | ⬜ Opsional | https://git-scm.com/downloads |
| Browser (Chrome/Firefox/Edge) | ✅ Ya | Biasanya sudah ada |
| Library Python (`fastapi`, dll.) | ✅ Ya | Otomatis via `pip install -r requirements.txt` |

---

## Cara Menjalankan

### 1. Clone / Download Project

Jika menggunakan Git:

```bash
git clone <url-repo>
cd donor_darah
```

Atau extract ZIP lalu buka folder `donor_darah`.

---

### 2. Masuk ke Folder Backend

```bash
cd backend
```

> ⚠️ **Penting**: Semua perintah berikut dijalankan dari dalam folder `backend/`, bukan dari root project.

---

### 3. Buat Virtual Environment

```bash
python -m venv venv
```

---

### 4. Aktifkan Virtual Environment

**Windows (Command Prompt / PowerShell):**
```bash
.\venv\Scripts\activate
```

**macOS / Linux:**
```bash
source venv/bin/activate
```

Setelah aktif, prompt akan berubah menampilkan `(venv)` di depannya.

---

### 5. Install Dependency

```bash
pip install -r requirements.txt
```

Paket yang akan diinstall:
- `fastapi` — framework backend
- `uvicorn` — ASGI server
- `pydantic` — validasi data
- `requests` — HTTP client untuk OSRM

---

### 6. Jalankan Server

```bash
uvicorn main:app --reload
```

Atau jika ingin dapat diakses dari perangkat lain di jaringan yang sama:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Contoh output saat startup berhasil:**

```
INFO:     Will watch for changes in these directories: ['.../backend']
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
[OSRM] Membangun distance matrix untuk 14 node (1 batch request)...
[OSRM] Distance matrix berhasil dibangun untuk 182 pasang node.
[OSRM] Graph selesai. 14 node, edge menggunakan jarak jalan nyata.
INFO:     Application startup complete.
```

> 💡 **Catatan startup**: Saat pertama kali dijalankan, backend akan memanggil OSRM (OpenStreetMap Routing Machine) untuk mengambil jarak jalan nyata antar semua fasilitas. Proses ini membutuhkan **koneksi internet** dan berlangsung sekitar **5–15 detik**. Setelah itu server siap digunakan.
>
> Jika koneksi OSRM gagal (tidak ada internet / server timeout), aplikasi tetap berjalan normal dengan fallback ke jarak Haversine (garis lurus).

---

### 7. Buka Aplikasi di Browser

```
http://localhost:8000
```

Dokumentasi API interaktif (Swagger UI):

```
http://localhost:8000/docs
```

---

### 8. Cara Menggunakan Aplikasi

1. **Pilih Lokasi Awal** — dropdown berisi 14 fasilitas donor di Surakarta.
2. **Pilih Golongan Darah** — A, B, AB, atau O.
3. **Isi Jumlah Kantong** — minimal 1.
4. **Atur Waktu** — default waktu lokal saat ini.
5. **Pilih Mode Pencarian**:
   - `A* saja` — tampilkan rute terbaik dengan A*
   - `BFS saja` — tampilkan rute dengan BFS
   - `Bandingkan A* vs BFS` — tampilkan kedua algoritma secara berdampingan
6. Klik **Cari Fasilitas**.
7. Animasi eksplorasi akan berjalan, diikuti tampilan **rute jalan nyata** dari titik awal ke fasilitas tujuan.

---

## Menghentikan Server

Tekan `Ctrl + C` di terminal tempat server berjalan.

---

## Troubleshooting

| Masalah | Solusi |
|---------|--------|
| `ModuleNotFoundError` | Pastikan virtual environment sudah diaktifkan (`.\venv\Scripts\activate`) |
| `Address already in use` | Port 8000 sudah dipakai. Ganti port: `uvicorn main:app --port 8001` |
| Peta tidak muncul | Pastikan koneksi internet aktif (tile peta dari CartoDB) |
| Rute berupa garis lurus | OSRM tidak tersedia saat startup. Restart server dengan koneksi internet aktif |
| Frontend tidak terupdate | Hard reload di browser: `Ctrl + Shift + R` |
| `python` tidak dikenali | Coba `python3` sebagai gantinya |

---

## Endpoint API

### `GET /api/nodes`

Mengembalikan semua node fasilitas dan edge graf.

```json
{
  "nodes": [...],
  "edges": [{"from": "node_1", "to": "node_2", "distance": 0.51}]
}
```

### `GET /api/search`

Menjalankan pencarian rute donor darah.

| Parameter | Tipe | Contoh | Keterangan |
|-----------|------|--------|------------|
| `start_id` | string | `node_1` | ID node awal |
| `blood_type` | string | `A` | Golongan darah: A, B, AB, O |
| `qty` | int | `2` | Jumlah kantong dibutuhkan |
| `current_time` | string | `09:00` | Format HH:MM |
| `algorithm` | string | `astar` | `astar` atau `bfs` |

**Contoh request:**

```
GET /api/search?start_id=node_1&blood_type=A&qty=2&current_time=09:00&algorithm=astar
```

**Response mencakup `path_geometry`** — koordinat jalan nyata untuk visualisasi Leaflet:

```json
{
  "algorithm": "astar",
  "path": [...],
  "path_geometry": [[-7.5615, 110.8351], [-7.5612, 110.8358], ...],
  "distance": 0.51,
  "success": true,
  "message": "[ASTAR] Ditemukan: RS Hermina Solo | Jarak: 0.51 km | ..."
}
```

---

## Catatan Pengembangan

- Jalankan backend **selalu dari folder `backend/`** karena import modul lokal relatif terhadap folder itu.
- Untuk menambah data fasilitas baru, edit `backend/data/nodes.json` lalu restart server.
- Untuk menambah algoritma baru, buat file di `backend/algorithms/` lalu hubungkan via `backend/routers/search.py`.
- `backend/run_interactive.py` dapat dipakai sebagai CLI helper tanpa membuka browser.
- Folder `venv/` dan `__pycache__/` tidak perlu di-commit ke repository (sudah ada di `.gitignore`).
