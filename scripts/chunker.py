import re

from src.config import CHUNK_OVERLAP, CHUNK_SIZE, SECTION_CHUNK_SIZE

_HEADER_PATTERN = re.compile(r"^(#{1,3})\s+(.+)$", re.MULTILINE)
_ALLCAPS_HEADER_PATTERN = re.compile(r"^([A-Z][A-Z0-9 \-]{2,})$", re.MULTILINE)



def _split_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    words = text.split()
    if not words:
        return []

    chunks: list[str] = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end])
        if chunk.strip():
            chunks.append(chunk)
        if end >= len(words):
            break
        start = max(end - overlap, start + 1)

    return chunks


def _split_plaintext_sections(text: str) -> list[tuple[str, str]]:
    """Split plain text on ALL-CAPS section headers (e.g. INVENTORY AGING)."""
    matches = list(_ALLCAPS_HEADER_PATTERN.finditer(text))
    if not matches:
        return [("Introduction", text.strip())] if text.strip() else []

    sections: list[tuple[str, str]] = []

    preamble = text[: matches[0].start()].strip()
    if preamble:
        sections.append(("Introduction", preamble))

    for i, match in enumerate(matches):
        title = match.group(1).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        if body:
            sections.append((title, body))

    return sections


def _split_markdown_sections(text: str) -> list[tuple[str, str]]:
    """Split text on markdown headers; returns (section_title, section_body) pairs."""
    matches = list(_HEADER_PATTERN.finditer(text))
    if not matches:
        return []

    sections: list[tuple[str, str]] = []

    preamble = text[: matches[0].start()].strip()
    if preamble:
        sections.append(("Introduction", preamble))

    for i, match in enumerate(matches):
        title = match.group(2).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        if body:
            sections.append((title, body))

    return sections


def _split_into_sections(text: str, source_file: str = "") -> list[tuple[str, str]]:
    sections = _split_markdown_sections(text)
    if sections:
        return sections

    # Plain-text emails/reports: try ALL-CAPS section headers
    if source_file.endswith(".txt"):
        return _split_plaintext_sections(text)

    return [("Introduction", text.strip())] if text.strip() else []


def chunk_documents(
    documents: list[dict],
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
    section_chunk_size: int = SECTION_CHUNK_SIZE,
) -> list[dict]:
    """Split documents into section-aware chunks with metadata."""
    chunks: list[dict] = []

    for doc in documents:
        sections = _split_into_sections(doc["text"], doc.get("source_file", ""))
        doc_chunk_id = 0

        for section_title, section_text in sections:
            word_count = len(section_text.split())
            if word_count <= section_chunk_size:
                parts = [section_text]
            else:
                parts = _split_text(section_text, chunk_size, overlap)

            for part in parts:
                chunks.append(
                    {
                        "source_file": doc["source_file"],
                        "chunk_id": doc_chunk_id,
                        "section_title": section_title,
                        "page": doc.get("page"),
                        "text": part,
                    }
                )
                doc_chunk_id += 1

    return chunks
