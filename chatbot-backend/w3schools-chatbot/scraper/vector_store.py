import json

import chromadb

EMBEDDINGS_FILE = "scraper/chunks_with_embeddings.json"
DB_PATH = "scraper/chroma_db"
COLLECTION_NAME = "w3chunks"


def store_embeddings(
    embeddings_file: str = EMBEDDINGS_FILE,
    db_path: str = DB_PATH,
    collection_name: str = COLLECTION_NAME,
):
    """
    Load embeddings from JSON and store them in ChromaDB.
    """
    print(f"Loading embeddings from {embeddings_file}...")
    with open(embeddings_file, "r", encoding="utf-8") as file:
        chunks = json.load(file)

    print("Connecting to ChromaDB...")
    client = chromadb.PersistentClient(path=db_path)
    collection = client.get_or_create_collection(name=collection_name)

    print(f"Inserting {len(chunks)} chunks into collection '{collection_name}'...")

    inserted_count = 0
    for chunk in chunks:
        collection.add(
            ids=[str(chunk["id"])],
            documents=[chunk["text"]],
            embeddings=[chunk["embedding"]],
            metadatas=[chunk["metadata"]],
        )
        inserted_count += 1

    print(f"Total documents inserted: {inserted_count}")
    return collection


if __name__ == "__main__":
    store_embeddings()
