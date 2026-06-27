"""
OceanGPT backend entrypoint.

Run with:
    uvicorn app.main:app --reload --port 8000
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.rag.store import vector_store
from app.routes import chat, environment, species

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("oceangpt")

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Building RAG knowledge base embeddings...")
    await vector_store.build()
    logger.info("Loaded %d knowledge base documents.", len(vector_store.documents))
    yield


app = FastAPI(
    title="OceanGPT API",
    description="Backend for the OceanGPT marine intelligence dashboard - "
                 "RAG over marine knowledge + live OBIS/WoRMS/NOAA/Open-Meteo data.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(species.router)
app.include_router(environment.router)


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "knowledge_base_docs": len(vector_store.documents)}
