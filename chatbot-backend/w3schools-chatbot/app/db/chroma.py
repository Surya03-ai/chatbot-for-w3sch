from __future__ import annotations

import chromadb

DEFAULT_DB_PATH = "scraper/chroma_db"
DEFAULT_COLLECTION_NAME = "w3chunks"


def get_collection(
    db_path: str = DEFAULT_DB_PATH, collection_name: str = DEFAULT_COLLECTION_NAME
):
    client = chromadb.PersistentClient(path=db_path)
    return client.get_collection(name=collection_name)
