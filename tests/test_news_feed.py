from __future__ import annotations

import os
import sys

import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import utils


def test_summarize_news_feed_filters_to_30_days():
    now = pd.Timestamp("2024-06-01T12:00:00Z")
    data = pd.DataFrame(
        {
            "published_at": [
                now - pd.Timedelta(days=5),
                now - pd.Timedelta(days=15),
                now - pd.Timedelta(days=31),
            ],
            "is_strong_opportunity": [True, False, True],
            "mentions_competitor": [False, True, True],
        }
    )

    summary = utils.summarize_news_feed(data, now=now)

    assert summary.lookback_days == 30
    assert summary.articles_scanned == 2
    assert summary.strong_opportunities == 1
    assert summary.competitor_mentions == 1


def test_summarize_news_feed_handles_missing_columns():
    now = pd.Timestamp("2024-06-01T12:00:00Z")
    data = pd.DataFrame({"published_at": [now - pd.Timedelta(days=10)]})

    summary = utils.summarize_news_feed(data, now=now)

    assert isinstance(summary, utils.NewsFeedSummary)
    assert summary.articles_scanned == 1
    assert summary.strong_opportunities == 0
    assert summary.competitor_mentions == 0


def test_summarize_news_feed_accepts_iterables():
    now = pd.Timestamp("2024-06-01T12:00:00Z")
    data = [
        {
            "published_at": now - pd.Timedelta(days=1),
            "is_strong_opportunity": 1,
            "mentions_competitor": 0,
        },
        {
            "published_at": now - pd.Timedelta(days=40),
            "is_strong_opportunity": 0,
            "mentions_competitor": 1,
        },
    ]

    summary = utils.summarize_news_feed(data, now=now)

    assert summary.articles_scanned == 1
    assert summary.strong_opportunities == 1
    assert summary.competitor_mentions == 0
