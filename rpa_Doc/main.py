# main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
from logging.handlers import RotatingFileHandler
import os
import requests

from src.api.controllers import rag_router, scrape_router
from src.config.settings import OLLAMA_BASE_URL

# ===============================
# Logging setup
# ===============================
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

file_handler = RotatingFileHandler(
    os.path.join(LOG_DIR, "app.log"),
    maxBytes=5_000_000,
    backupCount=5,
    encoding="utf-8"
)

formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
file_handler.setFormatter(formatter)

root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(file_handler)

for name in ("uvicorn", "uvicorn.error", "uvicorn.access", "rag"):
    lg = logging.getLogger(name)
    lg.setLevel(logging.INFO)
    lg.addHandler(file_handler)
    lg.propagate = False

logger = logging.getLogger("app")

# ===============================
# FastAPI app
# ===============================
app = FastAPI(
    title="⚖️ RPA RD Scraper & ChatBot (Modular API)",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(rag_router.router)
app.include_router(scrape_router.router)


@app.get("/")
def root():
    logger.info("Root accessed")
    return {"status": "online"}


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/ready")
def ready():
    try:
        r = requests.get(
            f"{OLLAMA_BASE_URL}/api/tags",
            timeout=2
        )
        r.raise_for_status()
        return {"status": "ready", "ollama": "reachable"}
    except Exception as e:
        logger.error("Ollama not ready: %s", e)
        return {"status": "not_ready", "ollama": "unreachable"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        workers=1,
        reload=False
    )
