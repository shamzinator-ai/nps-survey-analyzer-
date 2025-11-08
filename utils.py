from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, List, Mapping

import pandas as pd
import streamlit as st


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


@dataclass(frozen=True)
class NewsFeedSummary:
    """Structured counts for the real-time news feed cards."""

    articles_scanned: int
    strong_opportunities: int
    competitor_mentions: int
    lookback_days: int


def _to_dataframe(
    data: pd.DataFrame | Iterable[Mapping[str, object]] | None
) -> pd.DataFrame:
    """Return ``data`` as a DataFrame without mutating the original input."""

    if data is None:
        return pd.DataFrame()
    if isinstance(data, pd.DataFrame):
        return data.copy()
    if isinstance(data, Iterable):
        return pd.DataFrame(list(data))
    raise TypeError("Unsupported data type for news feed summary")


def summarize_news_feed(
    data: pd.DataFrame | Iterable[Mapping[str, object]] | None,
    *,
    lookback_days: int = 30,
    now: datetime | pd.Timestamp | None = None,
    date_column: str = "published_at",
    opportunity_column: str = "is_strong_opportunity",
    competitor_column: str = "mentions_competitor",
) -> NewsFeedSummary:
    """Aggregate metrics for the real-time news feed cards.

    Parameters
    ----------
    data:
        DataFrame or iterable of mappings containing the news feed information.
    lookback_days:
        Number of trailing days to include in the metrics.
    now:
        Optional reference datetime used when computing the trailing window.
    date_column:
        Column containing the published timestamp for each item.
    opportunity_column:
        Column indicating whether the item is a strong opportunity. Values are
        interpreted using ``pandas.Series.astype(bool)`` to support multiple
        truthy representations.
    competitor_column:
        Column indicating whether the item mentions a competitor. Values are
        converted using ``astype(bool)`` similar to ``opportunity_column``.
    """

    df = _to_dataframe(data)
    if df.empty:
        return NewsFeedSummary(0, 0, 0, lookback_days)

    if now is None:
        now = pd.Timestamp.utcnow()
    else:
        now = pd.Timestamp(now)

    if now.tzinfo is None:
        now = now.tz_localize("UTC")
    else:
        now = now.tz_convert("UTC")

    if date_column not in df.columns:
        return NewsFeedSummary(0, 0, 0, lookback_days)

    df = df.copy()
    df[date_column] = pd.to_datetime(df[date_column], errors="coerce", utc=True)
    df = df.dropna(subset=[date_column])
    if df.empty:
        return NewsFeedSummary(0, 0, 0, lookback_days)

    cutoff = now - pd.Timedelta(days=lookback_days)
    recent = df[df[date_column] >= cutoff]
    articles_scanned = int(len(recent))

    if opportunity_column in recent.columns:
        opportunities = int(recent[opportunity_column].fillna(False).astype(bool).sum())
    else:
        opportunities = 0

    if competitor_column in recent.columns:
        competitor_mentions = int(recent[competitor_column].fillna(False).astype(bool).sum())
    else:
        competitor_mentions = 0

    return NewsFeedSummary(articles_scanned, opportunities, competitor_mentions, lookback_days)
