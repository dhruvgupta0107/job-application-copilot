import io

import docx
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader


def extract_text(filename: str, file_bytes: bytes) -> str:
    """Extract raw text from an uploaded resume file (.pdf, .docx, or .txt)."""
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""

    if ext == "pdf":
        reader = PdfReader(io.BytesIO(file_bytes))
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    if ext == "docx":
        document = docx.Document(io.BytesIO(file_bytes))
        return "\n".join(p.text for p in document.paragraphs)

    if ext == "txt":
        return file_bytes.decode("utf-8", errors="ignore")

    raise ValueError(f"Unsupported file type: .{ext}. Use .pdf, .docx, or .txt")


# Resume chunking needs different tuning than general document RAG - bullets and
# section headers are short and self-contained, so a smaller chunk size with
# section-aware separators keeps one "chunk" close to one logical unit
# (a bullet, a project summary) instead of splitting mid-thought.
splitter = RecursiveCharacterTextSplitter(
    chunk_size=400,
    chunk_overlap=50,
    separators=["\n\n", "\n", ". ", " "],
)


def chunk_text(raw_text: str) -> list[str]:
    """Split extracted resume text into retrieval-sized chunks."""
    chunks = splitter.split_text(raw_text)
    # Drop near-empty fragments (e.g. stray whitespace/lines from PDF extraction)
    return [c.strip() for c in chunks if len(c.strip()) > 15]
