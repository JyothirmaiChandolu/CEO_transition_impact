"""
Title: CEO performance analysis
Author: Jyothirmai Chandolu
Employee_id: 800342

Step 4: Store Chunks in ChromaDB
Persists chunks and embeddings into ChromaDB vector store for semantic search.
"""

from langchain_chroma import Chroma
from pathlib import Path
import shutil


# Use absolute path so it works regardless of working directory
CHROMA_PATH = str(Path(__file__).parent / "chroma_db")


def store_in_chromadb(chunks: list, embedding_model) -> Chroma:
    """
    Store chunks in ChromaDB with embeddings.

    Args:
        chunks: List of LangChain Document objects from step2
        embedding_model: OpenAIEmbeddings object from step3

    Returns:
        Chroma vectorstore object
    """
    print(f"Storing {len(chunks)} chunks in ChromaDB...")
    print(f"  Database path: {CHROMA_PATH}")

    # Create vectorstore from documents
    # This automatically:
    # 1. Creates embeddings for all chunks using the embedding_model
    # 2. Stores embeddings + metadata in ChromaDB
    # 3. Persists to disk at CHROMA_PATH
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embedding_model,
        persist_directory=CHROMA_PATH,
        collection_name="ceo_analysis"
    )

    print(f"✓ ChromaDB vectorstore created and persisted")

    return vectorstore


def load_chromadb(embedding_model) -> Chroma:
    """
    Load existing ChromaDB vectorstore from disk.

    Args:
        embedding_model: OpenAIEmbeddings object from step3

    Returns:
        Chroma vectorstore object
    """
    # Check if database exists
    if not Path(CHROMA_PATH).exists():
        raise FileNotFoundError(f"ChromaDB not found at {CHROMA_PATH}. Run store_in_chromadb first.")

    print(f"Loading ChromaDB from {CHROMA_PATH}...")

    vectorstore = Chroma(
        persist_directory=CHROMA_PATH,
        embedding_function=embedding_model,
        collection_name="ceo_analysis"
    )

    print(f"✓ ChromaDB loaded")

    return vectorstore


def reset_chromadb() -> None:
    """
    Delete ChromaDB directory to start fresh.
    """
    if Path(CHROMA_PATH).exists():
        print(f"Deleting existing ChromaDB at {CHROMA_PATH}...")
        shutil.rmtree(CHROMA_PATH)
        print("✓ ChromaDB deleted")
    else:
        print(f"No ChromaDB found at {CHROMA_PATH}")


if __name__ == "__main__":
    # Test the ChromaDB storage
    from step1_load_documents import load_documents
    from step2_chunk_documents import chunk_documents
    from step3_create_embeddings import get_embedding_model

    # Load and process documents
    docs = load_documents()
    chunks = chunk_documents(docs)
    embeddings = get_embedding_model()

    # Store in ChromaDB
    vectorstore = store_in_chromadb(chunks, embeddings)

    print(f"\n✓ Successfully stored {len(chunks)} chunks in ChromaDB")

    # Test loading
    vectorstore_loaded = load_chromadb(embeddings)
    print("✓ Successfully loaded ChromaDB")
