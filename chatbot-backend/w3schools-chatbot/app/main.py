from __future__ import annotations

from fastapi import FastAPI

from app.api.chat import router as chat_router

app = FastAPI(title="W3Schools RAG Chatbot")
app.include_router(chat_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
