"""
Local text embeddings via fastembed (ONNX Runtime, Qdrant's library).

Runs entirely on CPU, no API key, no per-call cost - a deliberate choice so
OceanGPT's RAG layer has zero external dependency for embeddings. Unlike
sentence-transformers, fastembed has no PyTorch dependency, which keeps the
install small and the memory footprint low enough for free-tier hosting
(e.g. Render's free web service, ~512MB RAM). The model (BAAI/bge-small-en-v1.5,
~130MB) is downloaded once from Hugging Face and cached on first use.
"""

from functools import lru_cache

import numpy as np

from app.config import get_settings

settings = get_settings()


@lru_cache
def _get_model():
    # Imported lazily so the fastembed/onnxruntime import only happens once,
    # on first actual use, not at module load time.
    from fastembed import TextEmbedding

    return TextEmbedding(model_name=settings.embedding_model_name)


async def embed_texts(texts: list[str]) -> np.ndarray:
    """Embed a batch of texts, returning an (N, D) float32 array."""
    if not texts:
        return np.zeros((0, 1), dtype=np.float32)

    model = _get_model()
    vectors = list(model.embed(texts))
    return np.array(vectors, dtype=np.float32)


async def embed_query(text: str) -> np.ndarray:
    """Embed a single query string, returning a (D,) float32 vector."""
    arr = await embed_texts([text])
    return arr[0]
