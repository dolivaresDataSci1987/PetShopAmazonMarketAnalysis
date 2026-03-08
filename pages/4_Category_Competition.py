import streamlit as st
import plotly.express as px

from utils.load_data import load_category_competition

st.title("Category Competition")
st.markdown(
    """
This page highlights which categories appear more saturated, concentrated,
or competitively dense within the Amazon pet products market.
"""
)

competition = load_category_competition()

st.dataframe(competition, use_container_width=True)

numeric_cols = competition.select_dtypes(include="number").columns.tolist()
cat_cols = competition.select_dtypes(exclude="number").columns.tolist()

if numeric_cols and cat_cols:
    x_col = cat_cols[0]
    y_col = numeric_cols[0]

    fig = px.bar(
        competition.sort_values(y_col, ascending=False).head(20),
        x=x_col,
        y=y_col,
        title=f"Top Categories by {y_col}"
    )
    st.plotly_chart(fig, use_container_width=True)

if len(numeric_cols) >= 2 and cat_cols:
    fig2 = px.scatter(
        competition,
        x=numeric_cols[0],
        y=numeric_cols[1],
        hover_data=cat_cols,
        title=f"{numeric_cols[0]} vs {numeric_cols[1]}"
    )
    st.plotly_chart(fig2, use_container_width=True)
