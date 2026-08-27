# ADR-0008: Supabase Persistence for Sessions and Users (Roadmap Next-v2)

Date: 2026-08-27
Status: Accepted

## Context

Roadmap items 3 (shared sessions) and the user directory shipped behind
protocol seams — `SessionStore` (ADR-0006) and `UserDirectory` (ADR-0004) —
with in-memory implementations explicitly marked as the pre-persistence
default. Roadmap Next-v2 requires durable storage for conversation history,
shared-session data, and user records so shared-session testing and future
follow-up handling (§4) survive restarts.

## Decision

- **Supabase (Postgres via postgrest) using the official `supabase` 2.x SDK.**
  The backend is the trusted party and connects with the **service-role key**;
  access enforcement stays in application code (the read-time visibility
  filter and RBAC retrieval filter). Row-level-security policies are
  intentionally out of scope and no anon-key access is used.
- **Schema** (`supabase/schema.sql`, applied once in the SQL editor):
  `app_users(user_id, display_name, role)`, `sessions(session_id, created_at)`,
  `session_messages(id uuid, session_id FK cascade, sender_user_id,
  sender_role, question, answer, sources jsonb, access_levels text[],
  created_at)` — a 1:1 mirror of the domain dataclasses.
- **Selection at the composition root** (`deps.py`): `resolve_supabase_client`
  returns a client when both `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` are set,
  `None` when both are blank (in-memory stores, offline dev/tests), and raises
  on a half-set configuration — broken persistence config fails fast instead
  of silently downgrading.
- **Protocol fidelity over leaky abstraction**: the Supabase implementations
  raise the same exception types (`SessionNotFoundError`,
  `UserNotFoundError`) and return the same frozen domain objects; routes,
  the visibility filter, and tests cannot tell implementations apart. A
  conformance suite parametrizes every store behavior over both.
- **Offline testing**: unit tests inject a fake postgrest client (chainable
  recorder in `conftest.py`); the single live round-trip test auto-skips
  without keys (same gate pattern as the Groq integration test, ADR-0003).
- Client construction is lazy/offline-safe, mirroring the Pinecone adapter.

## Consequences

- Sessions and messages survive restarts; the in-memory implementations remain
  the zero-config default so nothing regresses without credentials.
- Message rows carry `sender_user_id`, `sender_role`, `sources`, and
  `access_levels` — the exact inputs §4 (safe follow-up handling) needs.
- Transient Supabase/network failures at request time surface as 500s rather
  than being masked; retry/fallback behavior is deliberately not added.
- Two corpora demo note: this storage is separate from Pinecone (documents);
  conversation data and document embeddings have independent lifecycles.
