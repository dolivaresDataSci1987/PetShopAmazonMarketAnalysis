import streamlit as st
import plotly.express as px

from utils.load_data import load_category_opportunity

st.title("Opportunity Map")
st.markdown(
    """
This section focuses on category-level opportunity signals,
helping identify promising areas for expansion or strategic entry.
"""
)

opportunity = load_category_opportunity()

st.dataframe(opportunity, use_container_width=True)

numeric_cols = opportunity.select_dtypes(include="number").columns.tolist()
cat_cols = opportunity.select_dtypes(exclude="number").columns.tolist()

if numeric_cols and cat_cols:
    fig = px.bar(
        opportunity.sort_values(numeric_cols[0], ascending=False).head(20),
        x=cat_cols[0],
        y=numeric_cols[0],
        title=f"Top Opportunities by {numeric_cols[0]}"
    )
    st.plotly_chart(fig, use_container_width=True)

if len(numeric_cols) >= 2 and cat_cols:
    fig2 = px.scatter(
        opportunity,
        x=numeric_cols[0],
        y=numeric_cols[1],
        hover_data=cat_cols,
        title="Opportunity Positioning"
    )
    st.plotly_chart(fig2, use_container_width=True)
