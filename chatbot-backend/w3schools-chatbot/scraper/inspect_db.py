import chromadb

# Configuration
DB_PATH = "scraper/chroma_db"
COLLECTION_NAME = "w3chunks"


def inspect_collection():
    """
    Inspect the ChromaDB collection to see what data is stored.
    
    Shows:
    - Total number of documents
    - First 5 documents with their IDs and content
    """
    print("=" * 80)
    print("CHROMADB COLLECTION INSPECTOR")
    print("=" * 80 + "\n")
    
    # Connect to ChromaDB
    print(f"Connecting to ChromaDB at '{DB_PATH}'...")
    try:
        client = chromadb.PersistentClient(path=DB_PATH)
        print("✓ Connected to ChromaDB\n")
    except Exception as e:
        print(f"✗ Error connecting to ChromaDB: {e}")
        return
    
    # Get the collection
    print(f"Loading collection '{COLLECTION_NAME}'...")
    try:
        collection = client.get_collection(name=COLLECTION_NAME)
        print("✓ Collection loaded\n")
    except Exception as e:
        print(f"✗ Collection not found: {e}")
        print("\nAvailable collections:")
        try:
            collections = client.list_collections()
            if collections:
                for col in collections:
                    print(f"  - {col.name}")
            else:
                print("  (No collections found)")
        except:
            pass
        return
    
    # Get total count
    total_count = collection.count()
    print("=" * 80)
    print(f"TOTAL DOCUMENTS IN COLLECTION: {total_count}")
    print("=" * 80 + "\n")
    
    if total_count == 0:
        print("⚠️  Collection is EMPTY!")
        print("\nTo populate the collection, run:")
        print("  1. python -m scraper.embeddings")
        print("  2. python -m scraper.vector_store")
        return
    
    # Retrieve all documents
    print(f"Retrieving first 5 documents (out of {total_count})...\n")
    
    results = collection.get(
        limit=5,  # Get first 5
        include=["documents", "metadatas"]  # IDs are always returned, don't include in include list
    )
    
    if not results or not results.get("ids"):
        print("✗ No documents retrieved!")
        return
    
    # Display each document
    for i, (doc_id, content, metadata) in enumerate(
        zip(results["ids"], results["documents"], results.get("metadatas", [{}] * 5)), 1
    ):
        print("-" * 80)
        print(f"Document {i}")
        print("-" * 80)
        print(f"ID: {doc_id}")
        print(f"Content Preview (first 200 characters):")
        print(f"  {content[:200]}...")
        
        if metadata:
            print(f"Metadata: {metadata}")
        print()
    
    print("=" * 80)
    print(f"✓ Successfully retrieved {len(results['ids'])} documents")
    print("=" * 80)


if __name__ == "__main__":
    inspect_collection()
