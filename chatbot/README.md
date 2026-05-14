# CEO Transition Analysis RAG Chatbot

A Retrieval-Augmented Generation (RAG) chatbot powered by LangChain and OpenAI GPT-4o-mini. Answers questions about CEO transitions, stock performance, KPIs, and financial analysis grounded in real S&P 100 data spanning 1996-2025.

## Architecture

The chatbot implements a 6-step RAG pipeline:

```
User Query
    ↓
Step 1: Load Knowledge Base Documents (.md files)
    ↓
Step 2: Split Documents into Chunks (500 chars, 50 overlap)
    ↓
Step 3: Create OpenAI Embeddings (text-embedding-3-small)
    ↓
Step 4: Store in ChromaDB Vector Store (persisted to disk)
    ↓
Step 5: Retrieve Top-4 Relevant Chunks (semantic similarity)
    ↓
Step 6: Generate Answer with GPT-4o-mini (grounded in data)
    ↓
Response to User
```

Each step is in its own file for clarity and testability.

## Folder Structure

```
chatbot/
├── knowledge_base/                  # Grounding knowledge
│   ├── financial_terms.md           # Sharpe, volatility, drawdown, etc.
│   ├── calculations.md              # How KPIs are calculated
│   ├── outlier_methodology.md       # Z-score, outlier classification
│   └── ceo_analysis.md              # Data sources, methodology
│
├── step1_load_documents.py          # Load .md files
├── step2_chunk_documents.py         # Split into chunks
├── step3_create_embeddings.py       # Create OpenAI embeddings
├── step4_store_chromadb.py          # Persist to ChromaDB
├── step5_retrieve_chunks.py         # Semantic search
├── step6_generate_answer.py         # Call GPT-4o-mini
├── context_builder.py               # Load company/KPI data
├── rag_pipeline.py                  # Orchestrate all steps
│
├── tests/                           # Unit tests
│   ├── test_step1_load.py
│   ├── test_context_builder.py
│   └── ...
│
├── chroma_db/                       # ChromaDB storage (auto-created)
├── requirements.txt
├── __init__.py
└── README.md (this file)
```

## Setup

### 1. Install Dependencies

```bash
pip install -r chatbot/requirements.txt
```

Dependencies:
- `langchain` - LLM orchestration framework
- `langchain-openai` - OpenAI integration
- `langchain-chroma` - ChromaDB vector store
- `chromadb` - Vector database
- `openai` - OpenAI API client
- `tiktoken` - Token counting for OpenAI
- `unstructured` - Document parsing

### 2. Set Environment Variable

```bash
export OPENAI_API_KEY="sk-..."
```

Or on EC2 systemd service, add to `/etc/systemd/system/ceo-backend.service`:
```ini
[Service]
Environment="OPENAI_API_KEY=sk-..."
```

### 3. Build ChromaDB Vector Store (First Time Only)

```bash
cd chatbot
python rag_pipeline.py
```

This:
1. Loads all .md files from `knowledge_base/`
2. Chunks them (500 chars, 50 overlap)
3. Creates embeddings using OpenAI text-embedding-3-small
4. Stores in ChromaDB (persisted to `chroma_db/`)
5. Runs batch tests

On subsequent runs, ChromaDB is loaded from disk (no API calls needed).

## Usage

### As a Python Module

```python
from chatbot.rag_pipeline import RAGPipeline

# Initialize (loads documents, ChromaDB, embeddings)
pipeline = RAGPipeline()

# Answer a general question
answer = pipeline.answer("What is Sharpe ratio?")
print(answer)

# Answer a company-specific question
answer = pipeline.answer(
    "How did AAPL stock perform after Tim Cook became CEO?",
    ticker="AAPL"
)
print(answer)

# Answer a sector question
answer = pipeline.answer(
    "Which Technology CEOs outperformed their sector?",
    sector="Technology"
)
print(answer)
```

### From FastAPI Backend

```python
# In backend/main.py
from chatbot.rag_pipeline import RAGPipeline

rag = RAGPipeline()  # Initialize once at startup

@app.post("/api/chat")
async def chat(request: ChatRequest):
    answer = rag.answer(
        query=request.query,
        ticker=request.ticker,
        sector=request.sector,
        transition_date=request.transition_date
    )
    return {"response": answer}
```

## Knowledge Base

The chatbot is grounded in 4 markdown files:

### 1. `financial_terms.md`
- Sharpe ratio, volatility, max drawdown
- Moving averages, beta, volume metrics
- CEO transition terminology (8-K filing, transition date, etc.)
- Performance measurement periods (90-day, 1-year)

### 2. `calculations.md`
- Formula for impact_90days_pct
- Formula for impact_1year_pct
- Formula for pre_transition_trend_90d_pct
- Volatility calculation (annualized std dev)
- Sharpe ratio calculation
- Max drawdown calculation
- Volume metrics

### 3. `outlier_methodology.md`
- Z-score standardization
- CEO Performance Outliers (90-day, 1-year, volatility)
- CEO Tenure Outliers
- Company Stock Outliers
- STRONG, MODERATE, NORMAL classification
- Sector-by-sector baselines

