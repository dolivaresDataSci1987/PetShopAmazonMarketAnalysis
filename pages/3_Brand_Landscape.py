import streamlit as st
import plotly.express as px

from utils.load_data import (
    load_brand_summary,
    load_brand_product_matrix,
    load_brand_animal_matrix
)

st.title("Brand Landscape")
st.markdown(
    """
This page explores brand presence, brand scale, and market coverage across the Amazon pet products market.
"""
)

brand_summary = load_brand_summary()
brand_product_matrix = load_brand_product_matrix()
brand_animal_matrix = load_brand_animal_matrix()

st.subheader("Brand Summary")
st.dataframe(brand_summary, use_container_width=True)

if "brand" in brand_summary.columns:
    numeric_cols = brand_summary.select_dtypes(include="number").columns.tolist()

    if numeric_cols:
        metric_col = numeric_cols[0]

        fig = px.bar(
            brand_summary.sort_values(metric_col, ascending=False).head(20),
            x="brand",
            y=metric_col,
            title=f"Top Brands by {metric_col}"
        )
        st.plotly_chart(fig, use_container_width=True)

st.divider()

c1, c2 = st.columns(2)

with c1:
    st.subheader("Brand × Product Matrix")
    st.dataframe(brand_product_matrix, use_container_width=True)

with c2:
    st.subheader("Brand × Animal Matrix")
    st.dataframe(brand_animal_matrix, use_container_width=True)
