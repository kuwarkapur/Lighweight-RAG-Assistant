from pathlib import Path

from pypdf import PdfReader

from src.config import DOCUMENTS_DIR


def _read_pdf(path: Path) -> str:
    reader = PdfReader(str(path))
    pages = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        if text.strip():
            pages.append((i + 1, text))
    return pages


def load_documents(documents_dir: Path | None = None) -> list[dict]:
    """Load text documents from the documents directory."""
    base = documents_dir or DOCUMENTS_DIR
    documents: list[dict] = []

    if not base.exists():
        return documents

    for path in sorted(base.iterdir()):
        if not path.is_file():
            continue

        suffix = path.suffix.lower()
        if suffix == ".csv":
            continue

        if suffix == ".pdf":
            for page_num, text in _read_pdf(path):
                documents.append(
                    {
                        "source_file": path.name,
                        "text": text,
                        "page": page_num,
                    }
                )
        elif suffix in {".md", ".txt"}:
            text = path.read_text(encoding="utf-8")
            documents.append(
                {
                    "source_file": path.name,
                    "text": text,
                    "page": None,
                }
            )

    return documents
