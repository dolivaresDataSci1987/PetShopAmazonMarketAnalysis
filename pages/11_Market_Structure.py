import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

from utils.load_data import load_products

st.title("Market Structure")
st.markdown(
    """
This section explores how the Amazon Pet Products market is structurally organized
across price tiers, animal types, and brand/product portfolios.
"""
)

# =========================================================
# Load data
# =========================================================
products = load_products().copy()

# =========================================================
# Basic cleaning
# =========================================================
products = products.dropna(subset=["price", "average_rating", "review_count"])
products = products[products["price"] > 0].copy()

for col in ["brand", "category_l2", "category_l3"]:
    if col in products.columns:
        products[col] = products[col].astype(str).str.strip()

products["brand"] = products["brand"]
products["animal_type_raw"] = products["category_l2"]
products["product_type_raw"] = products["category_l3"]

invalid_labels = ["", "nan", "None", "Unknown", "unknown", "N/A"]

products = products[
    ~products["brand"].isin(invalid_labels) &
    ~products["animal_type_raw"].isin(invalid_labels) &
    ~products["product_type_raw"].isin(invalid_labels)
].copy()

# =========================================================
# Normalize animal types
# =========================================================
animal_mapping = {
    "Dogs": "Dogs",
    "Dog": "Dogs",
    "Cats": "Cats",
    "Cat": "Cats",
    "Fish & Aquatic Pets": "Fish & Aquatic Pets",
    "Fish&Auatics Pets": "Fish & Aquatic Pets",
    "Fish & Aquatics Pets": "Fish & Aquatic Pets",
    "Aquatic Pets": "Fish & Aquatic Pets",
    "Birds": "Birds",
    "Bird": "Birds",
    "Small Animals": "Small Animals",
    "Small Animal": "Small Animals",
    "Reptiles & Amphibians": "Reptiles & Amphibians",
    "Repiteles &bAmphibians": "Reptiles & Amphibians",
    "Reptiles": "Reptiles & Amphibians",
    "Horses": "Horses",
    "Horse": "Horses",
}

valid_animal_order = [
    "Dogs",
    "Cats",
    "Fish & Aquatic Pets",
    "Birds",
    "Small Animals",
    "Reptiles & Amphibians",
    "Horses"
]

products["animal_type"] = products["animal_type_raw"].map(animal_mapping)
products = products[products["animal_type"].isin(valid_animal_order)].copy()

# =========================================================
# Normalize product types
# =========================================================
product_type_mapping = {
    "Food": "Food",
    "Dry Food": "Food",
    "Wet Food": "Food",
    "Treats": "Treats",
    "Biscuits": "Treats",
    "Chews": "Treats",
    "Toys": "Toys",
    "Toy": "Toys",
    "Beds": "Beds",
    "Bed": "Beds",
    "Collars": "Collars",
    "Leashes": "Leashes",
    "Bowls": "Bowls",
    "Grooming": "Grooming",
    "Shampoos": "Grooming",
    "Health Supplies": "Health Supplies",
    "Supplements": "Health Supplies",
    "Vitamins": "Health Supplies",
    "Waste Bags": "Waste & Litter",
    "Litter": "Waste & Litter",
    "Aquariums": "Aquariums & Accessories",
    "Filters": "Aquariums & Accessories",
    "Habitats": "Habitats & Cages",
    "Cages": "Habitats & Cages",
}

products["product_type_clean"] = products["product_type_raw"].replace(product_type_mapping)

# Keep a capped version for cleaner price visuals
price_cap = products["price"].quantile(0.99)
plot_products = products[products["price"] <= price_cap].copy()

# =========================================================
# Price segments
# =========================================================
bins = [0, 10, 20, 30, 50, 75, 100, 150, np.inf]
labels = ["$0–10", "$10–20", "$20–30", "$30–50", "$50–75", "$75–100", "$100–150", "$150+"]

plot_products["price_segment"] = pd.cut(
    plot_products["price"],
    bins=bins,
    labels=labels,
    include_lowest=True,
    right=False
)

# =========================================================
# KPI block
# =========================================================
total_products = len(products)
total_brands = products["brand"].nunique()
total_animal_types = products["animal_type"].nunique()
total_product_types = products["product_type_clean"].nunique()
avg_price = products["price"].mean()
median_price = products["price"].median()

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Products", f"{total_products:,}")
c2.metric("Brands", f"{total_brands:,}")
c3.metric("Animal Types", f"{total_animal_types:,}")
c4.metric("Product Types", f"{total_product_types:,}")
c5.metric("Avg Price", f"${avg_price:,.2f}")
c6.metric("Median Price", f"${median_price:,.2f}")

st.divider()

