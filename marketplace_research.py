"""Create safe, direct marketplace research links without scraping or claiming verified data."""
from urllib.parse import quote_plus


MARKETPLACE_SEARCHES = {
    "Amazon India": "https://www.amazon.in/s?k={query}",
    "Flipkart": "https://www.flipkart.com/search?q={query}",
    "IndiaMART": "https://dir.indiamart.com/search.mp?ss={query}",
    "Google Shopping": "https://www.google.com/search?tbm=shop&q={query}",
    "YouTube product reviews": "https://www.youtube.com/results?search_query={query}",
}


def build_marketplace_search_links(product_query):
    """Return search URLs for a non-empty product query.

    These are outbound search links only; results, prices, stock, and suppliers
    are provided by the destination sites and are not independently verified.
    """
    query = str(product_query or "").strip()
    if not query:
        return []
    encoded = quote_plus(query)
    return [
        {"source": name, "search_url": template.format(query=encoded)}
        for name, template in MARKETPLACE_SEARCHES.items()
    ]
