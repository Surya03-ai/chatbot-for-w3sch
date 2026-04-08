from __future__ import annotations

import os
from functools import lru_cache

from app.core.embedding import DEFAULT_MODEL_NAME, embed_query, load_embedding_model
from app.core.generation import GeminiModelClient, configure_gemini, generate_answer
from app.core.guards import check_greeting, check_input, check_relevance
from app.core.prompt import build_prompt
from app.core.retrieval import retrieve_documents
from app.db.chroma import DEFAULT_COLLECTION_NAME, DEFAULT_DB_PATH, get_collection

PREFERRED_GEMINI_MODEL = "gemini-pro"
QUIZ_INTENT_WORDS = ("quiz", "question", "mcq")
TOP_K = 3


@lru_cache(maxsize=1)
def _collect_gemini_models() -> list[str]:
    import google.generativeai as genai

    available_models = list(genai.list_models())
    valid_models: list[str] = []
    for model in available_models:
        model_name = getattr(model, "name", "")
        supported_methods = list(getattr(model, "supported_generation_methods", []) or [])
        if "generateContent" in supported_methods and model_name:
            valid_models.append(model_name.replace("models/", "", 1))
    if PREFERRED_GEMINI_MODEL in valid_models:
        valid_models.remove(PREFERRED_GEMINI_MODEL)
        valid_models.insert(0, PREFERRED_GEMINI_MODEL)
    return valid_models


class ChatService:
    def __init__(
        self,
        db_path: str = DEFAULT_DB_PATH,
        collection_name: str = DEFAULT_COLLECTION_NAME,
        embedding_model_name: str = DEFAULT_MODEL_NAME,
    ) -> None:
        self.db_path = db_path
        self.collection_name = collection_name
        self.embedding_model_name = embedding_model_name
        self.embedding_model = None
        self.collection = None
        self.gemini_model = None

    def _ensure_ready(self) -> None:
        if self.embedding_model is None:
            self.embedding_model = load_embedding_model(self.embedding_model_name)
        if self.collection is None:
            self.collection = get_collection(
                db_path=self.db_path, collection_name=self.collection_name
            )
        if self.gemini_model is None:
            api_key = os.getenv("GEMINI_API_KEY", "")
            self.gemini_model = configure_gemini(api_key, _collect_gemini_models())

    def _needs_quiz(self, query: str) -> bool:
        normalized_query = query.lower()
        return any(word in normalized_query for word in QUIZ_INTENT_WORDS)

    def generate_quiz(self, answer_text: str, query: str, count: int = 2) -> str:
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

    def answer(self, query: str, chat_history: list[dict] | None = None) -> dict:
        chat_history = chat_history or []

        greeting_response = check_greeting(query)
        if greeting_response:
            return {
                "query": query,
                "answer": greeting_response,
                "sources": [],
                "warning": None,
                "mode": "greeting",
            }

        self._ensure_ready()

        input_guard_response = check_input(query)
        if input_guard_response:
            return {
                "query": query,
                "answer": input_guard_response,
                "sources": [],
                "warning": None,
                "mode": "input_guard",
            }

        query_embedding = embed_query(self.embedding_model, query)
        context, sources, distances = retrieve_documents(
            self.collection, query_embedding, top_k=TOP_K
        )
        context = context[:3000]
        relevance = check_relevance(context, distances)
        prompt = build_prompt(context, query)
        print("=== QUERY ===", query)
        print("=== CONTEXT LENGTH ===", len(context))
        try:
            answer = generate_answer(self.gemini_model, prompt)
        except Exception as error:
            print(f"=== MODEL ERROR === {error}")
            answer = "Sorry, I couldn't generate a proper response."

        response_parts = []
        if relevance.get("fallback_message"):
            response_parts.append(relevance["fallback_message"])
        if relevance.get("warning"):
            response_parts.append(relevance["warning"])
        response_parts.append(answer)

        if self._needs_quiz(query):
            if answer.strip().lower() != "i don't know" and len(answer) > 50:
                quiz_text = self.generate_quiz(answer, query)
            else:
                quiz_text = ""
            if quiz_text:
                response_parts.append(quiz_text)

        return {
            "query": query,
            "answer": "\n".join(part for part in response_parts if part),
            "sources": sources,
            "warning": relevance.get("warning"),
            "mode": relevance.get("mode", "strict"),
        }
