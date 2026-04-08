# W3Schools Gemini RAG Chatbot

This project uses:

- `sentence-transformers` for embeddings
- ChromaDB for vector search
- `google-generativeai` for Gemini responses

It loads the existing persistent collection at `./scraper/chroma_db` with the collection name `w3chunks`.

## Setup

Install dependencies:

```powershell
pip install -r requirements.txt
```

Set your Gemini API key:

```powershell
$env:GEMINI_API_KEY = "your_actual_api_key_here"
```

## Run

Start the chatbot:

```powershell
python scraper/rag_chatbot.py
```

## How it works

For each user query, the chatbot:

1. Converts the query to an embedding with `all-MiniLM-L6-v2`
2. Retrieves the top 3 documents from ChromaDB
3. Combines them into a context string
4. Sends the prompt to Gemini
5. Prints the answer

Type `exit` to end the chat loop.

## Prompt

The chatbot uses this prompt:

```text
You are a W3Schools AI assistant.
Answer clearly using only the context below.

Context:
{context}

Question:
{query}

If answer not found, say 'I don't know'.
```

## Notes

- The chatbot only uses Gemini for generation.
- Retrieval uses the existing persistent ChromaDB collection.
- Context and source URLs are logged for every query.
