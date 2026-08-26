# ADR-0004: Access control identity source, RBAC mapping, and denial semantics

## Status
Accepted

## Date
2026-08-26

## Context
Roadmap item 2 requires user identification, role-based access control, and
permission-filtered retrieval. The intended production home for users/roles is
Supabase (memory-bank/tech-stack.md), but wiring a database now would couple
item 2 to infrastructure before sessions/conversations (items 3–4) exist.

## Decision
1. Identity arrives per request as an ``X-User-ID`` header, resolved through a
   ``UserDirectory`` protocol. V1 ships ``InMemoryUserDirectory`` seeded from
   built-in demo users, overridable via the ``ACCESS_CONTROL_SEED_JSON``
   setting. Supabase later implements the same protocol — call sites do not
   change.
2. Roles map to document access tiers (the same four strings ingestion stores
   in chunk metadata): employee → {general}; hr → {general, hr}; manager →
   {general, management}; executive → all four. Enforcement happens inside the
   vector-store query (Chroma ``where`` filter on ``access_level``), so
   unauthorized chunks are never retrieved rather than filtered after the fact.
3. When permission-filtered retrieval is empty, the pipeline performs ONE
   internal unfiltered existence probe (content discarded) to choose between
   the canonical security decline ("access denied …") and the canonical
   not-found answer. Both are application-level 200 responses: the brief
   requires a *security-based response*, and distinguishing denial from
   not-found is explicitly requested behavior, while chunk contents and source
   names of forbidden material are never exposed.

## Alternatives considered
- Supabase auth + DB-backed directory immediately — rejected for v1: infra
  coupling, slower iteration; reversible later because of the protocol seam.
- Post-retrieval filtering in Python — rejected: chunks would leave the store
  before a permission check, a larger blast radius for leakage bugs.
- Always answer not-found when denied — rejected: the project brief explicitly
  requires a distinguishable security-based response.

## Consequences
Zero new infrastructure; tests run fully offline with fake directories. The
existence-probe reveals only whether restricted material matches a query,
which the brief accepts. Adding a role or tier is a one-line table change plus
tests.
