import streamlit as st
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

if "category_l1" in products.columns:
    cat1_summary = (
        products.groupby("category_l1", dropna=False)
        .size()
        .reset_index(name="product_count")
        .sort_values("product_count", ascending=False)
        .head(15)
    )

    with left:
        fig_cat1 = px.bar(
            cat1_summary,
            x="category_l1",
            y="product_count",
            title="Products by Main Category"
        )
        fig_cat1.update_layout(
            xaxis_title="Category L1",
            yaxis_title="Product Count"
        )
        st.plotly_chart(fig_cat1, use_container_width=True)
else:
    with left:
        st.info("Column `category_l1` not found in products_master.csv")

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
# Scatter plot
# -----------------------------
st.subheader("Price vs Rating")

hover_cols = [
    col for col in [
        "product_title",
        "brand",
        "category_l1",
        "category_l2",
        "category_l3"
    ]
    if col in products.columns
]

sample_df = products.sample(min(len(products), 3000), random_state=42)

fig_scatter = px.scatter(
    sample_df,
    x="price",
    y="average_rating",
    size="review_count",
    hover_data=hover_cols,
    title="Price, Rating, and Review Volume"
)

fig_scatter.update_layout(
    xaxis_title="Price",
    yaxis_title="Average Rating"
)

st.plotly_chart(fig_scatter, use_container_width=True)
