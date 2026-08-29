"""Ingest hierarchical Nexora documents into Pinecone.

Clears ALL existing vectors from the Pinecone index, then ingests
every *.md file in generated_test_documents/ with its front-matter
access_level tag preserved in chunk metadata.

Usage:
    cd backend
    ..\.venv\Scripts\python.exe ../documents/ingest_hierarchical.py
"""

import sys
from pathlib import Path

# Add backend to Python path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT / "backend"))

from app.config.settings import Settings  # noqa: E402
from app.services.rag.ingestion import IngestionService, parse_markdown_document  # noqa: E402
from app.vectorstore.pinecone_client import PineconeVectorStore  # noqa: E402

DOCS_DIR = PROJECT_ROOT / "documents" / "generated_test_documents"


def main():
    if not DOCS_DIR.is_dir():
        print(f"Error: {DOCS_DIR} not found.")
        sys.exit(1)

    settings = Settings()
    store = PineconeVectorStore(
        api_key=settings.pinecone_api_key,
        index_name=settings.pinecone_index_name,
        namespace=settings.pinecone_namespace,
        cloud=settings.pinecone_cloud,
        region=settings.pinecone_region,
        dimension=settings.embedding_dim,
    )

    # --- Step 1: Clear existing vectors ---
    print("Step 1: Clearing existing vectors from Pinecone index...")
    try:
        index = store._ensure()
        # Delete all vectors in the namespace
        index.delete(delete_all=True, namespace=settings.pinecone_namespace)
        print("  All existing vectors deleted.")
    except Exception as exc:
        print(f"  Warning: Could not clear index: {exc}")
        print("  Continuing with ingestion (old sources will be overwritten per-source).")

    # --- Step 2: Parse and ingest documents ---
    print(f"\nStep 2: Ingesting documents from {DOCS_DIR}")
    ingestion = IngestionService(store, settings)

    md_files = sorted(DOCS_DIR.glob("*.md"))
    print(f"  Found {len(md_files)} markdown files.\n")

    tier_summary = {"general": [], "hr": [], "management": [], "restricted": []}
    total_chunks = 0
    errors = []

    for path in md_files:
        try:
            doc = parse_markdown_document(path)
        except ValueError as exc:
            errors.append((path.name, str(exc)))
            print(f"  SKIP  {path.name}: {exc}")
            continue

        chunks = ingestion.ingest_text(doc)
        total_chunks += chunks
        tier_summary[doc.access_level].append((doc.source, doc.title, chunks))
        print(f"  OK    {path.name:50s} [{doc.access_level:12s}] {chunks} chunks")

    # --- Step 3: Summary ---
    print("\n" + "=" * 70)
    print("INGESTION SUMMARY")
    print("=" * 70)

    for tier, docs in tier_summary.items():
        tier_chunks = sum(c for _, _, c in docs)
        print(f"\n  {tier.upper()} ({len(docs)} documents, {tier_chunks} chunks):")
        for source, title, count in docs:
            print(f"    - {title} ({count} chunks)")

    print(f"\n  TOTAL: {sum(len(d) for d in tier_summary.values())} documents, {total_chunks} chunks")

    if errors:
        print(f"\n  ERRORS ({len(errors)}):")
        for name, err in errors:
            print(f"    - {name}: {err}")

    # --- Step 4: Verify ---
    print("\n" + "=" * 70)
    print("VERIFICATION")
    print("=" * 70)

    import time
    print("  Waiting 5 seconds for Pinecone index to sync...")
    time.sleep(5)

    final_count = store.count()
    print(f"  Vectors in Pinecone index: {final_count}")
    print(f"  Expected: {total_chunks}")
    if final_count >= total_chunks:
        print("  ✅ Ingestion verified successfully!")
    else:
        print("  ⚠️  Count mismatch — Pinecone serverless indexes may take a few seconds to reflect.")
        print("     Re-check in 30 seconds or restart the backend server.")


if __name__ == "__main__":
    main()
