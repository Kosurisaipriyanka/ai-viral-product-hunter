"""Transparent experimental opportunity scoring for Google Trends signals."""
from __future__ import annotations

from typing import Any


def score_trend_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Score available trend signals; this is a heuristic, not a sales/virality prediction.

    Score = 70% latest indexed interest + 30% normalized recent momentum.
    Momentum is capped at +/-100% so very large percentage changes do not dominate.
    If momentum cannot be calculated (for example, previous interest is zero),
    the score is left unavailable rather than inventing a value.
    """
    results = []
    for item in items:
        latest = item.get("latest_interest")
        change = item.get("change_percent")
        result = dict(item)
        if not isinstance(latest, (int, float)) or change is None:
            result["opportunity_score"] = None
            result["score_status"] = "insufficient trend history"
        else:
            bounded_change = max(-100.0, min(100.0, float(change)))
            momentum_component = (bounded_change + 100.0) / 2.0
            score = (0.7 * max(0.0, min(100.0, float(latest)))) + (0.3 * momentum_component)
            result["opportunity_score"] = round(max(0.0, min(100.0, score)), 1)
            result["score_status"] = "experimental trend-only heuristic"
        results.append(result)
    return results
