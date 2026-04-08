from __future__ import annotations

from typing import Any, Tuple


def retrieve_documents(
    collection: Any, query_embedding: list[float], top_k: int = 3
) -> Tuple[str, list[dict], list[float]]:
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    context_parts: list[str] = []
    sources: list[dict] = []

    for i, doc in enumerate(documents):
        meta = metadatas[i] if i < len(metadatas) else {}
        title = meta.get("page_title", "Unknown")
        url = meta.get("source_url", "N/A")
        sources.append(
            {
                "rank": i + 1,
                "title": title,
                "url": url,
                "distance": distances[i] if i < len(distances) else None,
            }
        )
        context_parts.append(f"[Document {i+1}]\nTitle: {title}\n{doc}")

    return "\n\n".join(context_parts), sources, distances
