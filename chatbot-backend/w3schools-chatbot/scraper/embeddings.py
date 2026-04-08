import json
from sentence_transformers import SentenceTransformer

def generate_embeddings(chunks_file: str = "scraper/chunks.json") -> list[dict]:
    """
    Load chunks from JSON file and generate embeddings for each.
    
    Args:
        chunks_file: Path to the JSON file containing chunks
        
    Returns:
        List of dictionaries with id, text, metadata, and embedding
    """
    # Load the model (downloads automatically on first use)
    print("Loading sentence-transformers model...")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    
    # Load chunks from JSON file
    print(f"Loading chunks from {chunks_file}...")
    with open(chunks_file, "r", encoding="utf-8") as f:
        chunks = json.load(f)
    
    print(f"Found {len(chunks)} chunks. Generating embeddings...")
    
    # Generate embeddings for each chunk
    results = []
    for i, chunk in enumerate(chunks):
        print(chunk.keys())

        # chunks.json stores the chunk body in the "text" field
        text = chunk.get("text") or chunk.get("content")

        if not text or text.strip() == "":
            print(f"Warning: Chunk {i} has empty text, skipping...")
            continue

        chunk_id = chunk.get("id") or f"chunk_{i}"
        
        # Generate embedding
        embedding = model.encode(text, convert_to_tensor=False).tolist()
        
        # Add to results
        results.append({
            "id": chunk_id,
            "text": text,
            "metadata": chunk.get("metadata", {}),
            "embedding": embedding
        })
        
        # Progress indicator
        if (i + 1) % 10 == 0:
            print(f"Processed {i + 1}/{len(chunks)} chunks...")
    
    print(f"✓ Generated {len(results)} embeddings")
    return results


def save_embeddings(embeddings: list[dict], output_file: str = "scraper/chunks_with_embeddings.json"):
    """
    Save embeddings to a JSON file.
    
    Args:
        embeddings: List of dictionaries with embeddings
        output_file: Path to save the output JSON file
    """
    print(f"Saving embeddings to {output_file}...")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(embeddings, f, indent=2)
    print(f"✓ Embeddings saved")


if __name__ == "__main__":
    # Generate embeddings
    embeddings = generate_embeddings()
    
    # Save to file
    save_embeddings(embeddings)
    
    # Display sample
    if embeddings:
        print("\nSample output:")
        print(json.dumps(embeddings[0], indent=2)[:500] + "...")
