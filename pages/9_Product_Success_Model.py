import streamlit as st
import plotly.express as px

from utils.load_data import load_product_success

st.title("Product Success Model")
st.markdown(
    """
This page presents the product success scoring layer,
used to compare products through a composite performance lens.
"""
)

success = load_product_success()

st.dataframe(success, use_container_width=True)

numeric_cols = success.select_dtypes(include="number").columns.tolist()
text_cols = success.select_dtypes(exclude="number").columns.tolist()

if numeric_cols:
    fig = px.histogram(
        success,
        x=numeric_cols[0],
        nbins=30,
        title=f"Distribution of {numeric_cols[0]}"
    )
    st.plotly_chart(fig, use_container_width=True)

if len(numeric_cols) >= 2:
    fig2 = px.scatter(
        success,
        x=numeric_cols[0],
        y=numeric_cols[1],
        hover_data=text_cols,
        title=f"{numeric_cols[0]} vs {numeric_cols[1]}"
    )
    st.plotly_chart(fig2, use_container_width=True)
