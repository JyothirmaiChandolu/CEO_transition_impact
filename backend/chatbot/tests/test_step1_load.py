"""
Title: CEO performance analysis
Author: Jyothirmai Chandolu
Employee_id: 800342

Test Step 1: Load Documents
Tests that knowledge base documents are loaded correctly.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from step1_load_documents import load_documents


def test_documents_loaded():
    """Test that documents are loaded."""
    documents = load_documents()
    assert len(documents) > 0, "No documents loaded"
    print(f"✓ Loaded {len(documents)} documents")


def test_documents_have_content():
    """Test that each document has non-empty content."""
    documents = load_documents()
    for doc in documents:
        assert doc.page_content, f"Document has empty content"
        assert len(doc.page_content) > 0, "Document content is empty"
    print(f"✓ All documents have non-empty content")


def test_documents_have_metadata():
    """Test that documents have source metadata."""
    documents = load_documents()
    for doc in documents:
        assert 'source' in doc.metadata, "Document missing 'source' metadata"
        assert doc.metadata['source'], "Source metadata is empty"
    print(f"✓ All documents have source metadata")


def test_document_count():
    """Test that expected number of documents are loaded."""
    documents = load_documents()
    # We expect 4 markdown files: financial_terms, calculations, outlier_methodology, ceo_analysis
    assert len(documents) == 4, f"Expected 4 documents, got {len(documents)}"
    print(f"✓ Correct number of documents (4)")


if __name__ == "__main__":
    print("Running Step 1 Tests...\n")

    try:
        test_documents_loaded()
        test_documents_have_content()
        test_documents_have_metadata()
        test_document_count()

        print("\n✓ All Step 1 tests passed!")
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
