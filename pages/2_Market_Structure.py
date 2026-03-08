import streamlit as st
import plotly.express as px

from utils.load_data import (
    load_price_segments,
    load_product_types,
    load_animal_categories
)

st.title("Market Structure")
st.markdown(
    """
This section explores how the Amazon Pet Products market is structurally organized
across price bands, product types, and animal categories.
"""
)

price_segments = load_price_segments()
product_types = load_product_types()
animal_categories = load_animal_categories()

c1, c2 = st.columns(2)

with c1:
    st.subheader("Price Segments")
    st.dataframe(price_segments, use_container_width=True)

    possible_x = price_segments.columns[0]
    possible_y = price_segments.columns[-1]

    fig = px.bar(price_segments, x=possible_x, y=possible_y, title="Price Segment Overview")
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.subheader("Product Type Summary")
    st.dataframe(product_types, use_container_width=True)

    possible_x = product_types.columns[0]
    possible_y = product_types.columns[-1]

    fig = px.bar(product_types.head(15), x=possible_x, y=possible_y, title="Top Product Types")
    st.plotly_chart(fig, use_container_width=True)

st.divider()

st.subheader("Animal Category Summary")
st.dataframe(animal_categories, use_container_width=True)

possible_x = animal_categories.columns[0]
possible_y = animal_categories.columns[-1]

fig = px.bar(animal_categories.head(20), x=possible_x, y=possible_y, title="Animal Category Distribution")
st.plotly_chart(fig, use_container_width=True)
