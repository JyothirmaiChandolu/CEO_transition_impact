"""
__Title__      : CEO performance analysis
__Author__     : Jyothirmai Chandolu
__Employee_id__: 800342
__Version__    : 1
__Description__: Creates vector embeddings for document chunks using OpenAI's text-embedding-3-small model.
"""

from langchain_openai import OpenAIEmbeddings
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    # Try current directory
    load_dotenv()


def get_embedding_model() -> OpenAIEmbeddings:
    """
    Initialize OpenAI embeddings model.

    Returns:
        OpenAIEmbeddings object configured for text-embedding-3-small

    Details:
        - Uses text-embedding-3-small (fast, cheap, good quality)
        - Requires OPENAI_API_KEY environment variable
        - Embeddings are 1536-dimensional vectors
        - Used for semantic similarity search in ChromaDB
    """
    # Check for API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")

    print("Initializing OpenAI embeddings (text-embedding-3-small)...")

    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        api_key=api_key
    )

    print("✓ OpenAI embeddings initialized")

    return embeddings


def test_embedding(embedding_model: OpenAIEmbeddings) -> None:
    """
    Test the embedding model with a sample text.

    Args:
        embedding_model: OpenAIEmbeddings object
    """
    test_text = "What is the Sharpe ratio?"
    print(f"\nTesting embedding with: '{test_text}'")

    embedding = embedding_model.embed_query(test_text)

    print(f"✓ Embedding created: {len(embedding)} dimensions")
    print(f"  First 5 values: {embedding[:5]}")


if __name__ == "__main__":
    # Test the embeddings model
    embeddings = get_embedding_model()
    test_embedding(embeddings)
