from __future__ import annotations

PROGRAMMING_KEYWORDS = [
    "html",
    "css",
    "javascript",
    "react",
    "hooks",
    "python",
    "sql",
    "web",
    "frontend",
]

PROGRAMMING_INTENT_WORDS = [
    "quiz",
    "question",
    "example",
    "explain",
    "how",
]

GREETING_KEYWORDS = ["hi", "hello", "hey", "hii", "hiii"]

UNRELATED_TOPICS = [
    "cricket",
    "movie",
    "movies",
    "film",
    "films",
    "song",
    "songs",
    "music",
    "sports",
    "football",
    "basketball",
    "tennis",
]


def check_input(query: str) -> str | None:
    normalized_query = query.strip().lower()
    if not normalized_query:
        return None

    if any(keyword in normalized_query for keyword in PROGRAMMING_KEYWORDS):
        return None

    if any(intent_word in normalized_query for intent_word in PROGRAMMING_INTENT_WORDS):
        return None

    if any(topic in normalized_query for topic in UNRELATED_TOPICS):
        return (
            "I can help with web development topics like HTML, CSS, JavaScript, "
            "React, hooks, Python, SQL, and frontend concepts."
        )

    return None


def check_greeting(query: str) -> str | None:
    normalized_query = query.strip().lower()
    if normalized_query in GREETING_KEYWORDS:
        return "Hello! 👋 How can I help you with web development today?"
    return None


def check_relevance(context: str, distances: list[float]) -> dict:
    if not context.strip():
        return {
            "has_relevant_context": False,
            "mode": "fallback",
            "warning": "This answer may be approximate",
            "best_similarity": 0.0,
            "fallback_message": (
                "I couldn't find exact info in W3Schools, but here's a general explanation."
            ),
        }

    best_distance = min(distances) if distances else None
    best_similarity = 0.0 if best_distance is None else max(0.0, 1.0 - best_distance)
    is_low_confidence = (
        best_distance is None
        or best_distance > 0.8
        or best_similarity < 0.2
    )

    return {
        "has_relevant_context": True,
        "mode": "fallback" if is_low_confidence else "strict",
        "warning": "This answer may be approximate" if is_low_confidence else None,
        "best_similarity": best_similarity,
        "fallback_message": (
            "I couldn't find exact info in W3Schools, but here's a general explanation."
            if is_low_confidence
            else None
        ),
    }
