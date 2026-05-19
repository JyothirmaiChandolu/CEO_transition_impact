"""
__Title__      : CEO performance analysis
__Author__     : Jyothirmai Chandolu
__Employee_id__: 800342
__Version__    : 1
__Description__: Orchestrates all RAG pipeline steps (load, chunk, embed, store, retrieve, generate) into a single callable class.
"""

from .step1_load_documents import load_documents
from .step2_chunk_documents import chunk_documents
from .step3_create_embeddings import get_embedding_model
from .step4_store_chromadb import store_in_chromadb, load_chromadb
from .step5_retrieve_chunks import retrieve_chunks
from .step6_generate_answer import generate_answer
from .context_builder import ContextBuilder
from pathlib import Path


class RAGPipeline:
    """
    Complete RAG pipeline for CEO analysis chatbot.

    Steps:
    1. Load knowledge base documents (.md files)
    2. Chunk documents into manageable pieces
    3. Create embeddings using OpenAI
    4. Store in ChromaDB vector store
    5. Retrieve relevant chunks for query
    6. Generate answer using GPT-4o-mini with context
    """

    def __init__(self, kb_dir: str = None, data_dir: str = "data", reset: bool = False):
        """
        Initialize RAG pipeline.

        Args:
            kb_dir: Path to knowledge base directory
            data_dir: Path to data directory (companies.json, KPIs, etc.)
            reset: If True, rebuild ChromaDB from scratch

        Behavior:
        - Loads knowledge base documents
        - Creates embeddings and vector store (or loads existing)
        - Initializes context builder with company data
        """
        print("=" * 60)
        print("Initializing RAG Pipeline")
        print("=" * 60)

        self.data_dir = data_dir
        self.kb_dir = kb_dir

        # Step 1-3: Load documents, chunk, create embeddings
        print("\n[Step 1-3] Loading and processing documents...")
        documents = load_documents(kb_dir)
        chunks = chunk_documents(documents)
        embeddings = get_embedding_model()

        # Step 4: Create or load ChromaDB
        print("\n[Step 4] Setting up ChromaDB vector store...")
        from .step4_store_chromadb import reset_chromadb

        if reset:
            reset_chromadb()

        # Check if ChromaDB already exists
        chroma_db_path = Path(__file__).parent / "chroma_db"
        if chroma_db_path.exists():
            print("  Loading existing ChromaDB...")
            self.vectorstore = load_chromadb(embeddings)
        else:
            print("  Creating new ChromaDB...")
            self.vectorstore = store_in_chromadb(chunks, embeddings)

        # Initialize context builder
        print("\n[Setup] Initializing context builder...")
        self.context_builder = ContextBuilder(data_dir)

        print("\n" + "=" * 60)
        print("✓ RAG Pipeline Ready!")
        print("=" * 60 + "\n")

    def answer(self, query: str, ticker: str = None, sector: str = None, transition_date: str = None, chat_history: list = None) -> str:
        """
        Answer a user query using the RAG pipeline.

        Args:
            query: User question
            ticker: Optional company ticker for company-specific context
            sector: Optional sector for sector-specific context
            transition_date: Optional transition date for specific analysis
            chat_history: List of prior messages [{role, content}]

        Returns:
            String answer from the LLM
        """
        print(f"User Query: '{query}'")

        # Step 5: Retrieve relevant chunks
        print("  [Step 5] Retrieving relevant chunks...")
        kb_chunks = retrieve_chunks(self.vectorstore, query, top_k=4)

        # Build data context
        print("  [Context] Building data context...")
        if ticker:
            data_context = self.context_builder.build_company_context(ticker, transition_date)
        elif sector:
            data_context = self.context_builder.build_sector_context(sector)
        else:
            data_context = self.context_builder.build_general_context()

        # Step 6: Generate answer
        print("  [Step 6] Generating answer...")
        answer = generate_answer(query, kb_chunks, data_context, chat_history=chat_history)

        print(f"  [Done]\n")

        return answer

    def batch_test(self, test_queries: list = None) -> None:
        """
        Test pipeline with multiple queries.

        Args:
            test_queries: List of dicts with keys: query, ticker (optional), sector (optional)
        """
        if test_queries is None:
            test_queries = [
                {"query": "What is the Sharpe ratio?"},
                {"query": "How is CEO impact calculated?", "ticker": "AAPL"},
                {"query": "What are outliers in CEO analysis?"},
                {"query": "Tell me about Technology sector CEOs", "sector": "Technology"},
            ]

        print("\n" + "=" * 60)
        print("Running Batch Tests")
        print("=" * 60)

        for i, test in enumerate(test_queries):
            query = test.get("query")
            ticker = test.get("ticker")
            sector = test.get("sector")

            print(f"\n[Test {i+1}] Query: {query}")
            if ticker:
                print(f"         Ticker: {ticker}")
            if sector:
                print(f"         Sector: {sector}")

            answer = self.answer(query, ticker=ticker, sector=sector)
            print(f"\nAnswer:\n{answer}\n")


if __name__ == "__main__":
    # Initialize pipeline
    pipeline = RAGPipeline()

    # Run batch tests
    pipeline.batch_test()
