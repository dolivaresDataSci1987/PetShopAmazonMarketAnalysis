import streamlit as st
import plotly.express as px

from utils.load_data import load_top_products

st.title("Top Products")
st.markdown(
    """
This page showcases leading products in the market based on the ranking logic
used in the exported analytical tables.
"""
)

top_products = load_top_products()

st.dataframe(top_products, use_container_width=True)

numeric_cols = top_products.select_dtypes(include="number").columns.tolist()
text_cols = top_products.select_dtypes(exclude="number").columns.tolist()

if numeric_cols and text_cols:
    fig = px.bar(
        top_products.head(20),
        x=text_cols[0],
        y=numeric_cols[0],
        title=f"Top Products by {numeric_cols[0]}"
    )
    st.plotly_chart(fig, use_container_width=True)
