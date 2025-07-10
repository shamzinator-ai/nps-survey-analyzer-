import pandas as pd
import pytest
from unittest.mock import MagicMock

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import utils


def test_concat_series_with_missing_column(monkeypatch):
    df = pd.DataFrame({"a": ["x"]})
    st = MagicMock()
    monkeypatch.setattr(utils, "st", st)
    with pytest.raises(KeyError):
        utils.concat_series(df, ["a", "b"])
    st.error.assert_called_once()


def test_concat_series_with_nan_and_blank(monkeypatch):
    df = pd.DataFrame({
        "a": ["foo", None, ""],
        "b": ["bar", "baz", None],
    })
    st = MagicMock()
    monkeypatch.setattr(utils, "st", st)
    result = utils.concat_series(df, ["a", "b"])
    assert result.tolist() == ["foo bar", " baz", " "]
    st.error.assert_not_called()
    st.warning.assert_not_called()


def test_concat_series_warns_on_blank_column(monkeypatch):
    df = pd.DataFrame({
        "a": ["", ""],
        "b": ["hello", "world"],
    })
    st = MagicMock()
    monkeypatch.setattr(utils, "st", st)
    result = utils.concat_series(df, ["a", "b"])
    assert result.tolist() == [" hello", " world"]
    st.warning.assert_called_once()


def test_concat_series_multiple_columns(monkeypatch):
    df = pd.DataFrame(
        {
            "a": ["foo", None],
            "b": ["bar", ""],
            "c": [None, "baz"],
        }
    )
    st = MagicMock()
    monkeypatch.setattr(utils, "st", st)
    result = utils.concat_series(df, ["a", "b", "c"])
    assert result.tolist() == ["foo bar ", "  baz"]
    st.error.assert_not_called()
    st.warning.assert_not_called()
