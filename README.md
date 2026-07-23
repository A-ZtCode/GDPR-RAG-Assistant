# GDPR RAG Assistant

A retrieval-augmented question answering system for the EU General Data Protection Regulation. Ask questions about GDPR in natural language, get answers grounded in the actual text of the regulation with citations back to specific articles.

**Status:** work in progress. Building in public. The write-up series documents design decisions, code walkthroughs, and honest failure modes as they happen.

## Why this project

General-purpose language models answer regulatory questions confidently but often incorrectly, misattributing obligations or citing the wrong article. In a compliance context that's worse than saying "I don't know." This project builds a RAG system designed around grounded retrieval, verifiable citations, and honest refusal, using GDPR as a well-structured public corpus.

## Architecture

At query time: input guardrail, retriever over a vector store of chunked GDPR text, LLM generation constrained to the retrieved context, output validation, answer with citations to specific articles.

A separate ingestion pipeline chunks GDPR at the article level, computes embeddings, and loads the vector store.

## Write-up series

- [Part 1: Foundations, Decisions, and One API Key I Nearly Leaked](docs/blog/part-01-foundations.md)
- Part 2: Ingestion pipeline (coming)
- Part 3: Retrieval and grounded generation (coming)
- Part 4: Guardrails and evaluation (coming)
- Part 5: Serving and deployment (coming)

## Tech stack

- Python 3.12
- Anthropic Claude (Sonnet 4.5) for generation
- Chroma for the vector store (planned)
- Sentence Transformers for embeddings (planned)
- FastAPI for serving (planned)

## Running locally

```bash
git clone https://github.com/A-ZtCode/GDPR-RAG-Assistant.git
cd GDPR-RAG-Assistant
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your Anthropic API key
python test_llm.py
```

