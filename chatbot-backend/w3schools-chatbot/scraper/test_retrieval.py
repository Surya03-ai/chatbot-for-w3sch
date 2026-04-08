import chromadb
from sentence_transformers import SentenceTransformer

def test_retrieval(query: str, n_results: int = 3, db_path: str = "scraper/chroma_db"):
    """
    Test retrieval by querying the vector database and displaying results.
    
    Args:
        query: Search query text
        n_results: Number of results to return (default: 3)
        db_path: Path to the ChromaDB database
    """
    print("=" * 80)
    print(f"Query: {query}")
    print("=" * 80)
    
    # Load the model (same as used in embeddings.py)
    print("\n[1] Loading sentence-transformers model...")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    
    # Generate embedding for the query
    print("[2] Generating embedding for query...")
    query_embedding = model.encode(query, convert_to_tensor=False).tolist()
    print(f"    ✓ Query embedding generated (384 dimensions)")
    
    # Connect to ChromaDB
    print("[3] Connecting to ChromaDB...")
    client = chromadb.PersistentClient(path=db_path)
    collection = client.get_collection(name="w3chunks")
    print(f"    ✓ Connected to collection 'w3chunks' ({collection.count()} documents)")
    
    # Query the vector database
    print(f"[4] Searching for top {n_results} similar documents...")
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        include=["documents", "distances", "metadatas"]
    )
    
    # Display results
    print(f"\n{'RESULTS':^80}")
    print("-" * 80)
    
    if not results["documents"] or len(results["documents"][0]) == 0:
        print("No results found!")
        return
    
    for i, (doc, distance, metadata) in enumerate(
        zip(results["documents"][0], 
            results["distances"][0], 
            results["metadatas"][0])
    ):
        # Convert distance to similarity score (0-1)
        similarity = 1 - distance
        
        # Print result header
        print(f"\n[Result {i + 1}] Similarity: {similarity:.3f}")
        print("-" * 80)
        
        # Print document content (truncate if too long)
        content = doc
        if len(content) > 300:
            content = content[:300] + "..."
        print(f"Content:\n{content}")
        
        # Print metadata
        print(f"\nMetadata: {metadata}")
    
    print("\n" + "=" * 80)


def interactive_test(db_path: str = "scraper/chroma_db"):
    """
    Interactive testing mode - accept multiple queries.
    
    Args:
        db_path: Path to the ChromaDB database
    """
    print("\n" + "=" * 80)
    print("RAG Retrieval Test - Interactive Mode")
    print("=" * 80)
    print("Enter search queries to test retrieval. Type 'exit' to quit.\n")
    
    while True:
        query = input("Enter query: ").strip()
        
        if query.lower() == "exit":
            print("Exiting...")
            break
        
        if not query:
            print("Query cannot be empty!")
            continue
        
        test_retrieval(query, n_results=3, db_path=db_path)
        print()


if __name__ == "__main__":
    # Example queries to test
    test_queries = [
        "CSS colors and styling",
        "HTML forms and input elements",
        "JavaScript array methods"
    ]
    
    print("\n" + "=" * 80)
    print("RAG RETRIEVAL TEST")
    print("=" * 80)
    
    # Run test queries
    for query in test_queries:
        test_retrieval(query, n_results=3)
        print("\n")
    
    # Start interactive mode
    print("\n" + "=" * 80)
    print("Starting interactive mode...")
    print("=" * 80)
    interactive_test()
