# FEATURE PROMPT: Roadmap Item 1 — Core RAG Pipeline

Follow the `/new-feature` workflow (.clinerules/workflows/new-feature.md) exactly:
branch → implement → test → lint → self-review → commit → update memory-bank.
Do NOT push. Do NOT implement items 2–4 (access control, shared sessions, follow-ups).

## CONTEXT (read first)
- Project: secure employee RAG chat; V1 = single-agent. Primary doc: memory-bank/projectBrief.md
- Scope source: ROADMAP.md "Now" §1 ONLY.
- Architecture target: memory-bank/architecture.md ("Intended Folder Structure").
- Stack: memory-bank/tech-stack.md. Repo currently has NO code — this feature bootstraps the backend.
- Rules: .clinerules/01-security.md (secrets), 03-testing.md (adversarial tests),
  04-code-quality-review.md, 05-git-workflow.md, 02-commit-style.md.

## RESOLVED DEFAULTS FOR "TBD" ITEMS (record each as an ADR in docs/adr/, then fill tech-stack.md)

| TBD item        | Default to use                                    | Why |
|-----------------|---------------------------------------------------|-----|
| Package manager | pip + requirements.txt (repo root)                | matches CI INSTALL_CMD |
| Test framework  | pytest, tests in backend/tests/                   | matches CI TEST_CMD |
| Lint / format   | ruff check . / black .                            | matches CI |
| Embeddings      | ChromaDB default embedding function (MiniLM ONNX) | free, local, no extra API key |
| Groq model id   | env var GROQ_MODEL, default qwen/qwen3-32b        | verify against current Groq model list; exact "Qwen 27B" id is TBD — parameterize, never hardcode |

If a default proves unworkable, stop that sub-step, state why, propose alternative, continue with
fallback only if reversible.

## SCOPE — IN
1. Bootstrap `backend/` per the intended folder structure (only folders needed below).
   - app/main.py (minimal FastAPI app), app/config/settings.py (pydantic-settings reading .env).
   - Create `.env.example` (GROQ_API_KEY=, GROQ_MODEL=, CHROMA_PERSIST_DIR=./chroma_db,
     DOCUMENTS_DIR=./documents/generated_test_documents) and ensure `.gitignore` blocks `.env`.
2. Test-document generator: `documents/generate_test_documents.py` → deterministic markdown docs
   across 4 access tiers (general / hr / restricted / management), ≥3 docs per tier, written to
   documents/generated_test_documents/. Front-matter metadata MUST include `access_level`.
   NOTE: tiers are data-only scaffolding now; enforcement lands in item 2 — do NOT build RBAC.
3. Ingestion service (app/services/rag/ingestion.py): load docs → chunk (~800 chars, ~100 overlap,
   constants in config) → embed via Chroma default embeddings → persist to ChromaDB collection
   with metadata {source, access_level, chunk_index}. Idempotent: re-ingest replaces same-source chunks.
4. Vector store wrapper (app/vectorstore/chroma_client.py): single shared client factory;
   add/query/persist/count; no business logic inside.
5. Retrieval service (app/services/rag/retriever.py): top_k configurable (default 5);
   returns chunks + metadata + distances; NO access filtering yet (add TODO(item-2) marker).
6. Generation chain (app/services/llm/groq_chain.py): LangChain chain using ChatGroq(model=GROQ_MODEL),
   API key from env only; system prompt: answer ONLY from provided context, say "not found in
   documents" otherwise; pass retrieved chunks as context.
7. Pipeline facade (app/services/rag/pipeline.py): query(text) -> {answer, sources[]}.
8. Thin dev-only endpoint POST /api/dev/query marked
   "# PRE-AUTH DEV STUB — replaced by items 2–3" so the pipeline is exercisable.

## SCOPE — OUT (do not build, do not stub beyond markers above)
User IDs, roles, permission checks, session/conversation persistence (Supabase), follow-up
rewriting, streaming, frontend, Docker, deployment.

## ARCHITECTURE RULES
- Layered: routes → pipeline → retriever/generator → chroma_client. Routes never touch Chroma directly.
- All LLM/embedding clients injectable (constructor params / dependency injection) so tests can mock.
- No network call may occur inside a plain unit test (see Testing).
- Config exclusively via pydantic-settings + .env; zero hardcoded keys/URLs (rule 01-security).
- Minimal targeted code only; boring > clever; type hints throughout; docstrings on public functions.

## TESTING (rule 03-testing — adversarial, full suite must pass)
- Unit (mocked, run always): chunker boundaries (empty doc, tiny doc, huge doc, unicode, no sentence
  breaks); ingestion idempotency (double ingest ≠ duplicate chunks); retriever top_k=0/negative/
  k>corpus; chain prompt assembly with empty retrieval result; facade error propagation.
- Integration (marked @pytest.mark.integration, auto-skipped unless GROQ_API_KEY set):
  ingest generated docs → tier-targeted queries retrieve expected access_level docs → answer cites sources.
- CI safety: `pytest` alone (no API key) must pass 100% — mocks required, integration skips cleanly.
- pytest config in root pyproject.toml; requirements.txt pinned version ranges.

## EXECUTION STEPS (in order)
1. git checkout -b feature/rag-pipeline
2. Scaffold backend + .env.example + .gitignore check
3. Write ADRs (0002 embeddings choice, 0003 model/tooling defaults) + update tech-stack.md TBDs
4. Implement in this order: config → chroma_client → chunker/ingestion → retriever → groq_chain →
   pipeline → route → main
5. Generate test documents; verify counts on disk
6. Tests per section above; run FULL suite: pytest
7. ruff check . && black . (fix ALL warnings)
8. Self-review diff vs rule 04-code-quality-review.md (secrets, error handling, dead code, duplication)
9. Commit (Conventional Commits, e.g. feat(rag): add core ingestion-retrieval-generation pipeline)
10. Update memory-bank/progress.md (Done: rag pipeline …), activeContext.md (next: item 2 access control),
    move ROADMAP.md §1 out of "Now". CHANGELOG regenerates later via /commit — do not hand-edit.
11. Summarize in plain English; state ready-for-review; DO NOT push/merge.

## DEFINITION OF DONE CHECKLIST
- [ ] Feature branch exists, working tree committed clean
- [ ] Full pytest suite green without API key
- [ ] Generated docs exist (12+, 4 tiers)
- [ ] Query round-trip works locally end-to-end
- [ ] ruff + black clean
- [ ] No secrets in diff; .env ignored; .env.example present
- [ ] ADRs written; tech-stack.md TBDs resolved
- [ ] progress/activeContext/ROADMAP updated
- [ ] Out-of-scope features absent
- [ ] Plain-English summary delivered, not pushed

