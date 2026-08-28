# Roadmap

## Now

### 1. Build the RAG Pipeline — ✅ DONE (2026-08-25, branch `feature/rag-pipeline`)
Implemented: ChromaDB-backed ingestion/retrieval, LangChain + Groq generation chain, FastAPI facade with dev-only query stub, generated company-style test corpus (12 docs × 4 tiers). See memory-bank/progress.md and ADRs 0002–0003.

### 2. Implement Access Control — ✅ DONE (2026-08-26, branch `feature/access-control`)
Implemented: `X-User-ID` identity resolved through a pluggable `UserDirectory` (in-memory seed +
optional `ACCESS_CONTROL_SEED_JSON`), role→tier RBAC enforced inside the ChromaDB `where` filter,
canonical security-decline vs not-found answers, authenticated `POST /api/query` replacing the
pre-auth dev stub. See ADR-0004.
- [x] Support user identification through user ID.
- [x] Apply role-based access control.
- [x] Ensure users only receive information they are permitted to access.

### 3. Implement Shared-Session Safety — ✅ DONE (2026-08-27, branch `feature/shared-sessions`)
Implemented: a `SessionStore` protocol (in-memory today, Supabase later via the
same seam as `UserDirectory`), mandatory per-request identity with every answer
logged to its `session_id`, and a read-time visibility filter on
`GET /api/sessions/{id}` that never leaks another user's retrieved content —
answers are replaced with a non-leaky placeholder unless every tier they drew
from is within the viewer's permissions. Live queries still run fresh
permission-filtered retrieval (never reuse another user's context). See
ADR-0006.
- [x] Support multiple users in a shared session.
- [x] Track user identity for each relevant request.
- [x] Prevent information retrieved for one user from automatically being exposed to another user.

### 4. Implement Safe Follow-Up Handling — ✅ DONE (2026-08-27, branch `feature/follow-up-handling`)

Implemented (ADR-0009): a `FollowUpResolver` protocol seam with a deterministic,
offline `HeuristicFollowUpResolver`. Deictic/elliptical follow-ups ("what about
part-time?" after a vacation question) are detected and rewritten into
standalone questions by inlining **only the requester's own prior question**
(defense-in-depth: the resolver filters by `user_id`, and the route passes
only the caller's history). Rewritten questions still go through the normal
permission-filtered retrieval, so a follow-up targeting restricted content
returns the canonical security decline. The original question the user typed is
always what's logged to the session.
- [x] Detect follow-up questions.
- [x] Rewrite follow-up questions into standalone questions when required.
- [x] Perform retrieval according to the current user's access permissions.
- [x] Return a security-based response when information cannot be answered due to access restrictions.

### 5. Move the vector store to Pinecone — ✅ DONE (2026-08-27, ADR-0007)
Implemented: replaced ChromaDB with a hosted Pinecone (serverless, cosine)
index behind a new vendor-agnostic `VectorStore` protocol
(`app/vectorstore/base.py`); `PineconeVectorStore` (lazy/offline-safe
construction, score→distance mapping, server-side `access_level` `$in`
filter); local MiniLM-L6-v2 embeddings via FastEmbed (no chromadb dependency);
offline unit tests moved to an in-memory store; integration test now key-gated
on `PINECONE_API_KEY` + `GROQ_API_KEY`. See ADR-0007.
- [x] Use Pinecone instead of ChromaDB.
- [x] Add the Pinecone key/config to `.env.example`.
- [x] Keep unit tests 100% green and offline.

### Next

#### v1. Build the React Frontend — ✅ DONE (2026-08-26, branch `feature/frontend-rebuild`)
Implemented: Vite + React 18 + **JavaScript** app (see ADR-0005, which supersedes the discarded
TypeScript attempt parked on `feature/frontend-bootstrap`) with a demo-user picker plus custom
id/role override, an identity-aware chat that posts to `POST /api/query` with the `X-User-ID`
header, distinct rendering for security-based declines, and a per-session `session_id` already
carried in every request (dormant until Next-v2 Supabase). Gates: ESLint clean, 16 offline
Vitest/RTL tests, vite build; dev proxy removes any CORS need on the backend.
- [x] Create a user selection screen for test users.
- [x] Create the chat interface.
- [x] Allow users to select or provide their `user_id` and role.
- [x] Send the `user_id`, role, `session_id`, and message to the FastAPI backend.
- [x] Display AI responses and security-based responses in the chat.

#### v2. Integrate Supabase — ✅ DONE (2026-08-27, branch `feature/supabase-persistence`)

Implemented (ADR-0008): durable persistence behind the existing
`SessionStore`/`UserDirectory` protocol seams — `SupabaseSessionStore` +
`SupabaseUserDirectory` selected in the composition root only when
`SUPABASE_URL` + `SUPABASE_SERVICE_KEY` are both set (half-set config fails
fast; unset keeps the in-memory default so dev/tests stay offline). Schema in
`supabase/schema.sql` (`app_users`, `sessions`, `session_messages` with
sources + access_levels). Conformance tests prove the Supabase store matches
the in-memory store behavior exactly; live round-trip auto-skips without keys.
- [x] Store conversation history.
- [x] Store shared session information.
- [x] Store user-related data required for the project (user IDs, roles).
- [x] Track conversation messages with the associated `user_id`, role, and session information.
- [x] Keep stored data ready to support shared-session testing and safe follow-up handling (§4).

#### v3. Connect Frontend and Backend

* Integrate the React frontend with the FastAPI APIs.
* Ensure user and session information is correctly passed with each request.
* Verify that the frontend correctly displays authorized responses and security-based declines.


## Later / Ideas

No later features have been defined yet.

## Explicitly Not Planned

- Voice input
- File uploads
- Multi-agent algorithms
- Admin dashboard
- Mobile application
- Production deployment