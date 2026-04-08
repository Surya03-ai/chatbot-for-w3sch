from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, List

import chromadb
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

from scraper.rag_chatbot import (
    build_prompt,
    configure_gemini,
    embed_query,
    generate_answer,
    check_relevance,
    retrieve_documents,
)

# Configuration
MODEL_NAME = "all-MiniLM-L6-v2"
DB_PATH = "scraper/chroma_db"
COLLECTION_NAME = "w3chunks"
TOP_K = 3

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "has",
    "have",
    "how",
    "i",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "what",
    "when",
    "where",
    "which",
    "with",
    "why",
    "you",
}


@dataclass
class RetrievedChunk:
    text: str
    distance: float | None
    similarity: float
    metadata: dict


@dataclass
class RAGEvaluationResult:
    query: str
    faithfulness: float
    relevance: float
    context_precision: float
    context_recall: float
    hallucination_score: float
    hallucination_risk: str


def normalize_text(text: str) -> list[str]:
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    return [token for token in tokens if token not in STOPWORDS and len(token) > 1]


def unique_tokens(text: str) -> set[str]:
    return set(normalize_text(text))


def token_overlap_score(source: str, target: str) -> float:
    source_tokens = unique_tokens(source)
    target_tokens = unique_tokens(target)
    if not source_tokens or not target_tokens:
        return 0.0
    return len(source_tokens & target_tokens) / len(source_tokens)


def symmetric_overlap_score(left: str, right: str) -> float:
    left_tokens = unique_tokens(left)
    right_tokens = unique_tokens(right)
    if not left_tokens or not right_tokens:
        return 0.0
    union = left_tokens | right_tokens
    return len(left_tokens & right_tokens) / len(union)


def similarity_from_distance(distance: float | None) -> float:
    if distance is None:
        return 0.0
    return max(0.0, 1.0 - distance)


def load_embedding_model() -> SentenceTransformer:
    return SentenceTransformer(MODEL_NAME)


def load_collection():
    client = chromadb.PersistentClient(path=DB_PATH)
    return client.get_collection(name=COLLECTION_NAME)


def embedding_similarity(model: SentenceTransformer, left: str, right: str) -> float:
    if not left.strip() or not right.strip():
        return 0.0

    left_embedding = model.encode(left, convert_to_tensor=False)
    right_embedding = model.encode(right, convert_to_tensor=False)
    similarity = cosine_similarity([left_embedding], [right_embedding])[0][0]
    return max(0.0, min(1.0, float(similarity)))


def parse_context_blocks(context: str, sources: list[dict], distances: list[float]) -> list[RetrievedChunk]:
    pattern = r"\[Document \d+\]\nTitle: .*?(?=\n\n\[Document \d+\]|\Z)"
    blocks = re.findall(pattern, context, flags=re.DOTALL)
    retrieved: list[RetrievedChunk] = []

    for index, block in enumerate(blocks):
        lines = block.splitlines()
        text = "\n".join(lines[2:]) if len(lines) >= 3 else ""

        source = sources[index] if index < len(sources) else {}
        distance = distances[index] if index < len(distances) else None
        metadata = {
            "title": source.get("title", "Unknown"),
            "url": source.get("url", "N/A"),
            "rank": source.get("rank", index + 1),
        }
        retrieved.append(
            RetrievedChunk(
                text=text,
                distance=distance,
                similarity=similarity_from_distance(distance),
                metadata=metadata,
            )
        )

    return retrieved


def chunk_relevance(model: SentenceTransformer, query: str, chunk_text: str) -> float:
    return embedding_similarity(model, query, chunk_text)


def context_precision(
    model: SentenceTransformer, query: str, chunks: Iterable[RetrievedChunk]
) -> float:
    chunks = list(chunks)
    if not chunks:
        return 0.0

    relevant_chunks = sum(
        1 for chunk in chunks if chunk_relevance(model, query, chunk.text) >= 0.35
    )
    return relevant_chunks / len(chunks)


