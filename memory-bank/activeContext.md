# Active Context

<!-- Update this at the end of every session. This is the first thing to read when resuming. -->

## Current focus
Roadmap §1 verification is CLOSED (suite now actually runs, gates green) and §2 access control is
implemented end-to-end on `feature/access-control`, stacked on `fix/rag-pipeline-verification`.
Gate in the isolated `.venv`: pytest **77 passed / 2 skipped** (key-gated integration), ruff
clean, black clean, live uvicorn boot + HTTP identity smoke passed. **Nothing is pushed or
merged yet** — both branches await user review/approval (rules 02/05).

## Recent decisions
- Local dev MUST use the repo `.venv`: the global Anaconda env ships `langchain` 1.x which breaks
  the pinned `langchain-core` 0.3.x (`module 'langchain' has no attribute 'debug'`).
- ADR-0004: identity = `X-User-ID` header → `UserDirectory` protocol (v1 in-memory seed, optional
  `ACCESS_CONTROL_SEED_JSON`); roles→tiers via one mapping table; enforcement INSIDE the ChromaDB
  `where` filter; empty filtered retrieval triggers ONE internal unfiltered existence probe that
  picks canonical `ACCESS_DENIED_ANSWER` vs `NOT_FOUND_ANSWER` (LLM never called either way).
- Dev stub `/api/dev/query` removed → authenticated `POST /api/query`.
- Documented run command was broken (`backend.app.main:app` cannot import top-level `app`);
  correct form: `uvicorn app.main:app --app-dir backend` (tech-stack.md updated).
- Scoped ruff ignore: B008 for `backend/app/api/**` (FastAPI Depends-in-default DI pattern).
- Vocabularies use `enum.StrEnum` (UP042, py311 target).

## Blockers / open questions
- No `GROQ_API_KEY` locally → live LLM round-trip and the 2 integration tests remain unexecuted
  by design; add a real key to `.env` to run them.
- Exact Groq model id for "Qwen 27B" still unverified (placeholder `qwen/qwen3-32b`).
- User added a "Next" section to ROADMAP.md mid-session (frontend → Supabase → connect); it rides
  along in the docs commit — split it out if unwanted.
- Three Dependabot PRs open for GitHub Actions bumps (checkout / setup-python / gitleaks).

## Next step
With user approval: merge `fix/rag-pipeline-verification` → main, then `feature/access-control`
→ main (that order), tag, push. Then start ROADMAP "Next" v1 (React frontend) in a FRESH session
per 06-session-efficiency.

