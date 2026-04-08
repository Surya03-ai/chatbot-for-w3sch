import json
import chromadb
from sentence_transformers import SentenceTransformer

# Configuration
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
DB_PATH = "scraper/chroma_db"
COLLECTION_NAME = "w3chunks"
CHUNKS_FILE = "scraper/chunks.json"


def load_chunks_from_json(chunks_file: str) -> list[dict]:
    """
    Load chunks from JSON file and format them for ChromaDB.
    
    Args:
        chunks_file: Path to the chunks.json file
        
    Returns:
        List of formatted chunks with id and content
    """
    print(f"Loading chunks from {chunks_file}...")
    
    with open(chunks_file, "r", encoding="utf-8") as f:
        raw_chunks = json.load(f)
    
    print(f"Found {len(raw_chunks)} raw chunks")
    
    # Format chunks for ChromaDB
    formatted_chunks = []
    seen_ids = set()  # Track used IDs to ensure uniqueness
    
    for i, chunk in enumerate(raw_chunks):
        # Create unique ID using multiple components
        page_title = chunk.get("metadata", {}).get("page_title", "unknown")
        chunk_index = chunk.get("metadata", {}).get("chunk_index", i)
        source_url = chunk.get("metadata", {}).get("source_url", "")
        
        # Extract page name from URL
        if source_url:
            page_name = source_url.split("/")[-1].replace(".asp", "").replace(".html", "")
        else:
            page_name = "unknown"
        
        # Create base ID
        base_id = f"{page_name}_{chunk_index}"
        
        # Ensure uniqueness by adding counter if needed
        chunk_id = base_id
        counter = 1
        while chunk_id in seen_ids:
            chunk_id = f"{base_id}_{counter}"
            counter += 1
        
        seen_ids.add(chunk_id)
        
        # Use the text field as content
        content = chunk.get("text", "").strip()
        
        if not content:
            print(f"Warning: Chunk {i} has no content, skipping...")
            continue
        
        formatted_chunks.append({
            "id": chunk_id,
            "content": content,
            "metadata": chunk.get("metadata", {})
        })
    
    print(f"Successfully formatted {len(formatted_chunks)} chunks with unique IDs")
    return formatted_chunks


def generate_embeddings(chunks: list[dict], model) -> list[list[float]]:
    """
    Generate embeddings for all chunks.
    
    Args:
        chunks: List of chunk dictionaries
        model: Sentence-transformers model
        
    Returns:
        List of embedding vectors
    """
    print("Generating embeddings...")
    
    contents = [chunk["content"] for chunk in chunks]
    embeddings = model.encode(contents, convert_to_tensor=False).tolist()
    
    print(f"Generated {len(embeddings)} embeddings")
    return embeddings


def store_in_chromadb(chunks: list[dict], embeddings: list[list[float]]):
    """
    Store chunks and embeddings in ChromaDB, replacing any existing data.
    
    Args:
        chunks: List of chunk dictionaries
        embeddings: List of embedding vectors
    """
    print("Connecting to ChromaDB...")
    
    # Use PersistentClient to save data to disk
    client = chromadb.PersistentClient(path=DB_PATH)
    
    # Delete existing collection if it exists
    try:
        client.delete_collection(name=COLLECTION_NAME)
        print(f"Deleted existing collection '{COLLECTION_NAME}'")
    except:
        print(f"No existing collection '{COLLECTION_NAME}' found")
    
    # Create new collection
    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}  # Use cosine similarity
    )
    
    print(f"Created new collection '{COLLECTION_NAME}'")
    
    # Prepare data for insertion
    ids = [chunk["id"] for chunk in chunks]
    documents = [chunk["content"] for chunk in chunks]
    metadatas = []
    
    for chunk in chunks:
        metadata = chunk.get("metadata", {})
        # Add source info
        metadata["source"] = "w3schools"
        metadatas.append(metadata)
    
    # Insert data in batches to avoid memory issues
    batch_size = 100
    total_chunks = len(chunks)
    
    for i in range(0, total_chunks, batch_size):
        end_idx = min(i + batch_size, total_chunks)
        batch_ids = ids[i:end_idx]
        batch_documents = documents[i:end_idx]
        batch_embeddings = embeddings[i:end_idx]
        batch_metadatas = metadatas[i:end_idx]
        
        collection.add(
            ids=batch_ids,
            documents=batch_documents,
            embeddings=batch_embeddings,
            metadatas=batch_metadatas
        )
        
        print(f"Inserted batch {i//batch_size + 1}: chunks {i+1}-{end_idx}")
    
    print(f"\n✓ Successfully stored {total_chunks} chunks in ChromaDB")
    print(f"Collection info: {collection.count()} documents stored")


def main():
    """Main function to load real data and store in ChromaDB."""
    print("=" * 80)
    print("LOADING REAL SCRAPED DATA INTO CHROMADB")
    print("=" * 80)
    
    # Step 1: Load the embedding model
    print("\n[Step 1] Loading embedding model...")
    model = SentenceTransformer(EMBEDDING_MODEL)
    print("✓ Model loaded")
    
    # Step 2: Load chunks from JSON
    print("\n[Step 2] Loading chunks from JSON...")
    chunks = load_chunks_from_json(CHUNKS_FILE)
    
    if not chunks:
        print("❌ No chunks found in JSON file!")
        return
    
    # Step 3: Generate embeddings
    print("\n[Step 3] Generating embeddings...")
    embeddings = generate_embeddings(chunks, model)
    
    # Step 4: Store in ChromaDB
    print("\n[Step 4] Storing in ChromaDB...")
    store_in_chromadb(chunks, embeddings)
    
    print("\n" + "=" * 80)
    print("✓ REAL DATA SUCCESSFULLY LOADED!")
    print("Your RAG chatbot now has real scraped content.")
    print("=" * 80)
    
    # Show sample
    print("\nSample chunk:")
    if chunks:
        sample = chunks[0]
        print(f"ID: {sample['id']}")
        print(f"Content: {sample['content'][:200]}...")
        print(f"Source: {sample['metadata'].get('source_url', 'N/A')}")


if __name__ == "__main__":
    main()
