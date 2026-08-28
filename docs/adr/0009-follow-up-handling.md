# ADR-0009: Safe Follow-Up Handling (Roadmap Now §4)

Date: 2026-08-27
Status: Accepted

## Context

In a shared session, a user may follow up on their own question with a
deictic or elliptical remark ("How many vacation days do employees get?" →
"what about part-time?" / "and their leave?"). Sending the raw follow-up to
retrieval fails because it carries no standalone subject. Roadmap Now §4
requires detecting follow-ups, rewriting them into standalone questions, and
still honoring the requester's access permissions (which the existing
permission-filtered retrieval already enforces).

## Decision

- **A `FollowUpResolver` protocol seam**, mirroring `SessionStore`
  (ADR-0006/0008) and `UserDirectory` (ADR-0004): one deterministic, offline
  `HeuristicFollowUpResolver` now; an LLM-based condense step can slot in later
  behind the same interface. No new dependencies.
- **Detection is rule-based**: a question is a follow-up when it is short and
  contains a deictic pronoun/connector (`it/this/that/these/those/they/them/
  their/there`) or starts with an elliptical opener (`and/also/then/but/what
  about/how about/too`). Deterministic and testable.
- **Rewrite inlines only the requester's own prior question**: `f"{prior} 
  {follow_up}"` (e.g. "How many vacation days do employees get? what about
  part-time?"). This restores the dropped subject into the embedding query
  without touching another user's content.
- **Cross-user safety is structural**: the route builds the rewrite history
  *only* from messages where `sender_user_id == user.user_id`. The resolver
  never sees another participant's questions, answers, or sources, so foreign
  or restricted content is never surfaced. Retrieval still runs fresh with
  the requester's `allowed_levels`; the existing security-decline
  (`ACCESS_DENIED_ANSWER`) and not-found paths are preserved for rewritten
  questions alike.
- **The original question is logged to the session** (what the user typed),
  while the resolved question drives retrieval/answer. This keeps the shared
  transcript faithful and the visibility filter unchanged.

## Consequences

- Follow-ups now answer correctly and safely; non-follow-ups are byte-identical
  pass-throughs (no LLM, no rewrite).
- Rewritten queries that target restricted content still return the canonical
  security-decline rather than leaking content.
- The heuristic maximizes determinism over fluency; an LLM condense step can
  later replace the resolver behind the same protocol.