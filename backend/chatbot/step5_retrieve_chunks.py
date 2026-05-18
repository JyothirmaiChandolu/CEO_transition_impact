"""
Title: CEO performance analysis
Author: Jyothirmai Chandolu
Employee_id: 800342

Step 5: Retrieve Relevant Chunks
Uses semantic similarity search to find relevant knowledge base chunks for a query.
"""


def retrieve_chunks(vectorstore, query: str, top_k: int = 4) -> list:
    """
    Retrieve top-k most relevant chunks for a query.

    Args:
        vectorstore: ChromaDB Chroma object from step4
        query: User query string
        top_k: Number of top results to return (default 4)

    Returns:
        List of relevant chunk strings (page_content)

    Details:
        - Uses cosine similarity on embeddings
        - Finds chunks semantically similar to query
        - Returns most relevant chunks to use in LLM prompt
    """
    print(f"Retrieving top {top_k} relevant chunks for query: '{query}'")

    # Perform similarity search on the vectorstore
    results = vectorstore.similarity_search(query, k=top_k)

    # Extract just the text content (ignore metadata for now)
    chunks = [doc.page_content for doc in results]

    print(f"✓ Retrieved {len(chunks)} chunks")

    return chunks


def retrieve_chunks_with_scores(vectorstore, query: str, top_k: int = 4) -> list:
    """
    Retrieve top-k chunks with similarity scores.

    Args:
        vectorstore: ChromaDB Chroma object
        query: User query string
        top_k: Number of top results

    Returns:
        List of tuples: [(chunk_text, similarity_score), ...]

    Details:
        - Similarity score ranges from 0 to 1
        - Higher score = more relevant
        - Useful for debugging/understanding relevance
    """
    print(f"Retrieving chunks with scores for: '{query}'")

    results = vectorstore.similarity_search_with_scores(query, k=top_k)

    # Format as list of (content, score) tuples
    chunks_with_scores = [(doc.page_content, score) for doc, score in results]

    print(f"✓ Retrieved {len(chunks_with_scores)} chunks with scores")
    for i, (chunk, score) in enumerate(chunks_with_scores):
        print(f"  Chunk {i+1} (score: {score:.4f}): {chunk[:50]}...")

    return chunks_with_scores


if __name__ == "__main__":
    # Test the retriever
    from step3_create_embeddings import get_embedding_model
    from step4_store_chromadb import load_chromadb

    # Load ChromaDB
    embeddings = get_embedding_model()
    vectorstore = load_chromadb(embeddings)

    # Test query
    test_queries = [
        "What is Sharpe ratio?",
        "How is CEO impact calculated?",
        "What are outliers?",
        "What CEO transitions are tracked?"
    ]

    print("\n=== Testing Retrieval ===\n")

    for query in test_queries:
        print(f"\nQuery: '{query}'")
        chunks_with_scores = retrieve_chunks_with_scores(vectorstore, query, top_k=2)
        print()
