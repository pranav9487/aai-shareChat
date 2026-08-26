# Active Context

<!-- Update this at the end of every session. This is the first thing to read when resuming. -->

## Current focus
Frontend REBUILT in JavaScript per product decision (the TypeScript attempt on parked branch
`feature/frontend-bootstrap` is discarded — do not merge it). New branch
`feature/frontend-rebuild` off main@ed39778 carries: Vite + React 18 + JSX app wired to
`POST /api/query` (`X-User-ID` header, session_id in body), security-decline rendering,
ESLint+Vitest+vite-build gates all green, backend regression untouched-green.
**Committed locally, NOT merged/pushed** — awaits review (rules 02/05).

## Recent decisions
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
- Exact Groq model id ("Qwen 27B") still unverified vs Groq model list.
- CHANGELOG regeneration tooling still undecided; file remains [Unreleased]-empty (never
  hand-edited per rule).
- Three Dependabot PRs open (actions bumps). No frontend CI steps yet.
- Parked branch `feature/frontend-bootstrap` deletion needs explicit user confirmation (rule 05).

## Next step
With approval: merge `feature/frontend-rebuild` → main, tag (no tags exist yet; suggest v0.3.0),
push; optionally delete the parked bootstrap branch after that confirmation. Then Roadmap
Next-v2 (Supabase persistence behind a SessionStore protocol seam) in a FRESH session per
06-session-efficiency — which also unblocks Now §3/§4 (shared sessions + safe follow-ups).

