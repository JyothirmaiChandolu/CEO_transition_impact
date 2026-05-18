"""
__Title__      : CEO performance analysis
__Author__     : Jyothirmai Chandolu
__Employee_id__: 800342
__Version__    : 1
__Description__: Generates grounded answers using OpenAI GPT-4o-mini based on retrieved chunks and company data context.
"""

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
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


def generate_answer(query: str, kb_chunks: list, data_context: str) -> str:
    """
    Generate an answer using OpenAI ChatGPT grounded in knowledge base and data.

    Args:
        query: User question
        kb_chunks: List of relevant knowledge base chunks from step5
        data_context: Structured company/KPI data context from context_builder

    Returns:
        String answer from the LLM

    Details:
        - System prompt includes knowledge base + data context
        - Uses gpt-4o-mini for cost-effectiveness
        - Temperature 0.3 for deterministic, factual answers
        - Max tokens 500 to keep answers concise
    """
    # Check for API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")

    print(f"Generating answer for: '{query}'")

    # Initialize ChatOpenAI
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.3,  # Low temp for factual, consistent answers
        max_tokens=500,
        api_key=api_key
    )

    # Build system prompt with knowledge base and data context
    kb_text = "\n\n".join(kb_chunks)

    system_prompt = f"""You are an AI assistant for the CEO Performance Analysis website. Your main role is to help users understand and navigate the platform by explaining CEO transitions, stock performance metrics, financial terminology, outlier analysis, and other features visible on the website. You specialize in S&P 100 companies using verified data from 1996-2025.

=== KNOWLEDGE BASE ===
{kb_text}

=== DATA CONTEXT ===
{data_context}

=== CRITICAL RULES (FOLLOW STRICTLY) ===

0. WEBSITE ASSISTANCE:
   - Primary role: Help users understand and navigate the CEO Performance Analysis website
   - Explain features, metrics, and analysis visible on the platform
   - Answer questions about what users see on screen
   - Guide users through company selection, transitions, and analysis features
   - Explain terminology found in the UI (charts, tabs, metrics, buttons)

1. CONTEXT PRIORITY:
   - Always answer about selected transition in DATA CONTEXT if provided
   - Never contradict context with general knowledge
   - Use metrics directly from DATA CONTEXT only - don't generate new ones

2. CONVERSATION HANDLING:
   - Greetings (Hi, Hello, Good morning): Respond warmly, mention role ONLY in first response
   - Apologies (Sorry, My bad): "No problem! What can I help?" (short, move forward)
   - Thank you: "You're welcome! What else?" (short, no identity repeat)
   - Identity (Who are you?): "I'm a CEO performance analyst" (1-2 sentences, no repeat)
   - Analysis: Direct answer, no greeting/identity unless asked

3. DATA ACCURACY & CONSTRAINTS:
   - Use specific numbers from DATA CONTEXT only - never hallucinate metrics
   - If company not in context, ask user to select it first
   - If information unavailable, say so clearly
   - Cite metric sources when referencing data

4. FORMULA & TECHNICAL EXPLANATIONS:
   - NEVER use raw LaTeX notation (avoid \[, \], \frac, etc.)
   - Use simple text format: "1-year impact = (price_day_365 - price_transition) / price_transition × 100"
   - ALWAYS include a practical example with real numbers
   - Example: "If stock was $100 at transition and $125 after 1 year: impact = (125-100)/100 × 100 = +25%"
   - Break down complex formulas into simple steps
   - Emphasize what the formula measures, not the math notation

5. ANALYSIS SCOPE:
   - Answer about: CEO transitions, stock performance, KPIs, volatility, Sharpe ratio, drawdown, outliers, sector analysis, economic cycles, recessions, expansions, financial terminology
   - Keep answers: 1 line for greetings, 3-5 sentences for analysis

7. OUT OF SCOPE:
   - Completely unrelated topics (sports, politics, personal advice): "I can only assist with CEO performance analysis and financial/economic terminology"
   - System/technical questions (architecture, code, etc.): "I am not intended to provide this information"
   - NOTE: Recession, adjusted close, economic cycles, and all financial terms ARE in scope"""

    # Create messages
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=query)
    ]

    # Call OpenAI
    print("  Calling OpenAI GPT-4o-mini...")
    response = llm.invoke(messages)

    answer = response.content

    print(f"✓ Answer generated ({len(answer)} chars)")

    return answer


if __name__ == "__main__":
    # Test the answer generation
    from step3_create_embeddings import get_embedding_model
    from step4_store_chromadb import load_chromadb
    from step5_retrieve_chunks import retrieve_chunks

    # Load ChromaDB
    embeddings = get_embedding_model()
    vectorstore = load_chromadb(embeddings)

    # Test queries
    test_cases = [
        {
            "query": "What is Sharpe ratio?",
            "data_context": "General knowledge base query"
        },
        {
            "query": "How did AAPL stock perform after Tim Cook became CEO?",
            "data_context": "Company: Apple Inc. (AAPL), Sector: Technology\nTransition date: 2011-08-24\nCEO: Tim Cook\n90-day impact: +18.4%\n1-year impact: +45.2%"
        }
    ]

    print("\n=== Testing Answer Generation ===\n")

    for i, test in enumerate(test_cases):
        query = test["query"]
        data_context = test["data_context"]

        print(f"\n--- Test {i+1} ---")
        print(f"Query: {query}\n")

        # Retrieve relevant chunks
        chunks = retrieve_chunks(vectorstore, query, top_k=3)

        # Generate answer
        answer = generate_answer(query, chunks, data_context)

        print(f"Answer:\n{answer}\n")