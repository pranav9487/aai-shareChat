# Progress

<!-- Running log. Append, don't rewrite history. Newest at top.
     This tracks WORK STATUS (agent-facing, session to session).
     For the forward-looking feature plan, see ROADMAP.md instead —
     don't duplicate the full plan here, just what's actually in motion. -->

## Done

- backend-live-debug — end-to-end live verification of POST /api/query after the Pinecone
  pivot; fixed the full failure chain on main (b1a280d…10b6b9d): 403 "unknown user"
  (frontend/backend user-list drift → `guest` seeded on both sides, employee-only); bare 500 on
  missing GROQ key → actionable 503 guard in deps; `ensure_corpus` auto-provision wired into
  lifespan; session-view tests drifted to `/sessions/…` → corrected to `/api/sessions/…`;
  `pinecone` + `fastembed` SDKs were pinned but never installed into `.venv` → installed;
  Pinecone `delete_source` 404s on never-upserted serverless namespaces → treated as
  nothing-to-delete; `count()` trusted lagging `describe_index_stats` (0 for a populated index)
  → zero-report is probed with a non-zero vector; `GROQ_MODEL` `qwen/qwen3-32b` (dead id) →
  verified `qwen/qwen3.6-27b` in `.env`; qwen3 `<think>` blocks stripped from answers.
  LIVE-VERIFIED: priya(hr) → "accrue 25 vacation days" + hr source; guest(employee) → filtered
  to general tier only; mallory → 403; no header → 401. Full pytest suite + ruff + black green.
  Regression tests added at each layer (test_deps, test_pinecone_store ×3, test_chain,
  test_access_control, test_api paths) — 2026-08-27.
- nexora-ingestion — prepared chunk/embed/load of `documents/Nexora Technologies
  Pvt. Ltd.md`: `documents/ingest_nexora.py` splits the handbook into its 28
  numbered policy sections, assigns per-section RBAC access levels, writes each as
  a front-matter'd corpus doc, then chunks (~800 chars/~100 overlap) and embeds
  (ChromaDB default MiniLM) into the persistent `internal_docs` collection with
  `source/access_level/title/chunk_index` metadata. Hardened the script to create
  `OUTPUT_DIR` on a clean checkout and to fail-fast when no sections parse.
  NOT executed here — the repo's bash shell is broken (spawn `bash.exe ENOENT`),
  so ChromaDB ingestion still needs a working terminal. — 2026-08-27.
- shared-sessions — roadmap Now §3: `SessionStore` protocol + `InMemorySessionStore`
  (`backend/app/services/session/`), required (and now logged) `session_id` on
  POST /api/query, and a read-time visibility filter on GET /api/sessions/{id}
  that returns a non-leaky placeholder (never the answer/sources) when a viewer
  lacks the tiers a message drew from; live retrieval still fresh + filtered per
  user (no reuse of another user's context). Frontend: `getSession` client +
  shared-transcript panel with per-viewer refresh; ADR-0006; RBAC/extant tests
  preserved. Branch feature/shared-sessions, NOT yet merged — 2026-08-27.
- debug-unknown-user-403 — identified root cause of 403 Forbidden ("Access denied: unknown user"): backend `InMemoryUserDirectory` strictly validates user IDs against seeded users (`alice`, `priya`, `carlos`, `dana`, `guest`); entering an unseeded ID like `1` properly triggers non-leaky 403 rejection. Updated input placeholder in `UserSelector.jsx` to clearly show valid seed IDs — 2026-08-26.

- frontend-rebuild — identity-aware chat UI rebuilt in **JavaScript** per product decision
  (TS attempt on parked branch feature/frontend-bootstrap discarded): Vite+React18+JSX, demo-user
  picker + custom id/role override, single apiClient posting X-User-ID to POST /api/query,
  canonical-decline detection + styled security notices, per-page session_id on every request,
  Vite dev proxy (no backend CORS); gates: ESLint clean (new lint gate incl. react-hooks rules),
  Vitest/RTL 16/16, vite build ✓, backend regression ✓; ADR-0005 rewritten as the JS decision —
  2026-08-26 (branch feature/frontend-rebuild, NOT yet merged).
- access-control — X-User-ID identity + UserDirectory protocol (in-memory seed, optional
  ACCESS_CONTROL_SEED_JSON), role→tier RBAC enforced inside the ChromaDB where-filter, canonical
  security-decline vs not-found answers, authenticated POST /api/query replacing the pre-auth dev
  stub, 33 new adversarial unit/API tests + RBAC integration assertion, ADR-0004 — 2026-08-26
  (branch feature/access-control, NOT yet merged).
- rag-pipeline-verification — first-ever execution of the suite: fixed 3 latent test bugs
  (missing RetrievedChunk.distance in two fixtures, directory test writing without mkdir, stub
  isinstance assert shadowing pipeline validation), drove ruff + black to zero findings, created
  isolated .venv after a global langchain 1.x install broke the pinned langchain-core —
  2026-08-26 (branch fix/rag-pipeline-verification, NOT yet merged).
- rag-pipeline — core pipeline bootstrapped end-to-end (FastAPI app, ChromaDB store wrapper, chunker/ingestion, retriever, Groq chain, facade, dev query route); deterministic 12-doc test corpus generator; unit suite written; ADRs 0002–0003; TBDs resolved in tech-stack.md — 2026-08-25. NOTE: superseded by rag-pipeline-verification above; code merged to main as 144651c before verification ran.

## In progress

- (nothing currently in motion)

