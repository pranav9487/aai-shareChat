# ADR-0005: Frontend stack — React 18 in JavaScript via Vite/npm/Vitest

## Status
Accepted (supersedes the abandoned TypeScript attempt on parked branch
`feature/frontend-bootstrap`, which was discarded by product decision — the
TS toolchain changed the project's stack more than the UI warranted)

## Date
2026-08-26

## Context
Roadmap Next-v1 needs a React frontend. A previous implementation used
TypeScript strict mode; it was rejected because the type layer added ceremony
(`tsconfig`, `@types/*`, tsc gate) disproportionate to a demo chat UI. The
user directed a JavaScript rebuild.

## Decision
1. **React 18 in plain JavaScript + JSX** — components are `.jsx`; shared
   shapes are documented with light JSDoc instead of interfaces. No
   `@types/*`, no tsconfig.
2. **Vite** dev/build server; `/api` is proxied to `127.0.0.1:8000` so the
   FastAPI backend needs no CORS middleware.
3. **npm** as package manager; lockfile committed for reproducibility.
4. **Vitest + React Testing Library + jsdom** for offline component tests
   (rule 03); **ESLint 9 (flat config, js-recommended + react-hooks)** is the
   lint gate that replaces the removed tsc check.
5. No router/state/UI libraries: single page, `useState`, plain CSS.
6. Demo users mirrored client-side from the backend seed registry (+ custom
   id/role override) until a users-list endpoint or Supabase exists; drift is
   documented in code comments.
7. The canonical security-decline sentence is mirrored as a JS constant
   pointing at ``ACCESS_DENIED_ANSWER`` in
   ``backend/app/services/rag/pipeline.py``; declines render as a distinct
   styled security notice.
8. ``session_id`` (crypto.randomUUID per page visit) is sent on every request;
   the backend schema ignores extra fields today and Supabase (Next-v2) will
   give it real semantics.

## Alternatives considered
- Keeping TypeScript — rejected by product owner: ceremony > value here.
- No-build React via CDN/htm — rejected: loses offline tests and JSX, pins to
  CDN availability.
- Vanilla-JS static files served by FastAPI — viable fallback, but drops the
  requested React learning value and makes chat-thread state harder to test.
- Jinja server-side rendering — rejected: async chat updates degrade to page
  reloads.

## Consequences
Fastest path to the ROADMAP Next-v1 outcomes with the smallest cognitive
surface. API contract checking moves from compile time to tests; ESLint +
tests become the quality gates. If the project ever outgrows this, migrating
the same components to TS is mechanical.
