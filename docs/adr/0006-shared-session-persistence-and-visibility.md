# ADR-0006: Shared-session persistence and read-time visibility filtering

## Status
Accepted

## Date
2026-08-27

## Context
Roadmap item 3 requires a *shared* session: multiple users in one
conversation, where the system must "prevent information retrieved for one
user from automatically being exposed to another user." Before this ADR the
backend was stateless — the frontend already sent a per-visit ``session_id``
that the query schema silently ignored (ADR-0005 noted it as dormant). The
leak vector item 3 guards against only exists once a session starts collecting
message history, so persistence and the safety filter must land together.

## Decision
1. **``SessionStore`` protocol behind a seam (mirrors `UserDirectory`, ADR-0004).**
   V1 ships ``InMemorySessionStore`` (thread-safe, per-process, not durable);
   a Supabase-backed implementation planned for roadmap Next-v2 implements the
   same protocol, so call sites do not change.
2. **Every ``POST /api/query`` now requires (and logs against) ``session_id``.**
   Each exchange stores: author ``user_id``, author ``role``, the question, the
   answer, the answer's sources, and the set of document ``access_level``s the
   answer actually drew from (derived from source chunk metadata).
3. **Live retrieval never reuses stored context.** The pipeline still runs a
   fresh, permission-filtered query per request; stored messages are only
   *read* through the visibility filter below. This enforces the invariant
   "do not reuse one user's retrieved chunks for another user."
4. **Read-time visibility filter.** ``GET /api/sessions/{id}`` returns the
   transcript filtered per the requesting viewer: a message is visible if the
   viewer authored it, if the answer drew from no restricted tiers (not-found /
   security-decline), or if every tier it drew from is within the viewer's
   permitted tiers. Non-visible answers are replaced with a canonical
   non-leaky placeholder and their sources emptied; the question (the
   viewer-typed prompt, not retrieved content) is kept.

## Alternatives considered
- Supabase persistence now — rejected (same rationale as ADR-0004): infra
  coupling before load, reversible later behind the protocol seam.
- Membership-gated sessions (explicit join) — rejected for v1: open membership
  plus the per-viewer visibility filter already satisfies the requirement, and
  the filter is the actual guard.
- Hiding the whole message (question included) when not visible — rejected:
  the question is the viewer's own prompt, not retrieved content; keeping it
  makes the shared session readable while the answer stays strictly filtered.

## Consequences
New in-memory state exists per process; restarting the server clears sessions
(acceptable until Supabase). The visibility rule is a deliberately strict,
content-tag-driven subset check — a message is only shared to the extent its
answer drew within the viewer's own tiers, so nothing beyond that leaks. Adding
durability or a roles-list endpoint later does not change the filter's call
sites.