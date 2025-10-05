# RAG — Setup Qdrant, Ollama, and How to Run

This repository provides a simple RAG pipeline with:

- Qdrant as the vector database (via Docker Compose)
- Ollama for embeddings and LLM
- Python scripts for document ingestion and Q&A
- Optional n8n integration via the shared `ragnet` network

---

## Prerequisites

- macOS with Terminal access
- `Docker` and `Docker Compose`
- `Python` 3.11+ (3.12 recommended) and `pip`
- `Ollama`

---

## Environment Configuration

The root `.env` is used by Python scripts. Defaults are safe, but you can customize:

```
# key variables
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=kb_global
OLLAMA_BASE_URL=http://localhost:11434
LLM_MODEL=llama3.1:8b
EMBED_MODEL=nomic-embed-text
RAG_HOME=~/RAG
```

For Docker Compose, each folder `infrastructure/qdrant` and `infrastructure/n8n` has its own `.env` (see respective README files).

---

## Setup Ollama

1. Install Ollama (macOS):

- Download from `https://ollama.com/download` or via Homebrew: `brew install ollama`

2. Start Ollama server:

- `ollama serve` (keep it running), or use the background service if provided by the installer.

3. Pull required models:

- `ollama pull llama3.1:8b`
- `ollama pull nomic-embed-text`

4. Quick status check:

- API: `curl -fsS http://localhost:11434/api/tags`

---

## Run Qdrant (Vector DB)

1. Create shared network (optional but recommended):

- `docker network create ragnet`

2. Go to Qdrant Compose folder:

- `cd infrastructure/qdrant`

3. Adjust `.env` minimally:

- `QDRANT_VERSION`, `QDRANT_HTTP_PORT`, `QDRANT_GRPC_PORT`, `QDRANT_DATA_PATH`, `QDRANT_SNAPSHOTS_PATH` (see folder README for examples)

4. Start Qdrant:

- `docker compose up -d`
- Follow logs: `docker compose logs -f`

5. Host health check:

- `curl -fsS http://localhost:6333/readyz`

Note:

- The network hostname is `qdrant`. Other containers in `ragnet` can access it via `http://qdrant:6333`.

---

## (Optional) Run n8n

1. Ensure `ragnet` exists: `docker network create ragnet`
2. `cd infrastructure/n8n`
3. Set `.env` (port, basic auth, etc.)
4. Start: `docker compose up -d`
5. UI: `http://localhost:5678`

In `docker-compose.yml`, n8n already uses `QDRANT_URL=http://qdrant:6333` for in-network access.

---

## Set Up Virtualenv and Dependencies

1. From project root:

- `python3 -m venv .venv`
- `source .venv/bin/activate`

2. Install required Python packages:

```
pip install -U \
  langchain \
  langchain-qdrant \
  langchain-ollama \
  langchain-core \
  langchain-text-splitters \
  qdrant-client \
  python-dotenv \
  rich \
  pyyaml
```

---

## Ingest Corpus into Qdrant

1. Ensure Ollama and Qdrant are running.
2. From project root, run:

- `python ingest.py`

It will print the number of chunks indexed into the `kb_global` collection (default). Corpus is in `./corpus/`.

---

## Ask (Quickstart)

- `python ask.py "What is the Next.js App Router?"`

The script retrieves context from Qdrant and answers briefly based on available documents.

---

## Advanced CLI: `call_agent.py`

Features:

- Relevance scoring with a simple threshold
- Search profiles with heuristic fallback
- Source summary and execution timings

Examples:

- `python cli/call_agent.py -p nextjs15-en -q "How to use generateMetadata?"`
- All corpus (no profile): `python cli/call_agent.py -q "What is CQRS in NestJS?"`

Profiles are defined in `profiles.yaml`:

- `nextjs15-en`, `nestjs11-en`, and `all` (no filter)

---

## Key Structure

- `infrastructure/qdrant/` — Qdrant Compose and data
- `infrastructure/n8n/` — n8n Compose (optional)
- `corpus/` — Source docs (Next.js 15, NestJS 11)
- `ingest.py` — Ingest documents → Qdrant
- `ask.py` — Quick Q&A
- `cli/call_agent.py` — CLI with profiles and scoring
- `profiles.yaml` — Profile definitions

---

## Troubleshooting

- Qdrant not ready:
  - Health: `curl -fsS http://localhost:6333/readyz`
  - Logs: `cd infrastructure/qdrant && docker compose logs -f`
- Missing Ollama models:
  - Pull: `ollama pull llama3.1:8b` and `ollama pull nomic-embed-text`
  - Ensure server: `ollama serve`
- Docker port conflicts:
  - Change ports in each Compose `.env`, then `docker compose up -d` again
- Ingest cannot connect to Qdrant:
  - Ensure root `.env` `QDRANT_URL=http://localhost:6333`
  - If calling from another container in `ragnet`, use `http://qdrant:6333`
- Collection not found:
  - Ensure root `.env` `QDRANT_COLLECTION` matches ingest (`kb_global` by default)

---

## Quick Commands

- `docker network create ragnet`
- `cd infrastructure/qdrant && docker compose up -d`
- `source .venv/bin/activate && pip install -U ...`
- `python ingest.py`
- `python ask.py "your question"`
- `python cli/call_agent.py -p nextjs15-en -q "question"`

Happy building! For workflow automation, see `infrastructure/n8n` README for integrating with Qdrant over `ragnet`.
