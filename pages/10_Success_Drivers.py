import streamlit as st
import plotly.express as px

from utils.load_data import load_feature_importance

st.title("Success Drivers")
st.markdown(
    """
This section explains which variables contribute most strongly
to the product success scoring framework.
"""
)

importance = load_feature_importance()

st.dataframe(importance, use_container_width=True)

numeric_cols = importance.select_dtypes(include="number").columns.tolist()
text_cols = importance.select_dtypes(exclude="number").columns.tolist()

if numeric_cols and text_cols:
    fig = px.bar(
        importance.sort_values(numeric_cols[0], ascending=False),
        x=text_cols[0],
        y=numeric_cols[0],
        title=f"Feature Importance: {numeric_cols[0]}"
    )
    st.plotly_chart(fig, use_container_width=True)
