# System Patterns

<!-- Fill in as patterns emerge, so every session follows the same conventions instead of inventing new ones. -->

## Naming conventions
- Python: snake_case modules/functions, PascalCase classes, UPPER_SNAKE constants; enums are
  `StrEnum`; tests are `test_<behavior>()` in `backend/tests/test_<unit>.py`.
- Git: branches `feature/<name>` / `fix/<name>`; Conventional Commits `type(scope): summary`.

## Folder structure logic
- Layered backend: `api/routes` → `api/deps` (composition root) → `services/*` → `vectorstore/`.
- One concern per service package (`rag`, `llm`, `access_control`); tests sit flat in
  `backend/tests/` mirroring units, sharing fakes from `conftest.py`.

## Common patterns used in this project
- Dependency injection everywhere: embedders/stores/generators/directories arrive as constructor
  params or FastAPI `Depends`; unit tests inject fakes (FakeEmbedder, StubRetriever,
  RecordingGenerator, InMemoryUserDirectory) — plain unit tests never touch network/ONNX/Groq.
- FastAPI providers live in `app/api/deps.py` as `@lru_cache` factories; tests swap them via
  `app.dependency_overrides`.
- Session layer (item 3): `SessionStore` protocol + `InMemorySessionStore` in
  `app/services/session/`; `GET /api/sessions/{id}` runs a read-time visibility
  filter (`visible_messages`) that hides a non-author's answer unless every
  `access_level` it drew from is within the viewer's tiers — content that
  cannot be shared is replaced with a non-leaky placeholder, never shown.
- Canonical user-facing sentences are module constants shared by prompt/pipeline/tests
  (`NOT_FOUND_ANSWER`, `ACCESS_DENIED_ANSWER`, `HIDDEN_MESSAGE`).
- Vocabulary types are `StrEnum` with one mapping table (`ROLE_ALLOWED_TIERS`); ingestion's
  `ALLOWED_ACCESS_LEVELS` must stay identical to `AccessTier` values (test-enforced).
- Config only via pydantic-settings + root `.env` (mirror in `.env.example`); bad seeds fail fast.
- Security posture: permissions filter INSIDE the vector-store query (`access_level` `$in` filter applied server-side), denial
  responses expose no sources/content, auth error details are fixed and non-leaky.

## Things to avoid
- Routes touching Pinecone/LangChain directly (always through the pipeline facade).
- Hardcoding model ids/keys/URLs or silently defaulting unknown access levels.
- Reusing retrieved context across users/sessions — the core project invariant.
- Hand-editing CHANGELOG.md; committing `generated_test_documents/`, `.venv/`, or logs.
- Letting plain unit tests hit the hosted vector store (Pinecone) — use `InMemoryVectorStore` (ADR-0007).
