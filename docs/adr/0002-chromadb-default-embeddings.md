# ADR-0002: Use ChromaDB default embeddings for v1

## Status
Accepted

## Date
2026-08-25

## Context
Roadmap item 1 needs document embedding before ChromaDB storage. The project
already requires a Groq API key; adding a second paid API (e.g. OpenAI
embeddings) or another hosted service would add cost and credential surface
for no v1 requirement. memory-bank/tech-stack.md listed the embeddings model
as TBD.

## Decision
Use ChromaDB's built-in default embedding function (all-MiniLM-L6-v2 via
ONNX, downloaded on first use) behind an injectable ``EmbedFn`` callable in
``app/vectorstore/chroma_client.py``.

## Alternatives considered
- OpenAI / hosted embedding APIs — rejected: extra paid key + egress of
  internal documents to another processor.
- sentence-transformers via langchain-huggingface — viable local option, but
  adds a heavy torch dependency for identical MiniLM output at v1 scale.
- No injection seam — rejected: unit tests must run offline and fast.

## Consequences
Zero extra credentials/cost and fast tests (fake embedder injected).
Quality may be insufficient later; swapping means changing one factory call,
since every consumer depends only on the ``EmbedFn`` callable.
