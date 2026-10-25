
"""Transparent product decision rules for research screening."""


def recommend_product(
    selling_price,
    total_cost,
    trends_interest,
    youtube_views,
    supplier_name,
):
    """Return a decision and reasons based on explicit screening rules."""
    profit = selling_price - total_cost

    if selling_price <= 0:
        return {
            "decision": "HIGH RISK",
            "reasons": ["Selling price must be greater than zero."],
        }

    if profit < 0:
        return {
            "decision": "HIGH RISK",
            "reasons": ["Estimated profit is negative."],
        }

    margin = profit / selling_price * 100
    missing = []

    if total_cost <= 0:
        missing.append("Verify supplier and other costs.")
    if trends_interest <= 0:
        missing.append("Collect valid Google Trends data.")
    if youtube_views <= 0:
        missing.append("Collect relevant YouTube view data.")
    if not supplier_name.strip():
        missing.append("Record the supplier name.")
    if margin < 20:
        missing.append("Review the low profit margin.")

    if missing:
        return {
            "decision": "NEEDS MORE RESEARCH",
            "reasons": missing,
        }

    if (
        trends_interest >= 50
        and youtube_views >= 100_000
        and margin >= 30
    ):
        return {
            "decision": "PROMISING SIGNAL",
            "reasons": [
                "Entered research signals and estimated margin meet the screening thresholds."
            ],
        }

    return {
        "decision": "NEEDS MORE RESEARCH",
        "reasons": [
            "Research signals do not meet all promising-signal thresholds."
        ],
    }
