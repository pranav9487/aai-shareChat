# ADR-0007: Replace ChromaDB with Pinecone as the vector store

## Status
Accepted

## Date
2026-08-27

## Context
Roadmap item 1 built the vector store on ChromaDB (persistent, local) per
ADR-0002. ChromaDB is embedded/local; the project intends a hosted,
production-oriented retrieval backend, and a decision was made to move document
storage to a managed vector database. A second, independent constraint drove
the storage abstraction: ChromaDB runs locally, so unit tests could (and did)
touch it directly, whereas the target store is hosted and therefore must never
be reached from a plain unit test.

## Decision
1. **Swap the vector store to Pinecone (serverless).** A new
   ``PineconeVectorStore`` (``app/vectorstore/pinecone_client.py``) implements
   the same contract as the old Chroma store. Construction is lazy/offline (no
   index connect until the first upsert/query/count), which keeps the FastAPI
   composition root network-free at build time.
2. **Introduce a vendor-agnostic ``VectorStore`` protocol** in
   ``app/vectorstore/base.py`` holding ``EmbedFn``, ``RetrievedChunk`` and the
   ``delete_source/upsert_chunks/query/count`` surface. All consumers
   (retriever, ingestion, pipeline, Groq chain, deps, main) now type against
   the protocol, so the store stays swappable.
3. **Offline tests move to an in-memory store** (``test/inmemory``
   ``InMemoryVectorStore``) implementing the same protocol with the existing
   deterministic fake embedder. Real-Pinecone coverage lives only in the
   key-gated integration test (auto-skipped without ``PINECONE_API_KEY``).
4. **Keep local MiniLM-L6-v2 embeddings via FastEmbed** (ONNX, 384-dim, no
   torch) in ``DefaultEmbedder``, replacing ChromaDB's bundled embedder so the
   ``chromadb`` dependency is fully removed. The Pinecone index is created with
   ``dimension=384`` and ``metric="cosine"``.
5. **Access filtering maps 1:1.** Pinecone supports the same
   ``{"access_level": {"$in": [...]}}`` metadata filter as ChromaDB's ``where``,
   so RBAC enforcement stays server-side (forbidden chunks never leave the
   store).
6. **Distance semantics preserved.** Pinecone cosine *score* (higher = closer)
   is mapped to ``distance = 1 - score`` (lower = closer), keeping the retriever
   contract (nearest-first ascending distance) identical.

## Alternatives considered
- Keep ChromaDB — rejected: it cannot satisfy the hosted/managed retrieval
  requirement that motivated the change, and its local/persistent nature is
  undesirable in production.
- Use Pinecone's hosted embedding model — rejected: adds egress of internal
  documents to an embedding API and extra cost; the existing local MiniLM
  (ADR-0002) already gives adequate 384-dim vectors free.
- Write unit tests against a live Pinecone index — rejected (rule 03): plain
  tests must never make network calls; the in-memory store preserves coverage
  with identical semantics.

## Consequences
No source dependency on ``chromadb`` remains (the old module is a deprecated
re-export shim). Tests run fully offline and green without any key. Going live
requires a ``PINECONE_API_KEY`` (and Groq key); until then the app start and
unit suite remain key-independent. Retrieval now depends on network latency to
Pinecone, and the integration test needs a unique throwaway index per run.
