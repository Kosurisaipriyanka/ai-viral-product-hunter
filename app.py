"""Streamlit dashboard for the AI Viral Product Hunter (sample-data phase)."""
import io

import pandas as pd
import requests
import streamlit as st

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="AI Viral Product Hunter", page_icon="🔎", layout="wide")
st.title("🔎 AI Viral Product Hunter")
st.caption("Discover and evaluate product ideas. Current results are DEMO SAMPLE DATA, not live trends.")

categories = ["Pet Gadgets", "Home & Kitchen", "Fitness", "Beauty Accessories", "Travel Accessories"]
category = st.selectbox("Choose a product category", categories)

if st.button("Hunt Products", type="primary"):
    try:
        response = requests.get(f"{API_URL}/products", params={"category": category}, timeout=5)
        response.raise_for_status()
        st.session_state["products"] = response.json()["products"]
        st.session_state["category"] = category
    except requests.RequestException:
        st.session_state["products"] = None
        st.error("Cannot connect to the API. Start the backend with: uv run uvicorn api:app --reload")

products = st.session_state.get("products")
if products is None and "products" in st.session_state:
    st.info("The API is unavailable. Start the backend and try again.")
elif products:
    df = pd.DataFrame(products)
    st.subheader(f"Sample results: {st.session_state.get('category', category)}")
    st.warning("Demo mode: these products and scores are illustrative examples, not verified live market data.")
    m1, m2, m3 = st.columns(3)
    m1.metric("Products", len(df))
    m2.metric("Average viral score", f"{df['viral_score'].mean():.0f}/100")
    m3.metric("Average estimated retail price", f"₹{df['estimated_retail_price_inr'].mean():,.0f}")
    st.dataframe(df, use_container_width=True, hide_index=True)
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download results as CSV", data=csv, file_name="viral_product_candidates.csv", mime="text/csv")
else:
    st.info("Choose a category and click **Hunt Products** to view sample candidates.")

st.divider()
st.caption("Phase 1 uses sample data only. Live discovery and supplier research will be added later, using permitted sources and free-tier APIs where available.")
