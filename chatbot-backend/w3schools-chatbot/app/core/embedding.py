from __future__ import annotations

from sentence_transformers import SentenceTransformer

DEFAULT_MODEL_NAME = "all-MiniLM-L6-v2"


def load_embedding_model(model_name: str = DEFAULT_MODEL_NAME) -> SentenceTransformer:
    return SentenceTransformer(model_name)


def embed_query(model: SentenceTransformer, query: str) -> list[float]:
    return model.encode(query).tolist()
