# Tech Stack

## Backend
- Language: Python (3.11 per CI matrix)
- Framework: FastAPI
- Agent/RAG framework: LangChain (`langchain-core` + `langchain-groq`; see ADR-0003)

## Frontend
- Language: JavaScript/TypeScript: TBD
- Framework: React
- Version: TBD

## LLM
- Provider: Groq
- Model: Qwen, 27B model as specified for this project
- Exact API model identifier: configured via `GROQ_MODEL` env var; placeholder default
  `qwen/qwen3-32b` pending verification against the Groq model list (ADR-0003)

## Retrieval
- RAG architecture: Yes
- Vector database: ChromaDB (persistent client, cosine space)
- Embeddings model: ChromaDB default (all-MiniLM-L6-v2 ONNX) behind injectable `EmbedFn` (ADR-0002)

## Database
- Supabase
- Intended usage:
  - Conversation history
  - Session data
  - User IDs
  - User roles
  - Access-control-related data

## Testing
- Test framework: pytest (config in root `pyproject.toml`)
- Test file location: `backend/tests/`
- Test naming convention: `test_<unit>.py`, functions `test_<behavior>`
- Test command: `pytest` (from repo root); integration tests auto-skip without `GROQ_API_KEY`

## Linting and Formatting
- Linter: ruff (`ruff check .`)
- Formatter: black (`black .`)
- Lint command: `ruff check .`
- Format command: `black .`

## Package Management
- Python package manager: pip + `requirements.txt` at repo root (ADR-0003)
- Frontend package manager: TBD

## Commands

### Backend
Run inside the repo `.venv` (global site-packages conflict with pinned langchain-core).
- Development command: `uvicorn app.main:app --reload --app-dir backend`
- Build command: TBD (not applicable yet)
- Run command: `uvicorn app.main:app --host 0.0.0.0 --port 8000 --app-dir backend`
  (NOTE: the previously documented `backend.app.main:app` target could never import — fixed.)

### Frontend
- Development command: TBD
- Build command: TBD
- Run command: TBD

### Testing
- Test command: `pytest`

### Code Quality
- Lint command: `ruff check .`
- Format command: `black .`

## Environment Variables

All secrets, credentials, API keys, and service configuration must be stored in `.env` files and must never be hardcoded.

Expected values include:
- Groq API key (`GROQ_API_KEY`)
- Groq model id (`GROQ_MODEL`)
- ChromaDB persistence dir (`CHROMA_PERSIST_DIR`)
- Documents dir (`DOCUMENTS_DIR`)
- Optional user-registry seed JSON (`ACCESS_CONTROL_SEED_JSON`) — ADR-0004
- Supabase URL / keys (future items)
- Any other future service credentials

See `.env.example` for the canonical list. Do not commit `.env` files to version control.
