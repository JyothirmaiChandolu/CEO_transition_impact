"""
__Title__      : CEO performance analysis
__Author__     : Jyothirmai Chandolu
__Employee_id__: 800342
__Version__    : 1
__Description__: Package initialization for the RAG chatbot module that answers questions about CEO transitions and stock performance.
"""

from .rag_pipeline import RAGPipeline
from .context_builder import ContextBuilder

__all__ = ["RAGPipeline", "ContextBuilder"]
