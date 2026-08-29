"""Document parsing, chunking, and ingestion into the vector store."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from app.config.settings import Settings, get_settings
from app.vectorstore.base import VectorStore

ALLOWED_ACCESS_LEVELS = ("general", "hr", "restricted", "management")

_FRONT_MATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?(.*)\Z", re.DOTALL)


@dataclass(frozen=True)
class ParsedDocument:
    """A parsed source document ready for chunking."""

    source: str  # file name; used as the idempotency key in the vector store
    title: str
    access_level: str
    text: str


def chunk_text(text: str, *, chunk_size: int = 800, chunk_overlap: int = 100) -> list[str]:
    """Split *text* into overlapping chunks of at most ``chunk_size`` characters.

    Uses LangChain's RecursiveCharacterTextSplitter for optimal semantic boundaries.
    """
    if chunk_size <= 0:
        raise ValueError(f"chunk_size must be positive, got {chunk_size}")
    if not 0 <= chunk_overlap < chunk_size:
        raise ValueError(
            "chunk_overlap must satisfy 0 <= overlap < size, "
            f"got {chunk_overlap} for size {chunk_size}"
        )
    cleaned = text.strip()
    if not cleaned:
        return []

    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )

    return splitter.split_text(cleaned)


def parse_markdown_document(path: Path) -> ParsedDocument:
    """Parse a markdown file that starts with simple ``key: value`` front matter.

    Raises ``ValueError`` for malformed front matter or a missing/unknown
    ``access_level`` — silently defaulting access levels would be unsafe once
    role enforcement lands (item 2).
    """
    raw = path.read_text(encoding="utf-8")
    meta: dict[str, str] = {}
    body = raw
    match = _FRONT_MATTER_RE.match(raw)
    if match:
        head, body = match.groups()
        for line in head.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if ":" not in line:
                raise ValueError(f"{path.name}: malformed front-matter line {line!r}")
            key, _, value = line.partition(":")
            meta[key.strip().lower()] = value.strip()

    access_level = meta.get("access_level")
    if not access_level:
        raise ValueError(f"{path.name}: missing required 'access_level' front-matter field")
    if access_level not in ALLOWED_ACCESS_LEVELS:
        raise ValueError(
            f"{path.name}: unknown access_level {access_level!r}; expected one of "
            f"{', '.join(ALLOWED_ACCESS_LEVELS)}"
        )
    return ParsedDocument(
        source=path.name,
        title=meta.get("title", path.stem),
        access_level=access_level,
        text=body.strip(),
    )


class IngestionService:
    """Chunks parsed documents and upserts them into the vector store."""

    def __init__(self, store: VectorStore, settings: Settings | None = None) -> None:
        self._store = store
        self._settings = settings or get_settings()

    def ingest_text(self, doc: ParsedDocument) -> int:
        """Ingest one parsed document; returns the number of chunks written.

        Idempotent: any previously stored chunks from the same source are
        deleted before writing, so re-ingesting never duplicates.
        """
        chunks = chunk_text(
            doc.text,
            chunk_size=self._settings.chunk_size,
            chunk_overlap=self._settings.chunk_overlap,
        )
        self._store.delete_source(doc.source)
        ids = [f"{doc.source}::{i}" for i in range(len(chunks))]
        metadatas = [
            {
                "source": doc.source,
                "access_level": doc.access_level,
                "title": doc.title,
                "chunk_index": i,
            }
            for i, _ in enumerate(chunks)
        ]
        return self._store.upsert_chunks(chunks, metadatas, ids)

    def ingest_directory(self, directory: Path | str) -> dict[str, object]:
        """Ingest every ``*.md`` file under *directory*.

        Returns ``{"files", "chunks", "skipped", "errors"}``; per-file parse
        errors are collected instead of aborting the whole run.
        """
        directory = Path(directory)
        summary: dict[str, object] = {"files": 0, "chunks": 0, "skipped": [], "errors": {}}
        errors: dict[str, str] = {}
        skipped: list[str] = []
        files_ingested = 0
        total_chunks = 0
        for path in sorted(directory.glob("*.md")):
            try:
                doc = parse_markdown_document(path)
            except ValueError as exc:
                errors[path.name] = str(exc)
                continue
            if not doc.text.strip():
                skipped.append(path.name)
                continue
            total_chunks += self.ingest_text(doc)
            files_ingested += 1
        summary["files"] = files_ingested
        summary["chunks"] = total_chunks
        summary["skipped"] = skipped
        summary["errors"] = errors
        return summary


def ensure_corpus(store: VectorStore, settings: Settings | None = None) -> dict[str, object] | None:
    """Ingest the configured corpus once if the collection is still empty.

    Keeps the demo self-provisioning: an empty Pinecone index becomes
    answerable after the first server start, with no manual ingest step.
    Idempotent — a populated index is never touched (explicit re-ingestion
    remains a manual operation).

    Returns the ingestion summary, or ``None`` when nothing was done
    (already populated, or the documents directory does not exist).
    """
    resolved = settings or get_settings()
    if store.count() > 0:
        return None
    docs_dir = Path(resolved.documents_dir)
    if not docs_dir.is_dir():
        return None
    return IngestionService(store, resolved).ingest_directory(docs_dir)