def context_recall(
    model: SentenceTransformer, query: str, answer: str, chunks: Iterable[RetrievedChunk]
) -> float:
    chunks = list(chunks)
    if not chunks:
        return 0.0

    query_chunk_scores = [chunk_relevance(model, query, chunk.text) for chunk in chunks]
    answer_chunk_scores = [embedding_similarity(model, answer, chunk.text) for chunk in chunks]

    if not query_chunk_scores:
        return 0.0

    query_coverage = sum(query_chunk_scores) / len(query_chunk_scores)
    answer_support = sum(answer_chunk_scores) / len(answer_chunk_scores) if answer_chunk_scores else 0.0
    return max(0.0, min(1.0, (query_coverage + answer_support) / 2))


def faithfulness_score(
    model: SentenceTransformer, answer: str, chunks: Iterable[RetrievedChunk]
) -> float:
    chunks = list(chunks)
    combined_context = " ".join(chunk.text for chunk in chunks)
    if not answer.strip() or not combined_context.strip():
        return 0.0

    return embedding_similarity(model, answer, combined_context)


def relevance_score(model: SentenceTransformer, query: str, answer: str) -> float:
    if not query.strip() or not answer.strip():
        return 0.0
    return embedding_similarity(model, query, answer)


def hallucination_score(model: SentenceTransformer, answer: str, chunks: Iterable[RetrievedChunk]) -> float:
    faithfulness = faithfulness_score(model, answer, chunks)
    return max(0.0, min(1.0, 1.0 - faithfulness))


def hallucination_risk_label(score: float) -> str:
    if score < 0.25:
        return "Low"
    if score < 0.5:
        return "Medium"
    return "High"


def evaluate_rag(
    model: SentenceTransformer, query: str, answer: str, chunks: list[RetrievedChunk]
) -> RAGEvaluationResult:
    faithfulness = faithfulness_score(model, answer, chunks)
    relevance = relevance_score(model, query, answer)
    precision = context_precision(model, query, chunks)
    recall = context_recall(model, query, answer, chunks)
    hallucination = hallucination_score(model, answer, chunks)

    return RAGEvaluationResult(
        query=query,
        faithfulness=round(faithfulness, 2),
        relevance=round(relevance, 2),
        context_precision=round(precision, 2),
        context_recall=round(recall, 2),
        hallucination_score=round(hallucination, 2),
        hallucination_risk=hallucination_risk_label(hallucination),
    )


def format_result(result: RAGEvaluationResult) -> str:
    return (
        f"Faithfulness: {result.faithfulness:.2f}\n"
        f"Relevance: {result.relevance:.2f}\n"
        f"Context Precision: {result.context_precision:.2f}\n"
        f"Context Recall: {result.context_recall:.2f}\n"
        f"Hallucination Score: {result.hallucination_score:.2f}\n"
        f"Hallucination Risk: {result.hallucination_risk}"
    )


def run_examples() -> None:
    print("=" * 80)
    print("RAG EVALUATION")
    print("=" * 80)

    embed_model = load_embedding_model()
    collection = load_collection()
    gemini_model = configure_gemini()

    examples = [
        {
            "query": "What is HTML?",
        },
        {
            "query": "How do CSS selectors work?",
        },
        {
            "query": "What does JavaScript do on a webpage?",
        },
    ]

    for example in examples:
        query = example["query"]
        query_embedding = embed_query(embed_model, query)
        context, sources, distances = retrieve_documents(collection, query_embedding)
        chunks = parse_context_blocks(context, sources, distances)
        relevance = check_relevance(context, distances)
        context = context[:3000]
        prompt = build_prompt(context, query)
        answer = generate_answer(gemini_model, prompt)
        result = evaluate_rag(embed_model, query, answer, chunks)

        print(f"Query: {query}")
        print(f"Generated Answer: {answer}")
        print(format_result(result))
        print()


if __name__ == "__main__":
    run_examples()
