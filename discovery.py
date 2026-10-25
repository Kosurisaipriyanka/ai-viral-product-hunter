"""Optional Google Trends discovery connector.

Google Trends is a search-interest signal, not proof of product sales.
The pytrends package uses an unofficial interface; requests may be rate-limited
or blocked. The API reports failures honestly instead of inventing data.
"""
from __future__ import annotations

from typing import Any


def fetch_google_trends(keywords: list[str], geo: str = "IN") -> dict[str, Any]:
    """Fetch up to five keyword interest series for the last three months."""
    cleaned = list(dict.fromkeys(k.strip() for k in keywords if k.strip()))[:5]
    if not cleaned:
        return {
            "source": "Google Trends",
            "geo": geo,
            "timeframe": "today 3-m",
            "items": [],
            "note": "Enter at least one keyword.",
        }

    try:
        from pytrends.request import TrendReq

        # pytrends expects a single numeric timeout, not a requests-style tuple.
        client = TrendReq(hl="en-IN", tz=330, timeout=15, retries=1, backoff_factor=0.2)
        client.build_payload(cleaned, timeframe="today 3-m", geo=geo)
        frame = client.interest_over_time()
    except Exception as exc:
        return {
            "source": "Google Trends",
            "geo": geo,
            "timeframe": "today 3-m",
            "items": [],
            "error": "Google Trends could not be reached. It may be rate-limiting requests; try again later.",
            "detail": type(exc).__name__,
        }

    if frame.empty:
        return {
            "source": "Google Trends",
            "geo": geo,
            "timeframe": "today 3-m",
            "items": [],
            "note": "Google Trends returned no interest data for these keywords.",
        }

    items = []
    for keyword in cleaned:
        if keyword not in frame.columns:
            continue
        values = frame[keyword].dropna()
        if values.empty:
            continue
        latest = int(values.iloc[-1])
        previous = int(values.iloc[-2]) if len(values) > 1 else None
        change_pct = None
        if previous is not None and previous > 0:
            change_pct = round(((latest - previous) / previous) * 100, 1)
        items.append({
            "keyword": keyword,
            "latest_interest": latest,
            "previous_interest": previous,
            "change_percent": change_pct,
            "points": int(len(values)),
        })

    return {
        "source": "Google Trends",
        "geo": geo,
        "timeframe": "today 3-m",
        "items": items,
        "note": "Interest is indexed from 0 to 100; it is not sales volume or proof of virality.",
    }