# =========================================================
# 1) Brand distribution by price range
# =========================================================
st.subheader("1. Brand Distribution Across Price Segments")
st.markdown(
    """
This view shows how many distinct brands compete in each price tier,
together with the number of listed products in that segment.
"""
)

brand_price_summary = (
    plot_products.groupby("price_segment", observed=False)
    .agg(
        brand_count=("brand", "nunique"),
        product_count=("price", "size"),
        avg_rating=("average_rating", "mean"),
        avg_price=("price", "mean")
    )
    .reset_index()
)

brand_price_summary = brand_price_summary[brand_price_summary["product_count"] > 0]

fig_brand_price = px.scatter(
    brand_price_summary,
    x="price_segment",
    y="brand_count",
    size="product_count",
    color="avg_rating",
    text="brand_count",
    title="Brand Presence by Price Segment",
    hover_data={
        "price_segment": True,
        "brand_count": True,
        "product_count": True,
        "avg_price": ":.2f",
        "avg_rating": ":.2f"
    },
    color_continuous_scale="Blues"
)

fig_brand_price.update_traces(
    mode="markers+text",
    textposition="top center",
    marker=dict(line=dict(width=1, color="white"))
)

fig_brand_price.update_layout(
    xaxis_title="Price Segment",
    yaxis_title="Number of Brands",
    coloraxis_colorbar_title="Avg Rating",
    margin=dict(l=20, r=20, t=60, b=20)
)

st.plotly_chart(fig_brand_price, use_container_width=True)

st.divider()

# =========================================================
# 2) Product-level price distribution by animal type
# =========================================================
st.subheader("2. Product-Level Price Distribution by Animal Type")
st.markdown(
    """
This box plot shows how product prices are distributed within each animal category.
It highlights which markets are tighter and which are more price-dispersed.
"""
)

fig_box = px.box(
    plot_products,
    x="animal_type",
    y="price",
    color="animal_type",
    category_orders={"animal_type": valid_animal_order},
    points=False,
    title="Price Range per Product by Animal Type"
)

fig_box.update_layout(
    xaxis_title="Animal Type",
    yaxis_title="Price",
    showlegend=False,
    margin=dict(l=20, r=20, t=60, b=20)
)

st.plotly_chart(fig_box, use_container_width=True)

st.divider()

# =========================================================
# 3) Product type by brand
# =========================================================
st.subheader("3. Product-Type Portfolio by Brand")
st.markdown(
    """
This heatmap shows how top brands are distributed across major product types.
Darker cells indicate stronger portfolio presence.
"""
)

top_brands = (
    plot_products.groupby("brand")
    .size()
    .sort_values(ascending=False)
    .head(15)
    .index.tolist()
)

top_product_types = (
    plot_products.groupby("product_type_clean")
    .size()
    .sort_values(ascending=False)
    .head(12)
    .index.tolist()
)

brand_product_heatmap = (
    plot_products[
        plot_products["brand"].isin(top_brands) &
        plot_products["product_type_clean"].isin(top_product_types)
    ]
    .groupby(["brand", "product_type_clean"])
    .size()
    .reset_index(name="product_count")
)

heatmap_matrix = brand_product_heatmap.pivot(
    index="brand",
    columns="product_type_clean",
    values="product_count"
).fillna(0)

heatmap_matrix = heatmap_matrix.loc[
    heatmap_matrix.sum(axis=1).sort_values(ascending=False).index
]

fig_heatmap_brand = px.imshow(
    heatmap_matrix,
    labels=dict(x="Product Type", y="Brand", color="Product Count"),
    aspect="auto",
    color_continuous_scale="Blues",
    title="Top Brands vs Top Product Types"
)

fig_heatmap_brand.update_layout(
    margin=dict(l=20, r=20, t=60, b=20)
)

st.plotly_chart(fig_heatmap_brand, use_container_width=True)

st.divider()

# =========================================================
# 4) Product type composition by animal type
# =========================================================
st.subheader("4. Product-Type Composition by Animal Type")
st.markdown(
    """
This heatmap shows which product types dominate each animal market.
It helps reveal category-specific structural patterns.
"""
)

top_product_types_animal = (
    plot_products.groupby("product_type_clean")
    .size()
    .sort_values(ascending=False)
    .head(12)
    .index.tolist()
)

animal_product_heatmap = (
    plot_products[
        plot_products["product_type_clean"].isin(top_product_types_animal)
    ]
    .groupby(["animal_type", "product_type_clean"])
    .size()
    .reset_index(name="product_count")
)

animal_product_matrix = animal_product_heatmap.pivot(
    index="animal_type",
    columns="product_type_clean",
    values="product_count"
).fillna(0)

animal_product_matrix = animal_product_matrix.reindex(valid_animal_order)

