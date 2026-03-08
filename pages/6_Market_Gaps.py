import streamlit as st
import plotly.express as px

from utils.load_data import load_market_gaps

st.title("Market Gap Analysis")
st.markdown(
    """
This page identifies potential whitespace areas in the market:
segments that may show room for new products, stronger positioning, or unmet demand.
"""
)

gaps = load_market_gaps()

st.dataframe(gaps, use_container_width=True)

numeric_cols = gaps.select_dtypes(include="number").columns.tolist()
cat_cols = gaps.select_dtypes(exclude="number").columns.tolist()

if numeric_cols and cat_cols:
    fig = px.bar(
        gaps.sort_values(numeric_cols[0], ascending=False).head(20),
        x=cat_cols[0],
        y=numeric_cols[0],
        title=f"Top Market Gaps by {numeric_cols[0]}"
    )
    st.plotly_chart(fig, use_container_width=True)

if len(numeric_cols) >= 2 and cat_cols:
    fig2 = px.scatter(
        gaps,
        x=numeric_cols[0],
        y=numeric_cols[1],
        hover_data=cat_cols,
        title="Gap Positioning"
    )
    st.plotly_chart(fig2, use_container_width=True)
