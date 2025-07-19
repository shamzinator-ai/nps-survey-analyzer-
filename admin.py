"""Admin helpers for KB documents and usage analytics."""

import json
from pathlib import Path
from typing import Dict

KB_FILE = Path("kb_store.json")
ANALYTICS_FILE = Path("analytics.json")


def _load(path: Path, default):
    if path.exists():
        with path.open() as f:
            return json.load(f)
    return default


def _save(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2))


# ------------------------- Document Status Actions ------------------------

def approve(doc_id: int) -> None:
    data = _load(KB_FILE, {"docs": []})
    for item in data["docs"]:
        if item["doc_id"] == doc_id:
            item["status"] = "approved"
    _save(KB_FILE, data)


def reject(doc_id: int) -> None:
    data = _load(KB_FILE, {"docs": []})
    for item in data["docs"]:
        if item["doc_id"] == doc_id:
            item["status"] = "rejected"
    _save(KB_FILE, data)


def delete(doc_id: int) -> None:
    data = _load(KB_FILE, {"docs": []})
    data["docs"] = [d for d in data["docs"] if d["doc_id"] != doc_id]
    _save(KB_FILE, data)


# ------------------------------ Analytics ---------------------------------

def increment_counter(key: str) -> None:
    stats = _load(ANALYTICS_FILE, {})
    stats[key] = stats.get(key, 0) + 1
    _save(ANALYTICS_FILE, stats)


def stats() -> Dict[str, int]:
    return _load(ANALYTICS_FILE, {})

