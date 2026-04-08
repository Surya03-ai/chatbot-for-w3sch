from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.chat_service import ChatService


def main() -> None:
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

        result = service.answer(query, chat_history)
        print("Bot:", result["answer"])
        chat_history.append({"user": query, "bot": result["answer"]})
        chat_history = chat_history[-5:]
        print("\n" + "-" * 60 + "\n")


if __name__ == "__main__":
    main()
