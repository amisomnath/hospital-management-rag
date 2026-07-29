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

PostgreSQL with pgvector is the primary vector store. FAISS/NumPy is retained only
for lightweight SQLite tests. Torch availability can differ by OS/Python build.

## 2. Configure environment variables

```bash
cp .env.example .env
```

The included `.env` uses local PostgreSQL/pgvector on port 5432, Sentence
Transformers, and retrieval-only generation. Change the application and database
secrets. On the inspected RTX 3060 machine, use `EMBEDDING_DEVICE=cuda`.

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

PostgreSQL schemas and the `vector` extension are managed by Alembic:

```bash
sudo apt update
sudo apt install postgresql-18-pgvector

sudo -u postgres psql -c \
  "CREATE ROLE hospital_user WITH LOGIN PASSWORD 'replace-this-password';"
sudo -u postgres createdb -O hospital_user hospital_db
sudo -u postgres psql -d hospital_db -c \
  "CREATE EXTENSION IF NOT EXISTS vector;"

python -m alembic upgrade head
```

pgAdmin is a GUI client and does not install pgvector into PostgreSQL. After the
server package is installed, pgAdmin's Query Tool can run `CREATE EXTENSION
vector;` using a sufficiently privileged connection.

For Windows, follow the complete no-Docker instructions in `HANDOFF.md`, including
the pgvector Windows build, pgAdmin database creation, PowerShell environment,
CUDA verification and Alembic/startup order.

When models change:

```bash
alembic revision --autogenerate -m "describe the schema change"
alembic upgrade head
```

## 4. Ingest the sample hospital knowledge base

```bash
python scripts/ingest_knowledge_base.py
```

Validate the complete local CUDA/PostgreSQL/pgvector/Alembic setup:

```bash
python scripts/check_local_setup.py
```

Bulk upload through the authenticated API:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/documents/upload/bulk \
  -H "Authorization: Bearer $TOKEN" \
  -F "files=@document-one.md" \
  -F "files=@document-two.pdf"
```

Swagger and Postman must use repeated multipart field name `files`. The bulk
endpoint rebuilds the vector index once after the complete request.

What happens:

1. TXT/Markdown/PDF/DOCX text is loaded.
2. Each document is split into overlapping chunks.
3. Chunks and metadata are stored in SQL.
4. Hugging Face generates normalised embeddings.
5. Vectors are stored in PostgreSQL as `vector(384)`.
6. Queries use pgvector cosine distance; chat source metadata uses JSONB.

Rebuild vectors from existing SQL chunks:

```bash
python scripts/ingest_knowledge_base.py --rebuild-only
```

## 5. Run the server

```bash
uvicorn app.main:app --reload
```

Create the first admin (the password is prompted securely):

```bash
python scripts/create_admin.py --email admin@example.com --name "System Admin"
```

Open:

- Browser chatbot: `http://127.0.0.1:8000/`
- Swagger UI: `http://127.0.0.1:8000/docs`
- Health: `http://127.0.0.1:8000/api/v1/health`

## Authentication, token and chat-session flow

### 1. Register or use the terminal-created admin

Public registration creates a `patient`; the request cannot grant `staff`,
`doctor` or `admin` privileges. Passwords must contain 8–128 characters.

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "patient@example.com",
    "full_name": "Patient One",
    "password": "strong-password"
  }'
```

Registration returns the created user, not a token. Log in separately:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "patient@example.com",
    "password": "strong-password"
  }'
```

Successful login returns:

```json
{
  "access_token": "<signed-JWT>",
  "token_type": "bearer"
}
```

The JWT contains the user ID (`sub`), role, issue time (`iat`) and expiry (`exp`).
Its lifetime is controlled by `ACCESS_TOKEN_EXPIRE_MINUTES` (60 by default).

### 2. Save and use the token

For Bash with `jq` installed:

```bash
TOKEN="$(
  curl -s -X POST http://127.0.0.1:8000/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"patient@example.com","password":"strong-password"}' |
  jq -r '.access_token'
)"
```

Alternatively, copy only the `access_token` value from the login response:

