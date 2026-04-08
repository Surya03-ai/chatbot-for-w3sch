import chromadb
from sentence_transformers import SentenceTransformer

# Configuration
MODEL_NAME = "all-MiniLM-L6-v2"
DB_PATH = "scraper/chroma_db"
COLLECTION_NAME = "w3chunks"
TOP_K = 3  # Retrieve top 3 documents


def retrieve_context(query: str) -> tuple[str, list[dict]]:
    """
    Phase 3: Retrieve context from vector database for a given query.
    
    Steps:
    1. Convert query into embedding using sentence-transformers
    2. Query ChromaDB collection for top 3 similar documents
    3. Combine retrieved documents into a context string
    
    Args:
        query: User query string
        
    Returns:
        Tuple of (context_string, retrieved_docs_list)
    """
    # Step 1: Load the embedding model
    print("[1] Loading embedding model...")
    model = SentenceTransformer(MODEL_NAME)
    
    # Step 2: Convert query to embedding
    print("[2] Converting query to embedding...")
    query_embedding = model.encode(query, convert_to_tensor=False).tolist()
    
    # Step 3: Connect to ChromaDB
    print("[3] Connecting to ChromaDB...")
    client = chromadb.PersistentClient(path=DB_PATH)
    collection = client.get_collection(name=COLLECTION_NAME)
    print(f"    ✓ Collection '{COLLECTION_NAME}' loaded ({collection.count()} documents)")
    
    # Step 4: Query the vector database
    print(f"[4] Searching for top {TOP_K} similar documents...")
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=TOP_K,
        include=["documents", "distances"]
    )
    
    # Step 5: Extract and format results
    retrieved_docs = []
    context_parts = []
    
    if results["documents"] and len(results["documents"][0]) > 0:
        for i, (doc, distance) in enumerate(
            zip(results["documents"][0], results["distances"][0]), 1
        ):
            similarity = 1 - distance
            retrieved_docs.append({
                "rank": i,
                "content": doc,
                "similarity": similarity
            })
            # Add to context with separator
            context_parts.append(f"[Document {i}]\n{doc}")
    
    # Combine all retrieved documents into single context string
    context = "\n\n".join(context_parts)
    
    return context, retrieved_docs


def display_retrieval(query: str, context: str, retrieved_docs: list[dict]):
    """
    Display retrieval results in a clean, readable format.
    
    Args:
        query: The input query
        context: Combined context from retrieved documents
        retrieved_docs: List of retrieved document objects
    """
    print("\n" + "=" * 80)
    print("RETRIEVAL RESULTS")
    print("=" * 80)
    
    print(f"\nQuery: {query}")
    print("\n" + "-" * 80)
    print("RETRIEVED CONTEXT:")
    print("-" * 80)
    print(context)
    
    print("\n" + "-" * 80)
    print("RETRIEVAL SUMMARY:")
    print("-" * 80)
    for doc in retrieved_docs:
        print(f"  • Document {doc['rank']}: Similarity {doc['similarity']:.3f}")
    
    print("\n" + "=" * 80)


def main():
    """Main function: accept user input and retrieve context."""
    print("\n" + "=" * 80)
    print("RAG CHATBOT - PHASE 3: RETRIEVAL")
    print("=" * 80)
    print("\nThis is Phase 3 of the RAG system:")
    print("  1. Accept user query")
    print("  2. Convert to embedding")
    print("  3. Retrieve top 3 documents from ChromaDB")
    print("  4. Display retrieved context\n")
    
    # Example queries
    example_queries = [
        "What is HTML?",
        "How do I use CSS for styling?",
        "Explain JavaScript arrays"
    ]
    
    print("Running with example queries...\n")
    
    for query in example_queries:
        print("\n" + "=" * 80)
        print(f"Processing query: {query}")
        print("=" * 80)
        
        try:
            # Retrieve context
            context, retrieved_docs = retrieve_context(query)
            
            # Display results
            display_retrieval(query, context, retrieved_docs)
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Make sure the ChromaDB collection exists with embeddings stored.")
    
    # Interactive mode
    print("\n" + "=" * 80)
    print("INTERACTIVE MODE")
    print("=" * 80)
    print("Enter your own queries (type 'exit' to quit):\n")
    
    while True:
        user_query = input("Enter query: ").strip()
        
        if user_query.lower() == "exit":
            print("\n✓ Exiting...")
            break
        
        if not user_query:
            print("Query cannot be empty!")
            continue
        
        try:
            context, retrieved_docs = retrieve_context(user_query)
            display_retrieval(user_query, context, retrieved_docs)
            
        except Exception as e:
            print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
