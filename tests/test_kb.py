import os
import sys
from pathlib import Path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import kb


def fake_embed(text):
    return [1.0]


def test_add_document_and_search(tmp_path, monkeypatch):
    doc = tmp_path / "s.txt"
    doc.write_text("hello world")
    monkeypatch.setattr(kb, "KB_STORE", tmp_path / "kb.json")
    monkeypatch.setattr(kb, "embed_text", fake_embed)
    doc_id = kb.add_document(str(doc), "UX")
    kb.update_status(doc_id, "approved")
    results = kb.search("UX", "hello")
    assert results and "hello" in results[0]
