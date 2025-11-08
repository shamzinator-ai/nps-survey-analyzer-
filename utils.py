import pandas as pd
import streamlit as st
from typing import List


def concat_series(df: pd.DataFrame, free_text_cols: List[str]) -> pd.Series:
    """Concatenate multiple free-text columns into a single Series.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing the survey data.
    free_text_cols : List[str]
        Columns to concatenate.

    Returns
    -------
    pd.Series
        Concatenated free-text for each row.

    Raises
    ------
    KeyError
        If any of the requested columns are not present in ``df``.
    """
    missing = [c for c in free_text_cols if c not in df.columns]
    if missing:
        msg = f"Missing columns: {', '.join(missing)}"
        st.error(msg)
        raise KeyError(msg)

    # Build concatenated series
    series = df[free_text_cols].fillna("").apply(lambda r: " ".join(str(x) for x in r), axis=1)

    # Warn about completely blank columns
    empty_cols = [c for c in free_text_cols if df[c].fillna("").astype(str).str.strip().eq("").all()]
    if empty_cols:
        st.warning(
            "The following columns contain only empty strings: "
            + ", ".join(empty_cols)
            + ". Please review your selections."
        )

    return series
