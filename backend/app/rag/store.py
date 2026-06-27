"""
Lightweight in-memory vector store.

This is intentionally simple - no external vector DB needed. The knowledge
base here is small (a curated set of marine knowledge documents), so a flat
numpy cosine-similarity search is fast enough and has zero infrastructure
cost. If the knowledge base grows into the tens of thousands of chunks,
swap this out for pgvector, Qdrant, or similar - the interface
(`build()` / `search()`) is designed to make that swap easy.
"""

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from app.rag.embed import embed_texts, embed_query

KNOWLEDGE_DIR = Path(__file__).parent / "knowledge"
CACHE_PATH = KNOWLEDGE_DIR / "_embeddings_cache.json"


@dataclass
class Document:
    id: str
    title: str
    text: str


class VectorStore:
    def __init__(self) -> None:
        self.documents: list[Document] = []
        self.embeddings: np.ndarray | None = None

    def _load_documents(self) -> list[Document]:
        docs: list[Document] = []
        for path in sorted(KNOWLEDGE_DIR.glob("*.json")):
            if path.name.startswith("_"):
                continue
            with open(path, encoding="utf-8") as f:
                entries = json.load(f)
            for entry in entries:
                docs.append(Document(id=entry["id"], title=entry["title"], text=entry["text"]))
        return docs

    async def build(self, force_refresh: bool = False) -> None:
        """Load knowledge base docs and compute (or load cached) embeddings."""
        self.documents = self._load_documents()
        if not self.documents:
            self.embeddings = np.zeros((0, 1), dtype=np.float32)
            return

        if not force_refresh and CACHE_PATH.exists():
            cached = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
            cached_ids = cached.get("ids", [])
            if cached_ids == [d.id for d in self.documents]:
                self.embeddings = np.array(cached["vectors"], dtype=np.float32)
                return

        texts = [d.text for d in self.documents]
        self.embeddings = await embed_texts(texts)

        CACHE_PATH.write_text(
            json.dumps({"ids": [d.id for d in self.documents], "vectors": self.embeddings.tolist()}),
            encoding="utf-8",
        )

    async def search(self, query: str, top_k: int = 4) -> list[tuple[Document, float]]:
        """Return the top_k most similar documents to the query, with cosine similarity scores."""
        if self.embeddings is None or len(self.documents) == 0:
            return []

        query_vec = await embed_query(query)
        sims = _cosine_sim(self.embeddings, query_vec)
        top_indices = np.argsort(-sims)[:top_k]
        return [(self.documents[i], float(sims[i])) for i in top_indices]


def _cosine_sim(matrix: np.ndarray, vector: np.ndarray) -> np.ndarray:
    matrix_norms = np.linalg.norm(matrix, axis=1)
    vector_norm = np.linalg.norm(vector)
    denom = matrix_norms * vector_norm
    denom[denom == 0] = 1e-10
    return (matrix @ vector) / denom


# Module-level singleton, initialized once at app startup (see main.py)
vector_store = VectorStore()
