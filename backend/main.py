import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

load_dotenv()

from geo.loader import load_all_datasets
from routers.chat import router as chat_router
from routers.poi import router as poi_router

app = FastAPI(title="Ask Rovereto API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    data_dir = Path(os.getenv("DATA_DIR", "../data/processed"))
    app.state.datasets = load_all_datasets(data_dir)
    print(f"Datasets caricati: {list(app.state.datasets.keys())}")


@app.get("/health")
def health():
    datasets = getattr(app.state, "datasets", {})
    return {
        "status": "ok",
        "datasets_loaded": len(datasets),
        "features_count": {k: len(v) for k, v in datasets.items()},
    }


# Serve GeoJSON processati al frontend
data_dir = Path(os.getenv("DATA_DIR", "../data/processed"))
if data_dir.exists():
    app.mount("/static", StaticFiles(directory=str(data_dir)), name="static")

app.include_router(chat_router, prefix="/api")
app.include_router(poi_router, prefix="/api")
