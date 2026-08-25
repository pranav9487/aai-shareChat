# Active Context

<!-- Update this at the end of every session. This is the first thing to read when resuming. -->

## Current focus
Roadmap item 1 (RAG pipeline) fully implemented on branch `feature/rag-pipeline`. Verification
(pytest / ruff / black) could NOT be run because the agent environment had no working shell or git;
the suite is written but unexecuted. Treat "green" as unconfirmed until you run it locally.

## Recent decisions
- Embeddings: ChromaDB default MiniLM (ONNX) behind injectable `EmbedFn` — ADR-0002.
- Tooling locked to CI defaults: pip + root `requirements.txt`, pytest, ruff, black — ADR-0003.
  Deviation from architecture.md tree: `requirements.txt` + `pyproject.toml` live at REPO ROOT so
  CI's `INSTALL_CMD`/`TEST_CMD` work unchanged from the workspace root.
- `GROQ_MODEL` env var with placeholder default `qwen/qwen3-32b`; exact "Qwen 27B" id still to verify.
- `POST /api/dev/query` is an explicitly marked PRE-AUTH dev stub; replaced by items 2–3.
- Chunker: window splitter, boundary-snapping (\n\n → ". " → space), overlap via window step.

## Blockers / open questions
- Exact Groq model identifier for "Qwen 27B" — verify against Groq's current model list.
- Shell/git unavailable in agent sandbox this session → tests, lint, and commits must be run manually.

## Next step
At repo root run: `pip install -r requirements.txt`, then `pytest`, then `ruff check .`, then
`black --check .`. Fix anything red. Generate docs with `python documents/generate_test_documents.py`.
After green: commit on `feature/rag-pipeline` per 02-commit-style.md, then start Roadmap item 2
(access control) in a fresh session.

