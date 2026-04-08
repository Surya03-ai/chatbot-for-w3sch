from __future__ import annotations

import logging
import os
from typing import List, Optional

import google.generativeai as genai

from app.core.embedding import DEFAULT_MODEL_NAME, embed_query
from app.core.generation import GeminiModelClient, configure_gemini as _configure_gemini
from app.core.generation import generate_answer
from app.core.guards import check_greeting, check_input, check_relevance
from app.core.prompt import build_prompt
from app.core.retrieval import retrieve_documents
from app.services.chat_service import ChatService

EMBEDDING_MODEL = DEFAULT_MODEL_NAME
PREFERRED_GEMINI_MODEL = "gemini-pro"
DB_PATH = "./scraper/chroma_db"
COLLECTION_NAME = "w3chunks"
TOP_K = 5
MAX_CHAT_HISTORY = 5
QUIZ_INTENT_WORDS = ("quiz", "question", "mcq")

LOGGER = logging.getLogger("w3schools_rag")

GREETING_KEYWORDS = {
    "hello",
    "hey",
    "hi",
    "hiya",
    "good morning",
    "good afternoon",
    "good evening",
}
FAREWELL_KEYWORDS = {
    "bye",
    "goodbye",
    "see you",
    "see ya",
    "farewell",
    "take care",
    "catch you later",
}
GRATITUDE_KEYWORDS = {
    "thanks",
    "thank you",
    "thanks a lot",
    "thank you so much",
    "thx",
}


def configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")


def load_collection():
    from app.db.chroma import get_collection

    return get_collection(db_path=DB_PATH, collection_name=COLLECTION_NAME)


def get_generate_content_models() -> List[str]:
    available_models = list(genai.list_models())
    valid_models: List[str] = []

    for model in available_models:
        model_name = getattr(model, "name", "")
        supported_methods = list(
            getattr(model, "supported_generation_methods", []) or []
        )
        if "generateContent" in supported_methods and model_name:
            valid_models.append(model_name.replace("models/", "", 1))

    if not valid_models:
        raise RuntimeError("No Gemini models found that support generateContent")

    return valid_models


def build_gemini_candidates(valid_models: List[str]) -> List[str]:
    candidates: List[str] = []
    if PREFERRED_GEMINI_MODEL in valid_models:
        candidates.append(PREFERRED_GEMINI_MODEL)

    for model_name in valid_models:
        if model_name not in candidates:
            candidates.append(model_name)

    return candidates


def configure_gemini() -> GeminiModelClient:
    api_key = os.getenv("GEMINI_API_KEY", "")
    valid_models = get_generate_content_models()
    candidate_models = build_gemini_candidates(valid_models)
    return _configure_gemini(api_key, candidate_models)


def classify_intent(query: str) -> str:
    normalized_query = " ".join(query.strip().lower().split())
    if not normalized_query:
        return "query"
    if normalized_query in GREETING_KEYWORDS:
        return "greeting"
    if normalized_query in FAREWELL_KEYWORDS:
        return "farewell"
    if normalized_query in GRATITUDE_KEYWORDS:
        return "gratitude"
    return "query"


def get_intent_response(intent: str) -> Optional[str]:
    if intent == "greeting":
        return "Hi! How can I help you today?"
    if intent == "farewell":
        return "Goodbye! Happy coding!"
    if intent == "gratitude":
        return "You're welcome!"
    return None


def safe_generate(
    model: GeminiModelClient,
    context: str,
    query: str,
    chat_history: List[dict],
    relevance: dict,
) -> str:
    prompt = build_prompt(context, query)
    print("=== QUERY ===", query)
    print("=== CONTEXT LENGTH ===", len(context))
    answer = generate_answer(model, prompt)
    response_parts: List[str] = []
    if relevance.get("fallback_message"):
        response_parts.append(relevance["fallback_message"])
    if relevance.get("warning"):
        response_parts.append(relevance["warning"])
    response_parts.append(answer)
    return "\n".join(part for part in response_parts if part)


def generate_quiz(answer_text: str, query: str, count: int = 2) -> str:
    normalized_answer = answer_text.strip().lower()
    if normalized_answer == "i don't know" or len(answer_text.strip()) <= 50:
        return ""

    topic = answer_text.split(".")[0].strip() or query.strip()
    return f"""
Quiz:
1. What is the main concept described above?
A) Incorrect concept
B) {topic}
C) Unrelated idea
D) None
Correct Answer: B
""".strip()


def print_sources(sources: List[dict]) -> None:
    print("\nSources:")
    for s in sources:
        print(f"[{s['rank']}] {s['title']} -> {s['url']}")


def chat_loop() -> None:
    configure_logging()
    service = ChatService()
    chat_history: list[dict] = []

    print("\nRAG Chatbot Ready! (type 'exit' to quit)\n")
    while True:
        query = input("You: ").strip()
        if not query:
            continue
        if query.lower() == "exit":
            print("Goodbye!")
            break

        greeting_response = check_greeting(query)
        if greeting_response:
            print("Bot:", greeting_response)
            print("\n" + "-" * 60 + "\n")
            continue

        intent = classify_intent(query)
        intent_response = get_intent_response(intent)
        if intent_response:
            print("Bot:", intent_response)
            print("\n" + "-" * 60 + "\n")
            if intent == "farewell":
                break
            continue

        result = service.answer(query, chat_history)
        chat_history.append({"user": query, "bot": result["answer"]})
        chat_history = chat_history[-MAX_CHAT_HISTORY:]

        print("Bot:", result["answer"])
        print_sources(result["sources"])
        print("\n" + "-" * 60 + "\n")


if __name__ == "__main__":
    chat_loop()
