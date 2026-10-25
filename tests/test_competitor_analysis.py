from competitor_analysis import estimate_competitor_margin, summarize_competitor_prices


def test_competitor_prices_group_and_summarize_positive_prices():
    rows = [
        {"product_keyword": "Portable Blender", "source": "Amazon India", "listed_price_inr": 1499, "manually_checked": True},
        {"product_keyword": "portable blender", "source": "Flipkart", "listed_price_inr": 999, "manually_checked": False},
        {"product_keyword": "portable blender", "source": "IndiaMART", "listed_price_inr": 0, "manually_checked": False},
    ]
    summary = summarize_competitor_prices(rows)
    assert len(summary) == 1
    assert summary[0]["listing_count"] == 3
    assert summary[0]["priced_listing_count"] == 2
    assert summary[0]["lowest_price_inr"] == 999
    assert summary[0]["median_price_inr"] == 1249
    assert summary[0]["highest_price_inr"] == 1499
    assert summary[0]["manually_checked_count"] == 1


def test_competitor_summary_handles_no_rows_and_no_prices():
    assert summarize_competitor_prices([]) == []
    summary = summarize_competitor_prices([{"product_keyword": "Lamp", "listed_price_inr": 0}])
    assert summary[0]["median_price_inr"] is None


def test_estimated_margin_handles_costs_and_invalid_price():
    result = estimate_competitor_margin(1499, 600, 100, 150)
    assert result["total_cost_inr"] == 850
    assert round(result["estimated_profit_inr"], 2) == 649
    assert round(result["estimated_margin_percent"], 2) == 43.3
    assert estimate_competitor_margin(0, 100)["estimated_margin_percent"] is None
