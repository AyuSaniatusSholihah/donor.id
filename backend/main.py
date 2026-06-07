import os
# pyrefly: ignore [missing-import]
from fastapi import FastAPI
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware
# pyrefly: ignore [missing-import]
from fastapi.staticfiles import StaticFiles
# pyrefly: ignore [missing-import]
from fastapi.responses import FileResponse
# pyrefly: ignore [missing-import]              
from routers.search import router as search_router

app = FastAPI(
    title="Sistem Pencarian Donor Darah (A* & BFS)",
    description="Sistem rekomendasi pencarian rute fasilitas donor darah berdasarkan lokasi, stok, dan waktu operasional.",
    version="1.0.0"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Router
app.include_router(search_router, prefix="/api")

# Define frontend path
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")

# Serve index.html at root
@app.get("/")
def read_index():
    index_file = os.path.join(frontend_path, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "Sistem Backend Pencarian Donor Darah Aktif. Folder frontend tidak ditemukan."}

# Mount static files (JS, CSS, etc.)
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path), name="frontend")
