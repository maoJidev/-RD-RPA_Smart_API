# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from src.api.controllers import rag_router, scrape_router

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="⚖️ RPA RD Scraper & ChatBot (Modular API)",
    description="API สำหรับรวบรวมข้อหารือภาษีและตอบคำถามแบบ RAG (Refactored)",
    version="2.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(rag_router.router)
app.include_router(scrape_router.router)

@app.get("/")
def read_root():
    return {
        "message": "Welcome to the Modular RPA API",
        "docs": "/docs",
        "status": "online"
    }

if __name__ == "__main__":
    import uvicorn
    # Start Server
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
