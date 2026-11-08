# RAG Knowledge-Base Poisoning Demo

> **⚠️ Educational / lab use only.** All data is fictional. This project demonstrates a knowledge-base poisoning attack against a Retrieval-Augmented Generation (RAG) system in a controlled local environment.

## The Problem

RAG systems retrieve documents from a knowledge base and feed them to an LLM as context. If an attacker can **inject a malicious document** into the knowledge base, they can manipulate the retrieved context and cause the LLM to return **wrong, attacker-chosen answers** — without modifying the model itself.

This is called **RAG knowledge-base poisoning** (or *indirect prompt injection via retrieval*).

## Architecture

```
User Question → Embed query → FAISS top-k search → Retrieved chunks → LLM prompt → Answer
                                    ↑
                         data/clean/ + any uploaded docs
                        (attacker injects poison here)
```

- **Embeddings:** `all-MiniLM-L6-v2` via `sentence-transformers` (local, CPU-only)
- **Vector index:** `faiss-cpu`
- **LLM:** Any model on [OpenRouter](https://openrouter.ai) via the OpenAI-compatible API
- **UI:** Streamlit

## Quick Start

```bash
# 1. Clone and enter the project
cd RAG-Poisoning

# 2. Create a virtual environment
python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate  # Linux/Mac

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure your API key
copy .env.example .env
# Edit .env and paste your OpenRouter API key

# 5. Run the app
streamlit run app/ui.py
```

The first run will download the `all-MiniLM-L6-v2` model (~80 MB). Subsequent runs use the cache.

## Demo Steps

| Step | Action | What to observe |
|------|--------|-----------------|
| 1 | Ask: *"How do I reset my VPN password?"* | Clean answer citing the IT Self-Service Portal, extension 4357 |
| 2 | Upload `data/poison/vpn_password_reset_poison.txt` via the sidebar | Document is chunked and added to the index |
| 3 | Ask the same question again | Answer now cites the fake helpdesk (1-800-555-0199) and a phishing URL |
| 4 | Expand the **Transparency Panel** | The poison chunk appears at Rank 1 with a high similarity score |
| 5 | Click **Reset to clean knowledge base** | Index reverts to clean docs only |

## Project Structure

```
RAG-Poisoning/
├── app/
│   ├── ui.py            # Streamlit interface
│   ├── rag_engine.py    # Chunking, embedding, FAISS index, retrieval
│   └── llm_client.py    # OpenRouter / OpenAI-compatible LLM calls
├── data/
│   ├── clean/           # 17 fictional Acme Corp documents
│   └── poison/          # Pre-made poison document
├── defense/
│   ├── __init__.py
│   └── filters.py       # Defense hook stubs (ingestion + retrieval)
├── .env.example
├── requirements.txt
├── README.md
└── WRITEUP.md           # Lab write-up skeleton
```

## Defense Hooks

The code has two clearly marked integration points for defenses (both are no-op stubs by default):

1. **Ingestion-time check** (`defense/filters.py → ingestion_check()`): Called before a document enters the index. Can reject suspicious documents.
2. **Retrieval-time filter** (`defense/filters.py → retrieval_filter()`): Called after top-k retrieval, before chunks go to the LLM. Can filter or re-rank results.

## License

See [LICENSE](LICENSE).
