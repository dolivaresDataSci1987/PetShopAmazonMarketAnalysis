import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

from utils.load_data import load_products

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
products = products.dropna(subset=["price", "average_rating", "review_count"])
products = products[products["price"] > 0]

if "brand" in products.columns:
    products["brand"] = products["brand"].astype(str).str.strip()

if "category_l1" in products.columns:
    products["category_l1"] = (
        products["category_l1"]
        .astype(str)
        .str.strip()
        .replace(
            ["", "nan", "None", "Unknown", "unknown", "N/A"],
            np.nan
        )
    )

# -----------------------------
# KPI block
# -----------------------------
total_products = len(products)
total_brands = products["brand"].nunique() if "brand" in products.columns else 0
avg_price = products["price"].mean()
median_price = products["price"].median()
avg_rating = products["average_rating"].mean()
total_reviews = products["review_count"].sum()

c1, c2, c3, c4, c5, c6 = st.columns(6)

c1.metric("Products", f"{total_products:,}")
c2.metric("Brands", f"{total_brands:,}")
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
    fig_price.update_layout(
        xaxis_title="Price",
        yaxis_title="Product Count"
    )
    st.plotly_chart(fig_price, use_container_width=True)

with right:
    fig_rating = px.histogram(
        products,
        x="average_rating",
        nbins=30,
        title="Rating Distribution"
    )
    fig_rating.update_layout(
        xaxis_title="Average Rating",
        yaxis_title="Product Count"
    )
    st.plotly_chart(fig_rating, use_container_width=True)

st.divider()

# -----------------------------
# Charts row 2
# -----------------------------
left, right = st.columns(2)

if "category_l2" in products.columns:
    cat2_summary = (
        products.dropna(subset=["category_l2"])
        .assign(category_l2=lambda x: x["category_l2"].astype(str).str.strip())
        .loc[lambda x: ~x["category_l2"].isin(["", "nan", "None", "Unknown"])]
        .groupby("category_l2", dropna=False)
        .size()
        .reset_index(name="product_count")
        .sort_values("product_count", ascending=False)
        .head(10)
    )

    cat2_summary["share_pct"] = (
        cat2_summary["product_count"] / cat2_summary["product_count"].sum() * 100
    ).round(1)

    with left:
        fig_cat2 = px.bar(
            cat2_summary.sort_values("product_count", ascending=True),
            x="product_count",
            y="category_l2",
            orientation="h",
            text="share_pct",
            title="Top Animal Types by Product Count"
        )
        fig_cat2.update_traces(
            texttemplate="%{text:.1f}%",
            textposition="outside"
        )
        fig_cat2.update_layout(
            xaxis_title="Product Count",
            yaxis_title="Animal Type",
            yaxis={"categoryorder": "total ascending"},
            margin=dict(l=20, r=20, t=50, b=20)
        )
        st.plotly_chart(fig_cat2, use_container_width=True)
else:
    with left:
        st.info("Column `category_l2` not found in products_master.csv")

if "brand" in products.columns:
    brand_summary = (
        products.groupby("brand", dropna=False)
        .size()
        .reset_index(name="product_count")
        .sort_values("product_count", ascending=False)
        .head(15)
    )

    with right:
        fig_brand = px.bar(
            brand_summary,
            x="brand",
            y="product_count",
            title="Top Brands by Product Count"
        )
        fig_brand.update_layout(
            xaxis_title="Brand",
            yaxis_title="Product Count"
        )
        st.plotly_chart(fig_brand, use_container_width=True)
else:
    with right:
        st.info("Column `brand` not found in products_master.csv")

st.divider()

# -----------------------------
# Aggregated price-value view
# -----------------------------
st.subheader("Price Segment Positioning")
st.markdown(
    """
This chart summarizes how product rating and review intensity change across price ranges.
Bubble size reflects the number of products in each segment.
"""
)

# Optional cap to reduce impact of extreme outliers
plot_df = products.copy()
price_cap = plot_df["price"].quantile(0.99)
plot_df = plot_df[plot_df["price"] <= price_cap]

# Define price bins
bins = [0, 10, 20, 30, 50, 75, 100, 150, 999999]
labels = ["<$10", "$10–20", "$20–30", "$30–50", "$50–75", "$75–100", "$100–150", "$150+"]

plot_df["price_segment"] = pd.cut(
    plot_df["price"],
    bins=bins,
    labels=labels,
    include_lowest=True,
    right=False
)

segment_summary = (
    plot_df.dropna(subset=["price_segment"])
    .groupby("price_segment", observed=False)
    .agg(
        product_count=("price", "size"),
        avg_rating=("average_rating", "mean"),
        median_reviews=("review_count", "median"),
        avg_price=("price", "mean")
    )
    .reset_index()
)

segment_summary = segment_summary[segment_summary["product_count"] > 0]

fig_segment = px.scatter(
    segment_summary,
    x="avg_price",
    y="avg_rating",
    size="product_count",
    color="median_reviews",
    text="price_segment",
    title="Price Segments: Average Price vs Average Rating",
    hover_data={
        "price_segment": True,
        "product_count": True,
        "avg_price": ":.2f",
        "avg_rating": ":.2f",
        "median_reviews": ":,.0f"
    }
)

fig_segment.update_traces(textposition="top center")
fig_segment.update_layout(
    xaxis_title="Average Price in Segment",
    yaxis_title="Average Rating",
    yaxis_range=[max(0, segment_summary["avg_rating"].min() - 0.2), 5.05]
)

st.plotly_chart(fig_segment, use_container_width=True)
