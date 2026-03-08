import streamlit as st
import pandas as pd
import plotly.express as px

from utils.load_data import load_products

st.set_page_config(page_title="Overview", layout="wide")

st.title("Market Overview")
st.markdown(
    """
This page provides a high-level view of the Amazon Pet Products market,
including overall market size, pricing, ratings, and product composition.
"""
)

products = load_products().copy()

# -----------------------------
# Basic cleaning
# -----------------------------
products = products.dropna(subset=["price", "avg_rating", "review_count"])
products = products[products["price"] > 0]

if "brand" in products.columns:
    products["brand"] = products["brand"].astype(str).str.strip()

# -----------------------------
# KPI block
# -----------------------------
total_products = len(products)
total_brands = products["brand"].nunique() if "brand" in products.columns else None
avg_price = products["price"].mean()
median_price = products["price"].median()
avg_rating = products["avg_rating"].mean()
total_reviews = products["review_count"].sum()

c1, c2, c3, c4, c5, c6 = st.columns(6)

c1.metric("Products", f"{total_products:,}")
c2.metric("Brands", f"{total_brands:,}" if total_brands is not None else "N/A")
c3.metric("Avg Price", f"${avg_price:,.2f}")
c4.metric("Median Price", f"${median_price:,.2f}")
c5.metric("Avg Rating", f"{avg_rating:.2f}")
c6.metric("Total Reviews", f"{int(total_reviews):,}")

st.divider()

# -----------------------------
# Charts row 1
# -----------------------------
left, right = st.columns(2)

with left:
    fig_price = px.histogram(
        products,
        x="price",
        nbins=40,
        title="Price Distribution"
    )
    fig_price.update_layout(xaxis_title="Price", yaxis_title="Product Count")
    st.plotly_chart(fig_price, use_container_width=True)

with right:
    fig_rating = px.histogram(
        products,
        x="avg_rating",
        nbins=30,
        title="Rating Distribution"
    )
    fig_rating.update_layout(xaxis_title="Average Rating", yaxis_title="Product Count")
    st.plotly_chart(fig_rating, use_container_width=True)

st.divider()

# -----------------------------
# Charts row 2
# -----------------------------
left, right = st.columns(2)

if "animal_type" in products.columns:
    animal_summary = (
        products.groupby("animal_type", dropna=False)
        .size()
        .reset_index(name="product_count")
        .sort_values("product_count", ascending=False)
    )

    with left:
        fig_animal = px.bar(
            animal_summary,
            x="animal_type",
            y="product_count",
            title="Products by Animal Type"
        )
        fig_animal.update_layout(xaxis_title="Animal Type", yaxis_title="Product Count")
        st.plotly_chart(fig_animal, use_container_width=True)
else:
    with left:
        st.info("Column `animal_type` not found in products_master.csv")

if "product_type" in products.columns:
    product_type_summary = (
        products.groupby("product_type", dropna=False)
        .size()
        .reset_index(name="product_count")
        .sort_values("product_count", ascending=False)
        .head(15)
    )

    with right:
        fig_type = px.bar(
            product_type_summary,
            x="product_type",
            y="product_count",
            title="Top Product Types"
        )
        fig_type.update_layout(xaxis_title="Product Type", yaxis_title="Product Count")
        st.plotly_chart(fig_type, use_container_width=True)
else:
    with right:
        st.info("Column `product_type` not found in products_master.csv")

st.divider()

# -----------------------------
# Scatter plot
# -----------------------------
st.subheader("Price vs Rating")

fig_scatter = px.scatter(
    products.sample(min(len(products), 3000), random_state=42),
    x="price",
    y="avg_rating",
    size="review_count",
    hover_data=[col for col in ["title", "brand", "animal_type", "product_type"] if col in products.columns],
    title="Price, Rating, and Review Volume"
)
fig_scatter.update_layout(
    xaxis_title="Price",
    yaxis_title="Average Rating"
)
st.plotly_chart(fig_scatter, use_container_width=True)
