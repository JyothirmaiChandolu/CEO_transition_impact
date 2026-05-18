"""
__Title__      : CEO performance analysis
__Author__     : Jyothirmai Chandolu
__Employee_id__: 800342
__Version__    : 1
__Description__: Loads all markdown files from the knowledge_base/ folder using LangChain's DirectoryLoader.
"""

from pathlib import Path
from langchain_community.document_loaders import DirectoryLoader, TextLoader


def load_documents(kb_dir: str = None) -> list:
    """
    Load all markdown files from knowledge_base folder.

    Args:
        kb_dir: Path to knowledge base directory. If None, uses chatbot/knowledge_base/

    Returns:
        List of LangChain Document objects with page_content and metadata
    """
    if kb_dir is None:
        current_dir = Path(__file__).parent
        kb_dir = str(current_dir / "knowledge_base")

    print(f"Loading documents from: {kb_dir}")

    # TextLoader reads plain text — works for .md without any extra dependencies
    loader = DirectoryLoader(
        path=kb_dir,
        glob="**/*.md",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
        recursive=True,
        silent_errors=True,
    )

    documents = loader.load()

    print(f"✓ Loaded {len(documents)} documents")
    for doc in documents:
        source = doc.metadata.get('source', 'unknown')
        content_length = len(doc.page_content)
        print(f"  - {source} ({content_length} chars)")

    return documents


if __name__ == "__main__":
    # Test the loader
    docs = load_documents()
    print(f"\n{len(docs)} documents loaded successfully")

    # Print summary
    for doc in docs:
        print(f"\nSource: {doc.metadata.get('source')}")
        print(f"Content preview: {doc.page_content[:200]}...")
