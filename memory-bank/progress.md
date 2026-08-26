# Progress

<!-- Running log. Append, don't rewrite history. Newest at top.
     This tracks WORK STATUS (agent-facing, session to session).
     For the forward-looking feature plan, see ROADMAP.md instead —
     don't duplicate the full plan here, just what's actually in motion. -->

## Done

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

