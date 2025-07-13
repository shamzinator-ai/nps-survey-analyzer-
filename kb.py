"""Knowledge base upload and search utilities."""

import json
import os
from pathlib import Path
from typing import List

import openai
from supabase import create_client
import tiktoken
from docx import Document
from PyPDF2 import PdfReader

# File used when Supabase credentials are missing
KB_STORE = Path("kb_store.json")


# ---------------------------- Helper Functions -----------------------------

def _load_store() -> dict:
    if KB_STORE.exists():
        with KB_STORE.open() as f:
            return json.load(f)
    return {"docs": [], "next_id": 1}


def _save_store(data: dict) -> None:
    KB_STORE.write_text(json.dumps(data, indent=2))


# --------------------------- Embedding Utilities ---------------------------

def embed_text(text: str) -> List[float]:
    """Return OpenAI embedding vector for the given text."""
    # UPDATED: Use OpenAI embeddings for chunk storage
    resp = openai.embeddings.create(model="text-embedding-ada-002", input=text)
    return resp.data[0].embedding  # type: ignore


def chunk_text(text: str, tokens: int = 200) -> List[str]:
    """Split text into roughly ``tokens``-sized chunks."""
    enc = tiktoken.get_encoding("cl100k_base")
    ids = enc.encode(text)
    chunks = []
    for i in range(0, len(ids), tokens):
        chunk_ids = ids[i : i + tokens]
        chunks.append(enc.decode(chunk_ids))
    return chunks


# --------------------------- File Loading Helpers --------------------------

def _read_txt(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _read_md(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _read_docx(path: Path) -> str:
    doc = Document(str(path))
    return "\n".join(p.text for p in doc.paragraphs)


def _read_pdf(path: Path) -> str:
    reader = PdfReader(str(path))
    text = []
    for page in reader.pages:
        text.append(page.extract_text() or "")
    return "\n".join(text)


READERS = {
    ".txt": _read_txt,
    ".md": _read_md,
    ".docx": _read_docx,
    ".pdf": _read_pdf,
}


# ------------------------------ Core Routines ------------------------------

def add_document(file_path: str, agent: str) -> int:
    """Process a file and store its chunks for ``agent``.

    If Supabase credentials are unavailable, data is saved locally in
    ``kb_store.json``.
    """

    path = Path(file_path)
    ext = path.suffix.lower()
    if ext not in READERS:
        raise ValueError(f"Unsupported file type: {ext}")
    text = READERS[ext](path)
    chunks = chunk_text(text)
    embeddings = [embed_text(c) for c in chunks]

    data = _load_store()
    doc_id = data["next_id"]
    data["next_id"] += 1
    for chunk, embedding in zip(chunks, embeddings):
        data["docs"].append(
            {
                "doc_id": doc_id,
                "agent": agent,
                "chunk": chunk,
                "embedding": embedding,
                "status": "pending",
            }
        )
    _save_store(data)
    return doc_id


def update_status(doc_id: int, status: str) -> None:
    data = _load_store()
    for item in data["docs"]:
        if item["doc_id"] == doc_id:
            item["status"] = status
    _save_store(data)


def delete_document(doc_id: int) -> None:
    data = _load_store()
    data["docs"] = [d for d in data["docs"] if d["doc_id"] != doc_id]
    _save_store(data)


def search(agent: str, query: str, top_k: int = 3) -> List[str]:
    """Return top matching chunks for ``query`` for the given agent."""

    data = _load_store()
    docs = [d for d in data["docs"] if d["agent"] == agent and d["status"] == "approved"]
    if not docs:
        return []
    q_emb = embed_text(query)

    def _score(v: List[float]) -> float:
        return sum(a * b for a, b in zip(v, q_emb))

    ranked = sorted(docs, key=lambda d: _score(d["embedding"]), reverse=True)
    return [d["chunk"] for d in ranked[:top_k]]

