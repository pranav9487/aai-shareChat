import re
import sys
from pathlib import Path

# Add backend to Python path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT / "backend"))

from app.config.settings import Settings  # noqa: E402 - needs sys.path setup above
from app.services.rag.ingestion import IngestionService, ParsedDocument  # noqa: E402
from app.vectorstore.pinecone_client import PineconeVectorStore  # noqa: E402

HANDBOOK_PATH = PROJECT_ROOT / "documents" / "Nexora Technologies Pvt. Ltd.md"
OUTPUT_DIR = PROJECT_ROOT / "documents" / "generated_test_documents"

SECTION_ROLES = {
    1: ("general", "Company Overview"),
    2: ("general", "Working Hours"),
    3: ("general", "Attendance Policy"),
    4: ("general", "Annual Paid Leave"),
    5: ("general", "Sick Leave"),
    6: ("general", "Emergency Leave"),
    7: ("general", "Work From Home Policy"),
    8: ("hr", "Employee Performance Review"),
    9: ("restricted", "Salary Revision"),
    10: ("general", "Annual Bonus Policy"),
    11: ("general", "Employee Benefits"),
    12: ("general", "Health Insurance"),
    13: ("general", "Professional Development"),
    14: ("general", "Travel and Expense Reimbursement"),
    15: ("general", "Promotion Policy"),
    16: ("general", "Internal Job Opportunities"),
    17: ("general", "Notice Period"),
    18: ("general", "Resignation and Exit Process"),
    19: ("general", "Company Assets"),
    20: ("general", "Information Security"),
    21: ("restricted", "Confidential Information"),
    22: ("general", "Employee Code of Conduct"),
    23: ("general", "Grievance and Complaint Process"),
    24: ("general", "Employee Access Levels"),
    25: ("general", "Access-Control Test Cases"),
    26: ("general", "Shared Session Security Test"),
    27: ("general", "Sample Test Users"),
    28: ("general", "Frequently Asked Questions"),
}


def main():
    if not HANDBOOK_PATH.exists():
        print(f"Error: {HANDBOOK_PATH} not found.")
        sys.exit(1)

    print(f"Reading handbook from: {HANDBOOK_PATH}")
    content = HANDBOOK_PATH.read_text(encoding="utf-8")

    # Split by '# ' at start of lines (only top-level "# N. Title" headers,
    # never "## N.N." subsection headers, which keep a double '#').
    sections = re.split(r"\n# ", "\n" + content)

    parsed_docs = []

    for section in sections:
        section = section.strip()
        if not section:
            continue

        # Check if this matches a section number
        match = re.match(r"^(\d+)\.\s+(.*)", section)
        if not match:
            # Might be the title of the document itself or other non-section header
            continue

        sec_num = int(match.group(1))
        sec_content = section

        if sec_num in SECTION_ROLES:
            access_level, title = SECTION_ROLES[sec_num]
            safe_title = title.lower().replace(" ", "_").replace("/", "_")
            file_name = f"nexora_{sec_num:02d}_{safe_title}.md"

            # Format markdown with front matter
            front_matter = f"---\ntitle: {title}\naccess_level: {access_level}\n---\n\n"
            sec_markdown = front_matter + sec_content

            # Write to disk (ensure the corpus directory exists — a clean
            # checkout may not contain it yet).
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            target_path = OUTPUT_DIR / file_name
            target_path.write_text(sec_markdown, encoding="utf-8")
            print(
                f"Wrote section {sec_num} to {target_path.name} "
                f"with access_level: {access_level}"
            )

            parsed_docs.append(
                ParsedDocument(
                    source=file_name, title=title, access_level=access_level, text=sec_content
                )
            )

    if not parsed_docs:
        print("No numbered policy sections found in the handbook; nothing to ingest.")
        sys.exit(1)

    print("\nConnecting to Pinecone...")
    settings = Settings()
    store = PineconeVectorStore(
        api_key=settings.pinecone_api_key,
        index_name=settings.pinecone_index_name,
        namespace=settings.pinecone_namespace,
        cloud=settings.pinecone_cloud,
        region=settings.pinecone_region,
        dimension=settings.embedding_dim,
    )
    ingestion = IngestionService(store, settings)

    print("Ingesting sections into ChromaDB...")
    total_chunks = 0
    for doc in parsed_docs:
        chunks = ingestion.ingest_text(doc)
        total_chunks += chunks
        print(f"Ingested {doc.source} ({chunks} chunks)")

    print(
        f"\nSuccessfully ingested {len(parsed_docs)} documents "
        f"into ChromaDB ({total_chunks} total chunks)."
    )


if __name__ == "__main__":
    main()
