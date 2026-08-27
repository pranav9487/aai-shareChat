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

### 4. Implement Safe Follow-Up Handling
- Detect follow-up questions.
- Rewrite follow-up questions into standalone questions when required.
- Perform retrieval according to the current user's access permissions.
- Return a security-based response when information cannot be answered due to access restrictions.

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

#### v2. Integrate Supabase

* Store conversation history.
* Store shared session information.
* Store user-related data required for the project.
* Track conversation messages with the associated `user_id`, role, and session information.
* Use the stored data to support shared-session testing and safe follow-up handling.

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