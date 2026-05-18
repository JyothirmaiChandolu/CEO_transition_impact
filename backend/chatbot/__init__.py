"""
Title: CEO performance analysis
Author: Jyothirmai Chandolu
Employee_id: 800342

CEO Transition Analysis RAG Chatbot

A Retrieval-Augmented Generation (RAG) chatbot powered by LangChain and OpenAI.
Answers questions about CEO transitions, stock performance, and financial analysis
grounded in real S&P 100 company data (1996-2025).
"""

from .rag_pipeline import RAGPipeline
from .context_builder import ContextBuilder

__all__ = ["RAGPipeline", "ContextBuilder"]