fig_heatmap_animal = px.imshow(
    animal_product_matrix,
    labels=dict(x="Product Type", y="Animal Type", color="Product Count"),
    aspect="auto",
    color_continuous_scale="Teal",
    title="Animal Types vs Product Types"
)

fig_heatmap_animal.update_layout(
    margin=dict(l=20, r=20, t=60, b=20)
)

st.plotly_chart(fig_heatmap_animal, use_container_width=True)

st.divider()

# =========================================================
# 5) Price tier composition by animal type
# =========================================================
st.subheader("5. Price-Tier Composition by Animal Type")
st.markdown(
    """
This stacked bar chart shows how each animal market is distributed across price tiers.
It helps identify whether a category is concentrated in low, mid, or premium price bands.
"""
)

animal_price_mix = (
    plot_products.groupby(["animal_type", "price_segment"], observed=False)
    .size()
    .reset_index(name="product_count")
)

animal_totals = (
    animal_price_mix.groupby("animal_type")["product_count"]
    .sum()
    .reset_index(name="total_products")
)

animal_price_mix = animal_price_mix.merge(animal_totals, on="animal_type", how="left")
animal_price_mix["share_pct"] = (
    animal_price_mix["product_count"] / animal_price_mix["total_products"] * 100
)

fig_stacked = px.bar(
    animal_price_mix,
    x="animal_type",
    y="share_pct",
    color="price_segment",
    category_orders={
        "animal_type": valid_animal_order,
        "price_segment": labels
    },
    title="Price Tier Mix Within Each Animal Type"
)

fig_stacked.update_layout(
    xaxis_title="Animal Type",
    yaxis_title="Share of Products (%)",
    legend_title="Price Segment",
    barmode="stack",
    margin=dict(l=20, r=20, t=60, b=20)
)

st.plotly_chart(fig_stacked, use_container_width=True)

st.divider()

# =========================================================
# 6) Brand specialization across animal markets
# =========================================================
st.subheader("6. Brand Specialization Across Animal Markets")
st.markdown(
    """
This heatmap shows whether leading brands are specialized in one animal market
or diversified across several.
"""
)

top_brands_specialization = (
    plot_products.groupby("brand")
    .size()
    .sort_values(ascending=False)
    .head(15)
    .index.tolist()
)

brand_animal_heatmap = (
    plot_products[
        plot_products["brand"].isin(top_brands_specialization)
    ]
    .groupby(["brand", "animal_type"])
    .size()
    .reset_index(name="product_count")
)

brand_animal_matrix = brand_animal_heatmap.pivot(
    index="brand",
    columns="animal_type",
    values="product_count"
).fillna(0)

brand_animal_matrix = brand_animal_matrix[
    [c for c in valid_animal_order if c in brand_animal_matrix.columns]
]

brand_animal_matrix = brand_animal_matrix.loc[
    brand_animal_matrix.sum(axis=1).sort_values(ascending=False).index
]

fig_heatmap_specialization = px.imshow(
    brand_animal_matrix,
    labels=dict(x="Animal Type", y="Brand", color="Product Count"),
    aspect="auto",
    color_continuous_scale="Purples",
    title="Top Brands Across Animal Markets"
)

fig_heatmap_specialization.update_layout(
    margin=dict(l=20, r=20, t=60, b=20)
)

st.plotly_chart(fig_heatmap_specialization, use_container_width=True)

st.divider()

# =========================================================
# 7) Brand portfolio breadth
# =========================================================
st.subheader("7. Brand Portfolio Breadth")
st.markdown(
    """
This chart shows how many distinct product types each leading brand covers.
It helps distinguish specialist brands from broader portfolio players.
"""
)

brand_portfolio = (
    plot_products.groupby("brand")
    .agg(
        product_count=("price", "size"),
        product_type_count=("product_type_clean", "nunique"),
        animal_type_count=("animal_type", "nunique")
    )
    .reset_index()
)

brand_portfolio = brand_portfolio.sort_values(
    ["product_type_count", "product_count"],
    ascending=[False, False]
).head(20)

fig_portfolio = px.scatter(
    brand_portfolio,
    x="product_type_count",
    y="product_count",
    size="animal_type_count",
    color="animal_type_count",
    text="brand",
    title="Brand Breadth: Product-Type Coverage vs Product Count",
    hover_data={
        "brand": True,
        "product_type_count": True,
        "product_count": True,
        "animal_type_count": True
    },
    color_continuous_scale="Sunset"
)

fig_portfolio.update_traces(
    textposition="top center",
    marker=dict(line=dict(width=1, color="white"))
)

fig_portfolio.update_layout(
    xaxis_title="Distinct Product Types Covered",
    yaxis_title="Total Product Count",
    coloraxis_colorbar_title="Animal Types",
    margin=dict(l=20, r=20, t=60, b=20)
)

st.plotly_chart(fig_portfolio, use_container_width=True)
