from __future__ import annotations

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1)
    chat_history: list[dict] = Field(default_factory=list)


class ChatResponse(BaseModel):
    query: str
    answer: str
    sources: list[dict] = Field(default_factory=list)
    warning: str | None = None
    mode: str = "strict"
