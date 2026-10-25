from urllib.parse import quote_plus

from marketplace_research import build_marketplace_search_links


def test_marketplace_links_include_expected_sources_and_encoded_query():
    links = build_marketplace_search_links("portable blender India")
    assert len(links) == 5
    by_source = {item["source"]: item["search_url"] for item in links}
    assert "Amazon India" in by_source
    assert "Flipkart" in by_source
    assert quote_plus("portable blender India") in by_source["Amazon India"]
    assert by_source["Google Shopping"].startswith("https://www.google.com/search?tbm=shop")


def test_marketplace_links_reject_blank_query():
    assert build_marketplace_search_links("   ") == []
    assert build_marketplace_search_links(None) == []
