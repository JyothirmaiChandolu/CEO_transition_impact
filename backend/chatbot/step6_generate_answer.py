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


def generate_answer(
    query: str,
    kb_chunks: list,
    data_context: str,
    chat_history: list = None,
) -> str:
    """
    Generate an answer using OpenAI ChatGPT grounded in knowledge base and data.

    Args:
        query: User question
        kb_chunks: List of relevant knowledge base chunks from step5
        data_context: Structured company/KPI data context from context_builder
        chat_history: List of previous messages [{role: 'user'|'assistant', content: str}]

    Returns:
        String answer from the LLM
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")

    print(f"Generating answer for: '{query}'")

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.3,
        max_tokens=800,
        api_key=api_key
    )

    kb_text = "\n\n".join(kb_chunks)
    history = chat_history or []

    # Build a plain-text summary of the conversation for meta-questions
    history_summary = ""
    if history:
        lines = []
        for i, m in enumerate(history):
            role = "User" if m.get("role") == "user" else "Assistant"
            lines.append(f"  [{i+1}] {role}: {m.get('content', '')[:200]}")
        history_summary = "\n=== CONVERSATION HISTORY ===\n" + "\n".join(lines)

    system_prompt = f"""You are an AI assistant for the CEO Performance Analysis website. \
You help users understand CEO transitions, stock performance metrics, financial terminology, \
outlier analysis, and other platform features. You specialize in S&P 100 companies using \
verified data from 1996-2025.

=== KNOWLEDGE BASE ===
{kb_text}

=== DATA CONTEXT ===
{data_context}
{history_summary}

=== RULES (FOLLOW STRICTLY) ===

1. MEMORY & CONVERSATION AWARENESS:
   - You have access to the full conversation history above.
   - When asked "what was my previous/last question", quote the actual question from history.
   - When asked "what was my first question", quote the first user message from history.
   - When asked "what did we discuss", briefly summarize the topics from history.
   - When user says "it", "that", "there" without naming something, check recent history for context.
   - Maintain context — if discussing Apple and user asks "what about their volatility", they mean Apple.

2. ANSWER FORMAT (MANDATORY for analysis questions):
   - Start with 2-3 sentences giving a short explanation.
   - Then use bullet points (•) for key details, one point per line.
   - End with a short closing sentence.
   - Example format:
     The Sharpe ratio measures risk-adjusted return for a CEO's tenure. It compares excess return to volatility.
     • Formula: (return - risk-free rate) / standard deviation
     • Higher values indicate better risk-adjusted performance
     • A ratio above 1.0 is generally considered good
     This helps compare CEOs across different market conditions fairly.

3. CONTEXT PRIORITY:
   - Always use DATA CONTEXT metrics first — never hallucinate numbers.
   - If a company is not in context, ask the user to select it on the platform first.

4. CONVERSATION HANDLING:
   - Greetings (hi, hello): Respond warmly, offer help with CEO performance analysis.
   - Thank you: "You're welcome! What else can I help with?"
   - Apologies: "No problem! What can I help you with?"
   - Identity (who are you): "I am the CEO Performance Analysis Assistant. How can I help you?"
   - System/architecture questions: "I am not intended to provide this information."

5. FORMULA EXPLANATIONS:
   - NEVER use LaTeX notation (no \\[, \\], \\frac).
   - Use plain text: "impact = (end_price - start_price) / start_price × 100"
   - Always include a practical example with real numbers.

6. OUT OF SCOPE:
   - Unrelated topics (sports, politics, personal advice): "I can only assist with CEO performance analysis and financial terminology."
   - Non-financial/non-CEO topics: Politely decline and redirect.
   - NOTE: Recessions, economic cycles, financial terms, stock metrics ARE all in scope.

7. SHORT RESPONSES (do NOT use bullet format):
   - Greetings, thank-you, apologies, identity questions → 1-2 sentences max."""

    # Build message list: system → history → current query
    from langchain_core.messages import AIMessage
    messages = [SystemMessage(content=system_prompt)]

    for m in history:
        role = m.get("role", "user")
        content = m.get("content", "")
        if role == "user":
            messages.append(HumanMessage(content=content))
        else:
            messages.append(AIMessage(content=content))

    messages.append(HumanMessage(content=query))

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