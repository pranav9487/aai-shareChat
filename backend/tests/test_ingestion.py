"""Adversarial tests for front-matter parsing and ingestion."""

from __future__ import annotations

from pathlib import Path

import pytest
from app.config.settings import Settings
from app.services.rag.ingestion import (
    IngestionService,
    ParsedDocument,
    parse_markdown_document,
)

from documents.generate_test_documents import DOCUMENTS, build_markdown, write_documents

MULTI_CHUNK_TEXT = "".join(
    f"Paragraph {i} sentence one. Sentence two adds detail.\n\n" for i in range(80)
)


def make_settings(tmp_path: Path) -> Settings:
    return Settings(
        chroma_persist_dir=tmp_path / "db",
        documents_dir=tmp_path / "docs",
        chunk_size=500,
        chunk_overlap=50,
    )


def test_parse_rejects_missing_access_level(tmp_path: Path) -> None:
    doc = tmp_path / "doc.md"
    doc.write_text("# No front matter\n\nJust body text.", encoding="utf-8")
    with pytest.raises(ValueError, match="access_level"):
        parse_markdown_document(doc)


def test_parse_rejects_unknown_access_level(tmp_path: Path) -> None:
    doc = tmp_path / "doc.md"
    doc.write_text("---\ntitle: X\naccess_level: secret\n---\n\nBody.", encoding="utf-8")
    with pytest.raises(ValueError, match="unknown access_level"):
        parse_markdown_document(doc)


def test_parse_rejects_malformed_front_matter_line(tmp_path: Path) -> None:
    doc = tmp_path / "doc.md"
    doc.write_text("---\ntitle X without colon\n---\n\nBody.", encoding="utf-8")
    with pytest.raises(ValueError, match="malformed front-matter"):
        parse_markdown_document(doc)


def test_parse_happy_path(tmp_path: Path) -> None:
    doc = tmp_path / "memo.md"
    doc.write_text(build_markdown("Memo Title", "hr", "Body text."), encoding="utf-8")
    parsed = parse_markdown_document(doc)
    assert isinstance(parsed, ParsedDocument)
    assert parsed.source == "memo.md"
    assert parsed.title == "Memo Title"
    assert parsed.access_level == "hr"
    assert parsed.text == "Body text."


def test_ingest_is_idempotent(store, tmp_path: Path) -> None:
    service = IngestionService(store, make_settings(tmp_path))
    doc = ParsedDocument(
        source="big.md", title="Big", access_level="general", text=MULTI_CHUNK_TEXT
    )
    first_count = service.ingest_text(doc)
    assert first_count >= 2, "test text should produce multiple chunks"

    second_count = service.ingest_text(doc)
    assert second_count == first_count
    assert store.count() == first_count, "re-ingest must replace, not duplicate"


def test_ingest_stores_expected_metadata(store) -> None:
    from app.services.rag.retriever import Retriever

    doc = ParsedDocument(
        source="hr_memo.md",
        title="HR Memo",
        access_level="hr",
        text="Vacation days accrue monthly. Managers approve leave. " * 30,
    )
    IngestionService(store).ingest_text(doc)
    results = Retriever(store, top_k=3).retrieve("vacation days accrual approval")
    assert results, "expected at least one hit"
    for chunk in results:
        assert chunk.metadata["source"] == "hr_memo.md"
        assert chunk.metadata["access_level"] == "hr"
        assert chunk.metadata["title"] == "HR Memo"
        assert "chunk_index" in chunk.metadata


def test_ingest_directory_ingests_all_generated_documents(store, tmp_path: Path) -> None:
    docs_dir = tmp_path / "docs"
    write_documents(docs_dir)
    summary = IngestionService(store, make_settings(tmp_path)).ingest_directory(docs_dir)

    assert summary["files"] == len(DOCUMENTS) == 12
    assert summary["chunks"] >= len(DOCUMENTS)
    assert summary["errors"] == {}
    assert summary["skipped"] == []
    assert store.count() == summary["chunks"]


def test_ingest_directory_collects_errors_without_aborting(store, tmp_path: Path) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir(parents=True)
    good = docs_dir / "good.md"
    bad = docs_dir / "bad.md"
    empty = docs_dir / "empty.md"
    good.write_text(
        build_markdown("Good", "general", "Useful general content here."), encoding="utf-8"
    )
    bad.write_text("no front matter at all", encoding="utf-8")
    empty.write_text(build_markdown("Empty", "restricted", ""), encoding="utf-8")

    summary = IngestionService(store, make_settings(tmp_path)).ingest_directory(docs_dir)
    assert summary["files"] == 1
    assert set(summary["errors"]) == {"bad.md"}
    assert summary["skipped"] == ["empty.md"]
    assert store.count() == summary["chunks"] == 1
