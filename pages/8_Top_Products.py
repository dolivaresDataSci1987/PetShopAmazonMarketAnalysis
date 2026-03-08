import streamlit as st
import pandas as pd
import plotly.express as px

from utils.load_data import load_top_products

st.title("Top Products")

st.markdown(
"""
This page highlights the top-performing products in the Amazon pet market
based on the ranking metrics computed in the analytical pipeline.
"""
)

# =========================================================
# Load data
# =========================================================
top_products = load_top_products().copy()

# =========================================================
# Clean product titles (truncate long titles)
# =========================================================
def shorten_title(title, max_words=12):
    if not isinstance(title, str):
        return title
    words = title.split()
    if len(words) <= max_words:
        return title
    return " ".join(words[:max_words]) + "..."

if "product_title" in top_products.columns:
    top_products["short_title"] = top_products["product_title"].apply(shorten_title)
else:
    top_products["short_title"] = "Unknown product"

# =========================================================
# Basic cleaning
# =========================================================
for col in top_products.columns:
    if top_products[col].dtype == "object":
        top_products[col] = top_products[col].astype(str).str.strip()

# =========================================================
# Filters
# =========================================================
st.subheader("Filters")

f1, f2, f3 = st.columns(3)

animal_col = None
for c in ["animal_type", "category_l2"]:
    if c in top_products.columns:
        animal_col = c
        break

product_col = None
for c in ["product_type", "category_l3"]:
    if c in top_products.columns:
        product_col = c
        break

brand_col = "brand" if "brand" in top_products.columns else None

filtered_df = top_products.copy()

if animal_col:
    animal_options = ["All"] + sorted(filtered_df[animal_col].dropna().unique().tolist())
    selected_animal = f1.selectbox("Animal Type", animal_options)
    if selected_animal != "All":
        filtered_df = filtered_df[filtered_df[animal_col] == selected_animal]

if product_col:
    product_options = ["All"] + sorted(filtered_df[product_col].dropna().unique().tolist())
    selected_product = f2.selectbox("Product Type", product_options)
    if selected_product != "All":
        filtered_df = filtered_df[filtered_df[product_col] == selected_product]

if brand_col:
    brand_options = ["All"] + sorted(filtered_df[brand_col].dropna().unique().tolist())
    selected_brand = f3.selectbox("Brand", brand_options)
    if selected_brand != "All":
        filtered_df = filtered_df[filtered_df[brand_col] == selected_brand]

if filtered_df.empty:
    st.warning("No products match the selected filters.")
    st.stop()

st.divider()

# =========================================================
# Top product ranking
# =========================================================
st.subheader("Top Products Ranking")

metric_candidates = [
    "product_success_score",
    "velocity_score",
    "rating_number",
    "review_count"
]

metric_col = None
for m in metric_candidates:
    if m in filtered_df.columns:
        metric_col = m
        break

if metric_col:

    ranking_df = (
        filtered_df
        .sort_values(metric_col, ascending=False)
        .head(20)
        .sort_values(metric_col)
    )

    fig_rank = px.bar(
        ranking_df,
        x=metric_col,
        y="short_title",
        orientation="h",
        color="average_rating" if "average_rating" in ranking_df.columns else None,
        title=f"Top Products by {metric_col}",
        hover_data={
            "product_title": True,
            "brand": True if "brand" in ranking_df.columns else False,
            "price": ":.2f" if "price" in ranking_df.columns else False,
            "average_rating": ":.2f" if "average_rating" in ranking_df.columns else False,
            "rating_number": ":,.0f" if "rating_number" in ranking_df.columns else False,
            "review_count": ":,.0f" if "review_count" in ranking_df.columns else False,
        },
        color_continuous_scale="Tealgrn"
    )

    fig_rank.update_layout(
        xaxis_title=metric_col,
        yaxis_title="Product",
        margin=dict(l=20, r=20, t=60, b=20)
    )

    st.plotly_chart(fig_rank, use_container_width=True)

else:
    st.info("No suitable ranking metric found.")

st.divider()

# =========================================================
# Rating vs review volume
# =========================================================
st.subheader("Rating vs Review Volume")

if {"average_rating", "rating_number"}.issubset(filtered_df.columns):

    bubble_df = filtered_df.copy()

    if "price" in bubble_df.columns:
        size_col = "price"
    else:
        size_col = None

    fig_bubble = px.scatter(
        bubble_df,
        x="average_rating",
        y="rating_number",
        size=size_col,
        color="brand" if "brand" in bubble_df.columns else None,
        hover_data={
            "product_title": True,
            "price": ":.2f" if "price" in bubble_df.columns else False,
            "rating_number": ":,.0f",
        },
        title="Product Quality vs Market Validation"
    )

    fig_bubble.update_layout(
        xaxis_title="Average Rating",
        yaxis_title="Rating Count",
        margin=dict(l=20, r=20, t=60, b=20)
    )

    st.plotly_chart(fig_bubble, use_container_width=True)

st.divider()

# =========================================================
# Underlying table
# =========================================================
with st.expander("View full product table"):

    display_cols = [
        c for c in [
            "product_title",
            "brand",
            animal_col,
            product_col,
            "price",
            "average_rating",
            "rating_number",
            "review_count",
            "velocity_score",
            "product_success_score"
        ]
        if c in filtered_df.columns
    ]

    st.dataframe(
        filtered_df[display_cols].sort_values(metric_col, ascending=False),
        use_container_width=True
    )
