# Tech Stack

## Backend
- Language: Python (3.11 per CI matrix)
- Framework: FastAPI
- Agent/RAG framework: LangChain (`langchain-core` + `langchain-groq`; see ADR-0003)

## Frontend
- Language: JavaScript + JSX (light JSDoc; see ADR-0005 — supersedes the
  abandoned TypeScript attempt on parked branch feature/frontend-bootstrap)
- Framework: React 18
- Build tool: Vite (@vitejs/plugin-react)
- Testing: Vitest + React Testing Library + jsdom (`npm test`)
- Lint gate: ESLint 9 flat config (js-recommended + react-hooks; `npm run lint`)
- Dev proxy: `/api` → `http://127.0.0.1:8000` configured in `vite.config.js`,
  so the FastAPI backend needs no CORS settings

## LLM
- Provider: Groq
- Model: Qwen, 27B model as specified for this project
- Exact API model identifier: configured via `GROQ_MODEL` env var; placeholder default
  `qwen/qwen3-32b` pending verification against the Groq model list (ADR-0003)

## Retrieval
- RAG architecture: Yes
- Vector database: Pinecone (hosted, serverless index, cosine space) — see ADR-0007
- Embeddings model: local MiniLM-L6-v2 (ONNX via FastEmbed, 384-dim) behind the injectable `EmbedFn` (ADR-0002, kept in ADR-0007); the Pinecone index is created to match (dim 384)

## Database
- Supabase
- Intended usage:
  - Conversation history
  - Session data
  - User IDs
  - User roles
  - Access-control-related data

## Shared sessions (roadmap item 3)
- `SessionStore` protocol seam (in-memory today; Supabase later) — mirrors the
  `UserDirectory` seam from ADR-0004. See ADR-0006.
- `POST /api/query` requires `session_id` and logs each exchange (author, role,
  question, answer, sources, drawn `access_level`s) to the store.
- `GET /api/sessions/{session_id}` returns the transcript filtered per the
  viewer's permissions; non-visible answers come back as a non-leaky
  placeholder with empty sources.

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
- Frontend package manager: npm, lockfile committed (`frontend/package-lock.json`; ADR-0005)

## Commands

### Backend
Run inside the repo `.venv` (global site-packages conflict with pinned langchain-core).
- Development command: `uvicorn app.main:app --reload --app-dir backend`
- Build command: TBD (not applicable yet)
- Run command: `uvicorn app.main:app --host 0.0.0.0 --port 8000 --app-dir backend`
  (NOTE: the previously documented `backend.app.main:app` target could never import — fixed.)

### Frontend
Run inside `frontend/`; requires the FastAPI backend on port 8000 for live data.
- Development command: `npm run dev` (Vite on :5173, proxies `/api` to :8000)
- Build command: `npm run build` (vite build → `dist/`)
- Lint command: `npm run lint` (ESLint flat config)
- Test command: `npm test` (vitest run, jsdom, offline)

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
- Pinecone API key (`PINECONE_API_KEY`)
- Pinecone index name / namespace / cloud / region (`PINECONE_INDEX_NAME`, `PINECONE_NAMESPACE`, `PINECONE_CLOUD`, `PINECONE_REGION`) — see ADR-0007
- Documents dir (`DOCUMENTS_DIR`)
- Optional user-registry seed JSON (`ACCESS_CONTROL_SEED_JSON`) — ADR-0004
- Supabase URL / keys (future items)
- Any other future service credentials

See `.env.example` for the canonical list. Do not commit `.env` files to version control.
