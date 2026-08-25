# ADR-0003: Tooling defaults (pip/pytest/ruff/black) + Groq model parameterization

## Status
Accepted

## Date
2026-08-25

## Context
tech-stack.md left package manager, test framework, lint/format tools and the exact Groq
model id as TBD. The repo's CI template already hardcodes `pip install -r requirements.txt`,
`ruff check .`, `black --check .`, `pytest`, Python 3.11 — filling the TBDs with anything else
would force CI changes for no benefit.

## Decision
1. Adopt pip (`requirements.txt`), pytest (`backend/tests/`), ruff, black exactly as CI expects.
   Config lives in a root-level `pyproject.toml`; this deliberately deviates from
   memory-bank/architecture.md's tree, which placed `requirements.txt` under `backend/` — CI runs
   from the repo root, so the file must be at the root. Architecture doc updated accordingly.
2. LangChain is pulled in via `langchain-core` + `langchain-groq` (no bare `langchain` meta-package;
   nothing in item 1 uses it).
3. The Groq model id is never hardcoded: it comes from the `GROQ_MODEL` env var with placeholder
   default `qwen/qwen3-32b`. The project spec's "Qwen 27B" has no confirmed public Groq identifier,
   so the exact value stays a one-line `.env` change after verifying Groq's model list.

## Alternatives considered
- poetry/uv — nicer lockfiles but require changing CI INSTALL_CMD; revisit if dependency conflicts appear.
- Hardcoding a model id — rejected: violates the "exact id is TBD" constraint and 01-security spirit
  of keeping service configuration out of source.

## Consequences
Zero CI edits needed today; commands are identical locally and in CI. If pip resolution ever gets
painful, migrating to uv is contained to requirements.txt → pyproject + one CI env var.
