# Sistem Pencarian Donor Darah (A* & BFS) 🩸

Aplikasi web untuk mencari rute terdekat ke fasilitas donor darah (Rumah Sakit, UTD PMI, atau Donor Sukarela) berdasarkan **golongan darah**, **stok ketersediaan**, dan **jam operasional**. Sistem ini menggunakan dua algoritma pencarian rute: **A-Star (A*)** dan **Breadth-First Search (BFS)**.

---

## 📂 Struktur Direktori Program

Untuk memudahkan modifikasi, berikut adalah struktur folder dari aplikasi ini:

```text
donor_darah/
│
├── backend/                  # Folder utama untuk logika server dan algoritma (Python)
│   ├── algorithms/           # Implementasi algoritma pencarian rute
│   │   ├── astar.py          # Logika algoritma A* Search
│   │   └── bfs.py            # Logika algoritma BFS Search
│   ├── data/
│   │   ├── nodes.json        # 🗄️ DATABASE LOKASI: Tempat menyimpan data RS/PMI & Stok Darah
│   │   └── loader.py         # Skrip untuk membaca nodes.json ke dalam struktur graf
│   ├── models/               # Model data (Struktur Objek)
│   │   ├── graph.py          # Struktur data Graf (Nodes & Edges)
│   │   └── nodes.py          # Definisi objek lokasi (RS, PMI, Sukarela)
│   ├── routers/
│   │   └── search.py         # API Endpoints (Menangani request dari frontend ke algoritma)
│   ├── main.py               # 🚀 FILE UTAMA BACKEND: Konfigurasi FastAPI dan serve frontend
│   └── requirements.txt      # Daftar library Python yang dibutuhkan
│
├── frontend/                 # Folder utama untuk antarmuka pengguna (HTML/JS)
│   ├── index.html            # Kerangka UI (Sidebar dan Peta)
│   ├── style.css             # Tampilan dan gaya visual
│   └── app.js                # 🗺️ LOGIKA PETA: Integrasi Leaflet.js dan memanggil API
│
└── README.md                 # Dokumentasi yang sedang kamu baca
```

---

## 🛠️ Panduan Mengedit untuk Developer

Jika kamu ingin melakukan modifikasi pada program ini, berikut adalah panduan letak file yang harus kamu edit:

### 1. Menambah/Mengubah Data Lokasi & Stok Darah
Buka file: **`backend/data/nodes.json`**
- Di file ini kamu bisa menambahkan data Rumah Sakit atau PMI baru.
- Pastikan mengisi properti `lat` (latitude) dan `lon` (longitude) dengan benar agar muncul di peta.
- Bagian `connections` mengatur hubungan/jalur antar lokasi beserta jarak aslinya. Tambahkan ID lokasi tujuan di sini jika ada jalur baru.

### 2. Mengubah Titik Fokus Peta (Map Center)
Buka file: **`frontend/app.js`**
- Cari fungsi `initMap()`.
- Ubah koordinat di dalam fungsi `.setView([-7.5666, 110.8283], 14)` ke koordinat kota yang kamu inginkan (saat ini diset ke Surakarta).

### 3. Mengubah Logika Pencarian Rute (A* & BFS)
Buka folder: **`backend/algorithms/`**
- Jika kamu ingin memperbaiki atau memodifikasi nilai fungsi heuristik A*, buka file `astar.py`.
- Jika kamu ingin mengatur urutan kunjungan BFS, edit file `bfs.py`.

### 4. Menambah Fitur API Baru
Buka file: **`backend/routers/search.py`**
- File ini adalah penghubung antara tombol "Cari" di frontend dengan algoritma Python di backend.
- Jika ada penambahan parameter filter baru (misal: filter fasilitas yang buka 24 jam saja), tambahkan parameternya di endpoint `@router.get("/search")`.

---

## 🚀 Cara Menjalankan Aplikasi

Aplikasi ini menggunakan Python dengan framework FastAPI. Ikuti langkah di bawah untuk menjalankannya.

**Langkah 1: Masuk ke folder backend**
```bash
cd backend
```

**Langkah 2: Aktifkan Virtual Environment**
- Windows: `.\venv\Scripts\activate`
- Mac/Linux: `source venv/bin/activate`

**Langkah 3: Install Dependencies (Jika belum)**
```bash
pip install -r requirements.txt
```

**Langkah 4: Jalankan Server FastAPI**
```bash
uvicorn main:app --reload
```

**Langkah 5: Buka di Browser**
Akses aplikasi melalui browser dengan URL:
👉 **http://localhost:8000**

*(Dokumentasi API untuk testing bisa diakses di: `http://localhost:8000/docs`)*
