import pandas as pd
from unittest.mock import MagicMock
import tempfile
import os
import app


async def fake_translate_batch(texts):
    return [(text + "_t", "en", 1, "") for text in texts]


async def fake_categorize_batch(texts):
    return [(["C"], "r", 1, "") for _ in texts]


def test_process_free_text_reprocesses_on_concat_change(monkeypatch, tmp_path):
    df = pd.DataFrame({"a": ["foo"], "b": ["bar"]})
    df["Concatenated"] = df["a"]
    df["Translated"] = ["OLD"]
    df["Language"] = ""
    df["Categories"] = ""
    df["CategoryReasoning"] = ""
    df["OriginalCategories"] = ""
    df["OriginalCategoryReasoning"] = ""
    df["ModelTokens"] = 0
    df["FinishReason"] = ""

    monkeypatch.setattr(app, "async_translate_batch", fake_translate_batch)
    monkeypatch.setattr(app, "async_categorize_batch", fake_categorize_batch)

    st = MagicMock()
    progress = MagicMock()
    st.progress.return_value = progress
    monkeypatch.setattr(app, "st", st)

    cache_path = os.path.join(tmp_path, "cache.pkl")

    result = app.process_free_text(df, ["a", "b"], cache_path, batch_size=1)

    assert result["Concatenated"].iloc[0] == "foo bar"
    assert result["Translated"].iloc[0] == "foo bar_t"


def test_process_free_text_creates_partial_file(monkeypatch, tmp_path):
    df = pd.DataFrame({"a": ["x"], "b": ["y"]})

    monkeypatch.setattr(app, "async_translate_batch", fake_translate_batch)
    monkeypatch.setattr(app, "async_categorize_batch", fake_categorize_batch)

    st = MagicMock()
    progress = MagicMock()
    st.progress.return_value = progress
    monkeypatch.setattr(app, "st", st)

    cache_path = os.path.join(tmp_path, "cache.pkl")
    partial_path = os.path.join(tmp_path, "cache_partial.pkl")

    result = app.process_free_text(df, ["a", "b"], cache_path, batch_size=1)

    assert os.path.exists(partial_path)
    os.remove(partial_path)
