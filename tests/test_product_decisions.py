
from product_decisions import recommend_product


def test_negative_profit_is_high_risk():
    result = recommend_product(
        selling_price=500,
        total_cost=850,
        trends_interest=65,
        youtube_views=250_000,
        supplier_name="Supplier A",
    )
    assert result["decision"] == "HIGH RISK"


def test_missing_evidence_needs_more_research():
    result = recommend_product(
        selling_price=1499,
        total_cost=850,
        trends_interest=30,
        youtube_views=50_000,
        supplier_name="Supplier A",
    )
    assert result["decision"] == "NEEDS MORE RESEARCH"


def test_strong_sample_signals_are_promising():
    result = recommend_product(
        selling_price=1499,
        total_cost=850,
        trends_interest=65,
        youtube_views=250_000,
        supplier_name="Supplier A",
    )
    assert result["decision"] == "PROMISING SIGNAL"


def test_zero_selling_price_is_high_risk():
    result = recommend_product(
        selling_price=0,
        total_cost=850,
        trends_interest=65,
        youtube_views=250_000,
        supplier_name="Supplier A",
    )
    assert result["decision"] == "HIGH RISK"
