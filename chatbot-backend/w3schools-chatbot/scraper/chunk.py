from datetime import datetime

from langchain_text_splitters import RecursiveCharacterTextSplitter

from scraper.utils import count_tokens

CHUNK_SIZE = 512
CHUNK_OVERLAP = 50


def configure(chunk_size: int, chunk_overlap: int):
    """Set chunking parameters from the main configuration."""
    global CHUNK_SIZE, CHUNK_OVERLAP
    CHUNK_SIZE = chunk_size
    CHUNK_OVERLAP = chunk_overlap


def chunk_text(page: dict, topic: str) -> list[dict]:
    """Split a cleaned page into token-aware chunks for embedding.
    
    Each page dict must contain: url, topic, title, text, scraped_at
    The scraped_at timestamp is included in chunk metadata.
    """
    if not page:
        return []
    text = page.get("text", "")
    if not text:
        return []
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=count_tokens,
    )
    pieces = splitter.split_text(text)
    # Use scraped_at from the page, or generate if missing
    scraped_at = page.get("scraped_at") or (datetime.utcnow().replace(microsecond=0).isoformat() + "Z")
    chunks = []
    chunk_index = 0
    for piece in pieces:
        token_count = count_tokens(piece)
        if token_count < 30:
            continue
        chunk = {
            "text": piece,
            "metadata": {
                "source_url": page.get("url", ""),
                "topic": topic,
                "page_title": page.get("title", ""),
                "chunk_index": chunk_index,
                "token_count": token_count,
                "char_count": len(piece),
                "scraped_at": scraped_at,
            },
        }
        chunks.append(chunk)
        chunk_index += 1
    return chunks