### 4. `ceo_analysis.md`
- Data sources (SEC 8-K filings, yfinance, NBER recession dates)
- Dataset scope (100 companies, 251 transitions, 1996-2025)
- KPI calculation pipeline
- 11 GICS sectors
- CEO transition types (planned, unexpected, interim, internal/external)
- Analysis quality indicators
- Limitations and caveats

## Testing

Run unit tests:

```bash
# Test Step 1 (Load documents)
python chatbot/tests/test_step1_load.py

# Test Context Builder
python chatbot/tests/test_context_builder.py

# Run all tests with pytest
pytest chatbot/tests/ -v
```

Tests verify:
- Documents load correctly
- Chunks are created
- Embeddings work
- ChromaDB persists
- Retrieval returns relevant chunks
- Answer generation works
- Context builder loads company data

## How It Works

### Example: "How did AAPL stock perform after Tim Cook became CEO?"

**Step 1-4:** (Initialization - runs once)
- Load 4 knowledge base markdown files
- Split into ~50 chunks (financial_terms, calculations, etc.)
- Create OpenAI embeddings (1536-dim vectors)
- Store in ChromaDB at `chatbot/chroma_db/`

**Step 5:** (Retrieval - per query)
- Convert user query to embedding
- Find top-4 most similar chunks in ChromaDB
- Retrieved chunks might be:
  1. "Impact 1 Year section from calculations.md"
  2. "CEO transition impact metrics from financial_terms.md"
  3. "Transition date definition"
  4. "Macro context handling"

**Build Context:**
- Load AAPL company data from `data/companies.json`
- Load AAPL KPI data from `data/stocks/kpis/AAPL_kpis.json`
- Format as readable text:
  ```
  Company: Apple Inc. (AAPL)
  Sector: Technology
  CEO: Tim Cook (2011-08-24)
  90-day impact: +18.4%
  1-year impact: +45.2%
  Macro: Not in recession
  ```

**Step 6:** (Generation)
- Build system prompt with:
  - Retrieved chunks (knowledge base context)
  - AAPL data context (real numbers)
  - Clear instructions
- Send to GPT-4o-mini:
  - Temperature 0.3 (deterministic)
  - Max tokens 500 (concise)
- Return answer grounded in both knowledge base and real data

**Example Answer:**
```
Tim Cook's appointment as CEO in August 2011 had a strong positive impact on
AAPL stock. In the first 90 days, the stock gained 18.4%, and by the one-year
mark, it had appreciated 45.2%. This outperformance occurred outside a recession
period, indicating investor confidence in Cook's strategic direction and
operational capabilities. The sustained 1-year return suggests the market viewed
the transition as successful.
```

## LangChain Components Used

- **DirectoryLoader**: Load markdown files
- **UnstructuredMarkdownLoader**: Parse markdown
- **RecursiveCharacterTextSplitter**: Smart text splitting
- **OpenAIEmbeddings**: text-embedding-3-small model
- **Chroma**: Vector database (persisted)
- **similarity_search**: Semantic search on embeddings
- **ChatOpenAI**: GPT-4o-mini with message format
- **SystemMessage/HumanMessage**: LangChain message types

## Performance Notes

- **First run:** ~30-60 seconds (create embeddings, store in ChromaDB)
- **Subsequent runs:** <1 second (load from ChromaDB disk)
- **Per query:** ~2-3 seconds (retrieve chunks + call OpenAI)
- **API costs:** Minimal (text-embedding-3-small: $0.02 per million tokens)

## Integration with Frontend

Replace the static `ChatBot.tsx` with API calls:

```typescript
const generateResponse = async (query: string): Promise<string> => {
  const res = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query,
      ticker: company?.ticker ?? null,
      transition_date: transition?.transitionDate ?? null,
      sector: company?.sector ?? null,
    })
  });
  const data = await res.json();
  return data.response;
};
```

## Troubleshooting

**Error: OPENAI_API_KEY not set**
```bash
export OPENAI_API_KEY="sk-..."
```

**Error: ChromaDB not found**
- First run requires building ChromaDB:
  ```bash
  python chatbot/rag_pipeline.py
  ```

**Error: DocumentLoader not found**
```bash
pip install --upgrade langchain-community unstructured
```

**Slow response**
- First query slower (loading models)
- Subsequent queries faster
- ChromaDB persists to disk

**Low quality answers**
- Check that data context is being passed (ticker/sector)
- Verify knowledge base files exist in `knowledge_base/`
- Ensure KPI data exists in `data/stocks/kpis/`

## Future Improvements

- [ ] Fine-tune embeddings on domain-specific text
- [ ] Add memory for multi-turn conversations
- [ ] Implement conversation turn tracking
- [ ] Add streaming responses
- [ ] Caching frequent queries
- [ ] Better error handling
- [ ] Logging and monitoring

## References

- [LangChain Documentation](https://python.langchain.com/)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [OpenAI API Reference](https://platform.openai.com/docs/)
- [RAG Architecture](https://arxiv.org/abs/2005.11401)
