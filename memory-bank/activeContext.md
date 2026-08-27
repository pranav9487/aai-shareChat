# Active Context

<!-- Update this at the end of every session. This is the first thing to read when resuming. -->

## Current focus
Roadmap Now §3 (shared-session safety) IMPLEMENTED on new branch
`feature/shared-sessions` (off main): backend `SessionStore` protocol +
`InMemorySessionStore` under `app/services/session/`, `POST /api/query` now
requires and logs `session_id` (author, role, question, answer, sources, drawn
access_levels), and `GET /api/sessions/{id}` returns the transcript filtered
per the requesting viewer — non-visible answers return a non-leaky placeholder
and empty sources, never another user's retrieved content. Frontend mirrors it:
`getSession` client + a `SharedTranscript` panel with a per-viewer Refresh.
ADR-0006. **Committed locally, NOT merged/pushed — awaits review (rules 02/05).**

## Recent decisions
- ADR-0006: session persistence lives behind a `SessionStore` protocol seam
  (in-memory today, Supabase later) mirroring `UserDirectory` (ADR-0004); open
  membership is safe because the per-viewer visibility filter is the guard.
- Visibility rule: a message's answer shows to a non-author only if every
  `access_level` the answer drew from is within the viewer's allowed tiers; the
  question stays, only answer+sources are hidden. Live queries remain fresh +
  permission-filtered — never reuse another user's stored context (invariant).
- ADR-0005 (rewritten): React 18 in plain JavaScript/JSDoc via Vite+npm; TS layer dropped for
  ceremony reasons; ESLint 9 flat config (js-recommended + react-hooks + jsx-uses-vars) replaces
  tsc as the lint gate; vitest pinned ^3 (v2 bundles vite@5 → plugin type clash with vite@6).
- User edits preserved: `/new-feature` workflow gained step 11 (consult tech-stack.md +
  ROADMAP.md per feature) — carried onto this branch, committed here.
- Generated test corpus is intentionally tracked on main (user commit "#2 step") despite
  .gitignore; do not remove it.
- Demo users mirrored client-side from seed registry (+ custom id/role override); drift documented
  until users-list endpoint / Supabase. ACCESS_DENIED_ANSWER mirrored as JS constant.
- Backend run command fix stands: `uvicorn app.main:app --app-dir backend`.

## Blockers / open questions
- No `GROQ_API_KEY` locally → live chat answers impossible (UI shows styled Request-failed);
  integration tests auto-skip. Add key to `.env` when ready.
- The POSIX shell (`bash`) for running git/pytest/npm is currently BROKEN in this
  environment (spawn `bash.exe ENOENT`), so the git branch/commit and test suite
  could NOT be executed here — a working terminal (or git-enabled environment)
  is required to validate and commit.
- Nexora handbook ingestion (`documents/ingest_nexora.py`, hardened 2026-08-27) is
  ready but UNRUN for the same reason — ChromaDB persists to `chroma_db/` (gitignored)
  only once the script executes with a working terminal.
- Exact Groq model id ("Qwen 27B") still unverified vs GROQ_MODEL default.
- CHANGELOG regeneration tooling still undecided; file remains [Unreleased]-empty (never
  hand-edited per rule).
- Three Dependabot PRs open (actions bumps). No frontend CI steps yet.
- Parked branch `feature/frontend-bootstrap` deletion needs explicit user confirmation (rule 05).

## Next step
In a working shell, run the full validation (backend `pytest`, `ruff check .`,
`black --check .`; frontend `npm test`, `npm run lint`, `npm run build`), fix any
failures, and commit `feature/shared-sessions` per 02-commit-style; regenerate
CHANGELOG via the /commit workflow. On approval, merge → main (tag if desired).
Then, in a FRESH session per 06-session-efficiency: roadmap Next-v2 (Supabase
persistence behind the `SessionStore`/`UserDirectory` seams) for durable shared
sessions, which unblocks Now §4 (safe follow-up handling).

