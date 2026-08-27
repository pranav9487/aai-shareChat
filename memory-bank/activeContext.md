# Active Context

<!-- Update this at the end of every session. This is the first thing to read when resuming. -->

## Current focus
Roadmap Next-v2 (Supabase persistence) IMPLEMENTED on branch
`feature/supabase-persistence` (off main): `SupabaseSessionStore` +
`SupabaseUserDirectory` behind the existing protocol seams, selected by
`resolve_supabase_client` (both env vars set → durable; blank → in-memory;
half-set → fail-fast). Schema ready in `supabase/schema.sql` — **user must
create a Supabase project, run that SQL once, and fill SUPABASE_URL +
SUPABASE_SERVICE_KEY in `.env` to activate durability**; until then behavior
is unchanged (in-memory). Conformance suite proves both store implementations
are behaviorally identical. Full suite + lint green. ADR-0008. **Committed
locally, NOT merged/pushed — awaits review (rules 02/05).**
After merge: remaining roadmap work is Now §4 (safe follow-up handling — the
message rows already store exactly what it needs) and Next v3 (wire the
frontend transcript panel to `/api/sessions/{id}`).

## Recent decisions
- ADR-0008: Supabase persistence behind the `SessionStore`/`UserDirectory`
  protocol seams; service-role key server-side (RBAC visibility filter stays
  the security layer, RLS out of scope); selection in deps with fail-fast on
  half-set config; conformance suite pins both store implementations to
  identical behavior.
- ADR-0006: session persistence lives behind a `SessionStore` protocol seam
  (in-memory + Supabase now) mirroring `UserDirectory` (ADR-0004); open
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
- RESOLVED 2026-08-27: shell works, `GROQ_API_KEY` present, `GROQ_MODEL` verified as
  `qwen/qwen3.6-27b`, nexora corpus ingested into the Pinecone index `internal-docs`
  (28 docs / 31 chunks + the earlier demo corpus; both corpora coexist in the index).
- `feature/shared-sessions` branch vs main overlap: main already contains session
  store/visibility + session_id requirement (user commits); review the branch for any
  remaining delta before merging or deleting it (needs explicit user OK, rule 05).
- Old demo corpus and nexora corpus both live in the same Pinecone index; consider a
  single canonical corpus + re-ingest policy later.
- Dependabot CI bumps still pending; frontend transcript panel not yet wired to the
  `/api/sessions/{id}` route.
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

