
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



def calculate_opportunity_score(
    trends_interest=None,
    relevant_video_count=0,
    total_video_count=0,
    top_relevant_views=None,
    margin_percent=None,
    supplier_verified=False,
):
    """Return a transparent 0-100 screening score plus component breakdown.

    This heuristic prioritizes indexed interest, relevant video evidence,
    attention among relevant videos, estimated margin, and supplier verification.
    It is not a prediction of sales or virality.
    """
    def bounded(value, low=0, high=100):
        return max(low, min(high, float(value)))

    trend_points = bounded(trends_interest or 0) * 0.25
    if total_video_count > 0:
        relevance_rate = bounded((relevant_video_count / total_video_count) * 100)
    else:
        relevance_rate = 0
    relevance_points = relevance_rate * 0.25

    if top_relevant_views is None or top_relevant_views <= 0:
        views_strength = 0
    else:
        # Log-like tiers avoid allowing one enormous video to dominate the score.
        views_strength = min(100, (float(top_relevant_views) / 100_000) ** 0.5 * 50)
    views_points = views_strength * 0.15

    margin_strength = bounded((margin_percent or 0) / 40 * 100)
    margin_points = margin_strength * 0.25
    supplier_points = 10 if supplier_verified else 0

    components = {
        "trend_interest": round(trend_points, 1),
        "video_relevance": round(relevance_points, 1),
        "relevant_video_views": round(views_points, 1),
        "estimated_margin": round(margin_points, 1),
        "supplier_verification": round(supplier_points, 1),
    }
    score = round(sum(components.values()))
    gaps = []
    if trends_interest is None:
        gaps.append("Google Trends interest is unavailable.")
    if total_video_count == 0:
        gaps.append("No YouTube videos were returned.")
    elif relevant_video_count == 0:
        gaps.append("No videos were classified as HIGH or MEDIUM relevance.")
    if margin_percent is None:
        gaps.append("Profit margin is unavailable until selling price and costs are entered.")
    if not supplier_verified:
        gaps.append("Supplier listing, product match, shipping, and reliability are not verified.")

    if score >= 75 and not gaps:
        label = "STRONGER OPPORTUNITY SIGNAL"
    elif score >= 50:
        label = "MIXED OPPORTUNITY SIGNAL"
    else:
        label = "WEAK OR INCOMPLETE SIGNAL"

    return {
        "score": score,
        "label": label,
        "components": components,
        "evidence_gaps": gaps,
        "method_note": "Heuristic screening score, not a validated sales or virality prediction. Trend interest is normalized; video views are attention, not purchases.",
    }



def rank_product_comparisons(products):
    """Score and rank user-entered product evidence for side-by-side comparison."""
    ranked = []
    for product in products:
        name = str(product.get("product_name", "")).strip()
        if not name:
            continue
        result = calculate_opportunity_score(
            trends_interest=product.get("trends_interest"),
            relevant_video_count=product.get("relevant_video_count", 0),
            total_video_count=product.get("total_video_count", 0),
            top_relevant_views=product.get("top_relevant_views"),
            margin_percent=product.get("margin_percent"),
            supplier_verified=bool(product.get("supplier_verified", False)),
        )
        ranked.append({
            "product_name": name,
            "opportunity_score": result["score"],
            "signal": result["label"],
            "trend_interest": product.get("trends_interest"),
            "relevant_videos": product.get("relevant_video_count", 0),
            "videos_checked": product.get("total_video_count", 0),
            "top_relevant_views": product.get("top_relevant_views"),
            "estimated_margin_percent": product.get("margin_percent"),
            "supplier_verified": bool(product.get("supplier_verified", False)),
            "evidence_gaps": " ".join(result["evidence_gaps"]) or "No configured evidence gaps",
            "score_method": result["method_note"],
        })
    ranked.sort(key=lambda item: item["opportunity_score"], reverse=True)
    for index, product in enumerate(ranked, start=1):
        product["rank"] = index
    return ranked