```bash
TOKEN='paste-the-access-token-here'
```

Send it to protected REST endpoints as a Bearer token:

```bash
curl http://127.0.0.1:8000/api/v1/users/me \
  -H "Authorization: Bearer $TOKEN"
```

Missing, invalid or expired REST tokens return HTTP `401`. There is currently no
refresh-token, revocation or server-side logout endpoint. Client logout means
deleting the locally stored token. An already issued token remains usable until
expiry unless the user is deactivated or `SECRET_KEY` is changed.

### 3. Start or continue a REST chat session

Omit `session_id` on the first request. The server creates a UUID and returns it:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/chat/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"message":"What are the general ward visiting hours?"}'
```

Example response shape:

```json
{
  "answer": "...",
  "category": "hospital",
  "provider": "retrieval_only",
  "session_id": "0bfa89c0-7de0-4d24-a54c-0cb67a52c14c",
  "sources": [],
  "safety_notice": "..."
}
```

Copy the returned `session_id` into later requests to store them under the same
conversation:

```bash
SESSION_ID='paste-the-returned-session-id-here'

curl -X POST http://127.0.0.1:8000/api/v1/chat/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{\"message\":\"What documents are needed?\",\"session_id\":\"$SESSION_ID\"}"
```

If `session_id` is omitted, a new session is created. If an unknown ID is supplied
to the REST endpoint, the server creates a new session with a different generated
ID; always use the ID returned in the response.

### 4. WebSocket protocol

Generate a UUID in the browser with `crypto.randomUUID()` or in a terminal:

```bash
SESSION_ID="$(python -c 'import uuid; print(uuid.uuid4())')"
```

Connect using the session ID and JWT:

```text
ws://127.0.0.1:8000/api/v1/chat/ws/{session_id}?token=<JWT>
```

Browser example:

```javascript
const sessionId = crypto.randomUUID();
const ws = new WebSocket(
  `ws://127.0.0.1:8000/api/v1/chat/ws/${sessionId}` +
  `?token=${encodeURIComponent(accessToken)}`
);

ws.onmessage = (event) => console.log(JSON.parse(event.data));
ws.onopen = () => ws.send(JSON.stringify({
  type: "chat_message",
  message: "What documents are required for admission?"
}));
```

The protected socket closes with policy code `1008` when authentication fails.
It sends `connection`, `status`, `answer`, `rejected`, or `error` events. This is
native WebSocket, not Socket.IO. Use `wss://` behind HTTPS in production.

### 5. Current session/history behavior and limitations

- With `SAVE_CHAT_HISTORY=true`, user and assistant messages are persisted in
  `chat_sessions` and `chat_messages`; disabling it stops message persistence.
- Reusing an existing session ID stores later messages in the same session.
- Stored history is not currently loaded into the prompt, so answers are grounded
  in the current message and retrieved documents, not earlier conversation turns.
- The current code does not assign newly created sessions to `user_id` and does
  not enforce session ownership. Do not treat session IDs as an authorization
  boundary; add ownership checks before production or multi-user deployment.
- There is no session list/history/delete API and no automatic session expiry yet.
- WebSocket JWTs are passed in the query string because browser WebSocket cannot
  set an Authorization header. Production proxies must redact query strings.

### 6. Role example

Creating a department requires an authenticated role allowed by that endpoint:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/departments \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"name":"Cardiology","description":"Heart care"}'
```

Authentication failures return `401`; an authenticated user without the required
role receives `403`. Knowledge-document list/upload requires `staff`, `doctor` or
`admin`. The terminal-created admin can perform privileged setup operations.

## Run tests

Tests deliberately use the deterministic hash embedding backend, so they do not download a model.

```bash
pytest -q
```

## Docker Compose

Docker is optional; the local PostgreSQL workflow above is the primary setup.

```bash
docker compose up --build
```

Then ingest from inside the API container:

```bash
docker compose exec api python scripts/ingest_knowledge_base.py
```

The Compose setup uses the pgvector PostgreSQL image and persistent volumes for
PostgreSQL, the SQLite fallback artifacts, and the Hugging Face cache.

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
