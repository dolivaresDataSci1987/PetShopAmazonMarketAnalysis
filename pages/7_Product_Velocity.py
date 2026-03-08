import streamlit as st
import plotly.express as px

from utils.load_data import load_product_velocity

st.title("Product Velocity")
st.markdown(
    """
This page tracks momentum signals across products, using velocity-style metrics
to identify fast-rising items and emerging performers.
"""
)

velocity = load_product_velocity()

st.dataframe(velocity, use_container_width=True)

numeric_cols = velocity.select_dtypes(include="number").columns.tolist()
text_cols = velocity.select_dtypes(exclude="number").columns.tolist()

if numeric_cols:
    fig = px.histogram(
        velocity,
        x=numeric_cols[0],
        nbins=30,
        title=f"Distribution of {numeric_cols[0]}"
    )
    st.plotly_chart(fig, use_container_width=True)

if len(numeric_cols) >= 2:
    fig2 = px.scatter(
        velocity,
        x=numeric_cols[0],
        y=numeric_cols[1],
        hover_data=text_cols,
        title=f"{numeric_cols[0]} vs {numeric_cols[1]}"
    )
    st.plotly_chart(fig2, use_container_width=True)
