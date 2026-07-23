# Hospital Management RAG + LLM Chatbot

A teaching-focused but runnable FastAPI capstone combining hospital CRUD APIs, SQLAlchemy/Alembic, Hugging Face embeddings, persistent vector retrieval, optional local or Groq generation, and a medical-only WebSocket chatbot.

## Important safety boundary

This software is an educational information assistant. It is not a medical device, does not diagnose, does not prescribe, and must not replace professional or emergency care. Do not load real patient-identifying data into an external LLM without the required consent, legal basis, access control, encryption, vendor review, and organisational approval.

## Architecture

```text
Browser / REST client
        |
        | HTTP + WebSocket
        v
FastAPI endpoints
        v
ChatService
  |-- greeting and emergency rules
  |-- medical-scope guard
  |-- RAG retrieval
  |-- provider factory
        |
        |-- retrieval-only (no generation key)
        |-- local Hugging Face
        `-- Groq (requires GROQ_API_KEY)
```

## Provider modes

- `LLM_PROVIDER=retrieval_only`: safest first run. Returns retrieved approved passages and needs no generative key.
- `LLM_PROVIDER=local_hf`: loads `google/flan-t5-base` locally through Transformers. The first run downloads model files. CPU generation can be slow.
- `LLM_PROVIDER=groq`: uses the Groq Python SDK and requires `GROQ_API_KEY`. When the key is absent, the factory falls back to retrieval-only.

The intended embedding backend is Hugging Face Sentence Transformers:

```env
EMBEDDING_BACKEND=sentence_transformers
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

`EMBEDDING_BACKEND=hash` exists only for tests or offline classroom demonstrations.

## 1. Create and activate a virtual environment

### Windows PowerShell

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Linux/macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

FAISS and Torch availability can differ by operating system and Python build. The application uses a NumPy vector-search fallback when FAISS is unavailable, but the Hugging Face modes still require their model dependencies.

## 2. Configure environment variables

```bash
cp .env.example .env
```

The included `.env` starts with SQLite, Sentence Transformers, and retrieval-only generation. Change the secret before any shared deployment.

For Groq:

```env
LLM_PROVIDER=groq
GROQ_API_KEY=your_key
GROQ_MODEL=llama-3.3-70b-versatile
```

For local Hugging Face generation:

```env
LLM_PROVIDER=local_hf
LOCAL_LLM_MODEL=google/flan-t5-base
LOCAL_LLM_DEVICE=-1
```

## 3. Create the database schema

For the first local run, development mode also calls `Base.metadata.create_all()`. The migration-based workflow is:

```bash
alembic upgrade head
```

When models change:

```bash
alembic revision --autogenerate -m "describe the schema change"
alembic upgrade head
```

## 4. Ingest the sample hospital knowledge base

```bash
python scripts/ingest_knowledge_base.py
```

What happens:

1. TXT/Markdown/PDF text is loaded.
2. Each document is split into overlapping chunks.
3. Chunks and metadata are stored in SQL.
4. Hugging Face generates normalised embeddings.
5. Vectors are written to FAISS when installed and to a NumPy fallback file.
6. Metadata is written to `storage/vector_index/metadata.json`.

Rebuild vectors from existing SQL chunks:

```bash
python scripts/ingest_knowledge_base.py --rebuild-only
```

## 5. Run the server

```bash
uvicorn app.main:app --reload
```

Open:

- Browser chatbot: `http://127.0.0.1:8000/`
- Swagger UI: `http://127.0.0.1:8000/docs`
- Health: `http://127.0.0.1:8000/api/v1/health`

## WebSocket protocol

Connect to:

```text
ws://127.0.0.1:8000/api/v1/chat/ws/{session_id}
```

Send:

```json
{
  "type": "chat_message",
  "message": "What documents are required for admission?"
}
```

The server sends `connection`, `status`, `answer`, `rejected`, or `error` events.

## Example REST flow

Create a department:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/departments \
  -H "Content-Type: application/json" \
  -d '{"name":"Cardiology","description":"Heart care"}'
```

Ask the chatbot without WebSocket:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/chat/query \
  -H "Content-Type: application/json" \
  -d '{"message":"What are the general ward visiting hours?"}'
```

## Run tests

Tests deliberately use the deterministic hash embedding backend, so they do not download a model.

```bash
pytest -q
```

## Docker Compose

```bash
docker compose up --build
```

Then ingest from inside the API container:

```bash
docker compose exec api python scripts/ingest_knowledge_base.py
```

The Compose setup uses PostgreSQL and persistent volumes for PostgreSQL, vector files, and the Hugging Face cache.

## Why the layers exist

- `api/`: HTTP and WebSocket route registration. Routes validate transport input and delegate work.
- `models/`: SQLAlchemy database entities.
- `schemas/`: Pydantic request/response validation.
- `crud/`: direct database operations.
- `services/`: business rules, ingestion, embedding, retrieval, prompts, and safety workflow.
- `llm/`: interchangeable generation providers behind one interface.
- `websocket/`: connection lifecycle and event handling.
- `scripts/`: operations that should run outside a request, such as bulk ingestion.

## Production work still required

This is a complete MVP and teaching capstone, not a finished clinical deployment. Before production use, add:

- Role-based permissions on every patient and document endpoint.
- Organisation/tenant isolation and row-level access rules.
- Encryption and secrets management.
- Audit logs and retention rules.
- Antivirus/file scanning and stronger document-parser isolation.
- Clinically reviewed knowledge sources and version approval.
- Retrieval and answer-quality evaluation sets.
- Rate limits and abuse controls.
- Redis or another shared channel layer when using multiple WebSocket workers.
- A separate inference service for heavy local models.
- Reverse-proxy WebSocket upgrades and timeout configuration.
- Monitoring, backups, disaster recovery, and incident response.
- Human review and jurisdiction-specific medical/privacy compliance.
