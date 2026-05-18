"""
Title: CEO performance analysis
Author: Jyothirmai Chandolu
Employee_id: 800342

Step 2: Split Documents into Chunks
Uses LangChain RecursiveCharacterTextSplitter to break documents into manageable chunks
for embedding and retrieval.
"""

from langchain_text_splitters import RecursiveCharacterTextSplitter


def chunk_documents(documents: list, chunk_size: int = 500, chunk_overlap: int = 50) -> list:
    """
    Split documents into smaller chunks for embedding.

    Args:
        documents: List of LangChain Document objects from step1
        chunk_size: Maximum characters per chunk (default 500)
        chunk_overlap: Characters to overlap between chunks (default 50)

    Returns:
        List of LangChain Document objects (chunks)

    Details:
        - Chunks overlap to preserve context at boundaries
        - RecursiveCharacterTextSplitter breaks on paragraph/sentence/word level
        - Preserves metadata from original documents
    """
    print(f"Chunking documents (size={chunk_size}, overlap={chunk_overlap})...")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""]  # Try to split on smart boundaries
    )

    chunks = splitter.split_documents(documents)

    print(f"✓ Created {len(chunks)} chunks from {len(documents)} documents")

    # Print statistics
    chunk_sizes = [len(chunk.page_content) for chunk in chunks]
    print(f"  - Chunk size range: {min(chunk_sizes)}-{max(chunk_sizes)} chars")
    print(f"  - Average chunk size: {sum(chunk_sizes) // len(chunk_sizes)} chars")

    return chunks


if __name__ == "__main__":
    # Test the chunker
    from step1_load_documents import load_documents

    docs = load_documents()
    chunks = chunk_documents(docs)

    print(f"\n✓ Successfully created {len(chunks)} chunks")

    # Show some chunk examples
    print("\nSample chunks:")
    for i, chunk in enumerate(chunks[:3]):
        source = chunk.metadata.get('source', 'unknown')
        print(f"\nChunk {i+1} (source: {source}):")
        print(f"  {chunk.page_content[:150]}...")
