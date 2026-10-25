"""Summaries for manually collected competitor listing evidence."""
from collections import defaultdict
from statistics import median


def summarize_competitor_prices(rows):
    """Group listing evidence by normalized keyword and summarize positive prices."""
    groups = defaultdict(list)
    for row in rows or []:
        keyword = str(row.get("product_keyword") or "").strip()
        if not keyword:
            continue
        groups[keyword.casefold()].append((keyword, row))
    summaries = []
    for entries in groups.values():
        keyword = entries[0][0]
        priced = [float(row.get("listed_price_inr") or 0) for _, row in entries
                  if float(row.get("listed_price_inr") or 0) > 0]
        checked = sum(bool(row.get("manually_checked")) for _, row in entries)
        sources = sorted({str(row.get("source") or "Unknown") for _, row in entries})
        summaries.append({
            "product_keyword": keyword,
            "listing_count": len(entries),
            "priced_listing_count": len(priced),
            "manually_checked_count": checked,
            "source_count": len(sources),
            "sources": ", ".join(sources),
            "lowest_price_inr": min(priced) if priced else None,
            "median_price_inr": median(priced) if priced else None,
            "highest_price_inr": max(priced) if priced else None,
        })
    return sorted(summaries, key=lambda item: item["product_keyword"].casefold())


def estimate_competitor_margin(selling_price, supplier_cost, shipping_cost=0, other_costs=0):
    """Return estimated margin percentage based on manually entered assumptions."""
    price = float(selling_price or 0)
    costs = sum(max(0.0, float(value or 0)) for value in (supplier_cost, shipping_cost, other_costs))
    if price <= 0:
        return {"total_cost_inr": costs, "estimated_profit_inr": None, "estimated_margin_percent": None}
    profit = price - costs
    return {
        "total_cost_inr": costs,
        "estimated_profit_inr": profit,
        "estimated_margin_percent": profit / price * 100,
    }
