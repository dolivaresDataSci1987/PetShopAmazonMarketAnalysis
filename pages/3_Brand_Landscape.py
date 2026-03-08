import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

from utils.load_data import (
    load_brand_summary,
    load_brand_product_matrix,
    load_brand_animal_matrix
)

st.title("Brand Landscape")
st.markdown(
    """
This page explores which brands lead the market, how they are positioned,
and where they specialize across animal types and product categories.
"""
)

# =========================================================
# Load data
# =========================================================
brand_summary = load_brand_summary().copy()
brand_product_matrix = load_brand_product_matrix().copy()
brand_animal_matrix = load_brand_animal_matrix().copy()

# =========================================================
# Basic cleaning
# =========================================================
invalid_labels = ["", "nan", "None", "Unknown", "unknown", "N/A"]

if "brand" in brand_summary.columns:
    brand_summary["brand"] = brand_summary["brand"].astype(str).str.strip()
    brand_summary = brand_summary[~brand_summary["brand"].isin(invalid_labels)].copy()

if "brand" in brand_product_matrix.columns:
    brand_product_matrix["brand"] = brand_product_matrix["brand"].astype(str).str.strip()
if "product_type" in brand_product_matrix.columns:
    brand_product_matrix["product_type"] = brand_product_matrix["product_type"].astype(str).str.strip()
brand_product_matrix = brand_product_matrix[
    ~brand_product_matrix["brand"].isin(invalid_labels)
].copy()

if "brand" in brand_animal_matrix.columns:
    brand_animal_matrix["brand"] = brand_animal_matrix["brand"].astype(str).str.strip()
if "animal_type" in brand_animal_matrix.columns:
    brand_animal_matrix["animal_type"] = brand_animal_matrix["animal_type"].astype(str).str.strip()
brand_animal_matrix = brand_animal_matrix[
    ~brand_animal_matrix["brand"].isin(invalid_labels)
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

if "animal_type" in brand_animal_matrix.columns:
    brand_animal_matrix["animal_type"] = brand_animal_matrix["animal_type"].map(animal_mapping)
    brand_animal_matrix = brand_animal_matrix[
        brand_animal_matrix["animal_type"].isin(valid_animal_order)
    ].copy()

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

if "product_type" in brand_product_matrix.columns:
    brand_product_matrix["product_type_clean"] = (
        brand_product_matrix["product_type"]
        .replace(product_type_mapping)
        .astype(str)
        .str.strip()
    )
else:
    brand_product_matrix["product_type_clean"] = "Unknown"

# =========================================================
# Numeric cleanup
# =========================================================
for df in [brand_summary, brand_product_matrix, brand_animal_matrix]:
    for col in df.columns:
        if df[col].dtype == "object":
            continue

# Fill likely numeric cols if present
numeric_fill_zero = [
    "product_count",
    "total_rating_number",
    "total_review_count",
    "demand_proxy",
    "animal_types_count",
    "product_types_count",
    "brand_strength_score"
]
numeric_fill_nan = [
    "avg_price",
    "median_price",
    "avg_rating",
    "avg_review_rating",
    "avg_verified_purchase_ratio"
]

for col in numeric_fill_zero:
    if col in brand_summary.columns:
        brand_summary[col] = pd.to_numeric(brand_summary[col], errors="coerce").fillna(0)

for col in numeric_fill_nan:
    if col in brand_summary.columns:
        brand_summary[col] = pd.to_numeric(brand_summary[col], errors="coerce")

for df in [brand_product_matrix, brand_animal_matrix]:
    for col in ["product_count", "avg_price", "avg_rating", "demand_proxy"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

# =========================================================
# Keep relevant brands only
# =========================================================
brand_summary = brand_summary.dropna(subset=["brand"]).copy()

# Remove tiny/noisy brands if needed for cleaner charts
brand_summary_filtered = brand_summary.copy()
if "product_count" in brand_summary_filtered.columns:
    brand_summary_filtered = brand_summary_filtered[brand_summary_filtered["product_count"] > 0].copy()

# =========================================================
# KPI block
# =========================================================
total_brands = brand_summary_filtered["brand"].nunique()

total_products = int(brand_summary_filtered["product_count"].sum()) if "product_count" in brand_summary_filtered.columns else 0
avg_brand_price = brand_summary_filtered["avg_price"].mean() if "avg_price" in brand_summary_filtered.columns else np.nan
avg_brand_rating = brand_summary_filtered["avg_rating"].mean() if "avg_rating" in brand_summary_filtered.columns else np.nan
avg_product_types = brand_summary_filtered["product_types_count"].mean() if "product_types_count" in brand_summary_filtered.columns else np.nan
avg_animal_types = brand_summary_filtered["animal_types_count"].mean() if "animal_types_count" in brand_summary_filtered.columns else np.nan

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Brands", f"{total_brands:,}")
c2.metric("Total Products", f"{total_products:,}")
c3.metric("Avg Brand Price", f"${avg_brand_price:,.2f}" if pd.notna(avg_brand_price) else "NA")
c4.metric("Avg Brand Rating", f"{avg_brand_rating:.2f}" if pd.notna(avg_brand_rating) else "NA")
c5.metric("Avg Product-Type Breadth", f"{avg_product_types:.1f}" if pd.notna(avg_product_types) else "NA")
c6.metric("Avg Animal-Type Breadth", f"{avg_animal_types:.1f}" if pd.notna(avg_animal_types) else "NA")

st.divider()

# =========================================================
# A) What brands lead?
# =========================================================
st.header("A. What brands lead the market?")

left, right = st.columns(2)

with left:
    st.subheader("Top Brands by Brand Strength Score")

    if {"brand", "brand_strength_score"}.issubset(brand_summary_filtered.columns):
        top_strength = (
            brand_summary_filtered.sort_values("brand_strength_score", ascending=False)
            .head(15)
            .sort_values("brand_strength_score", ascending=True)
        )

        fig_strength = px.bar(
            top_strength,
            x="brand_strength_score",
            y="brand",
            orientation="h",
            color="avg_price" if "avg_price" in top_strength.columns else None,
            title="Top Brands by Brand Strength Score",
            hover_data={
                "brand": True,
                "product_count": True if "product_count" in top_strength.columns else False,
                "demand_proxy": True if "demand_proxy" in top_strength.columns else False,
                "avg_price": ":.2f" if "avg_price" in top_strength.columns else False,
                "avg_rating": ":.2f" if "avg_rating" in top_strength.columns else False
            }
        )
        fig_strength.update_layout(
            xaxis_title="Brand Strength Score",
            yaxis_title="Brand",
            coloraxis_colorbar_title="Avg Price",
            margin=dict(l=20, r=20, t=60, b=20)
        )
        st.plotly_chart(fig_strength, use_container_width=True)
    else:
        st.info("Required columns for brand strength ranking are missing.")

with right:
    st.subheader("Top Brands by Demand Proxy")

    if {"brand", "demand_proxy"}.issubset(brand_summary_filtered.columns):
        top_demand = (
            brand_summary_filtered.sort_values("demand_proxy", ascending=False)
            .head(15)
            .sort_values("demand_proxy", ascending=True)
        )

        fig_demand = px.bar(
            top_demand,
            x="demand_proxy",
            y="brand",
            orientation="h",
            color="avg_rating" if "avg_rating" in top_demand.columns else None,
            title="Top Brands by Demand Proxy",
            hover_data={
                "brand": True,
                "product_count": True if "product_count" in top_demand.columns else False,
                "brand_strength_score": ":.2f" if "brand_strength_score" in top_demand.columns else False,
                "avg_price": ":.2f" if "avg_price" in top_demand.columns else False,
                "avg_rating": ":.2f" if "avg_rating" in top_demand.columns else False
            }
        )
        fig_demand.update_layout(
            xaxis_title="Demand Proxy",
            yaxis_title="Brand",
            coloraxis_colorbar_title="Avg Rating",
            margin=dict(l=20, r=20, t=60, b=20)
        )
        st.plotly_chart(fig_demand, use_container_width=True)
    else:
        st.info("Required columns for demand ranking are missing.")

st.subheader("Scale vs Strength")
st.markdown(
    """
This bubble chart compares portfolio scale with overall brand strength.
Bubble size reflects demand proxy and color reflects average price.
"""
)

required_cols_scale = {"brand", "product_count", "brand_strength_score"}
if required_cols_scale.issubset(brand_summary_filtered.columns):
    scale_df = brand_summary_filtered.copy()

    if "demand_proxy" not in scale_df.columns:
        scale_df["demand_proxy"] = 1

    scale_df = scale_df.sort_values("demand_proxy", ascending=False).head(30)

    fig_scale_strength = px.scatter(
        scale_df,
        x="product_count",
        y="brand_strength_score",
        size="demand_proxy",
        color="avg_price" if "avg_price" in scale_df.columns else None,
        text="brand",
        title="Brand Scale vs Brand Strength",
        hover_data={
            "brand": True,
            "product_count": True,
            "brand_strength_score": ":.2f",
            "demand_proxy": ":,.0f" if "demand_proxy" in scale_df.columns else False,
            "avg_price": ":.2f" if "avg_price" in scale_df.columns else False,
            "avg_rating": ":.2f" if "avg_rating" in scale_df.columns else False,
            "product_types_count": True if "product_types_count" in scale_df.columns else False,
            "animal_types_count": True if "animal_types_count" in scale_df.columns else False
        },
        color_continuous_scale="Blues"
    )

    fig_scale_strength.update_traces(
        textposition="top center",
        marker=dict(line=dict(width=1, color="white"))
    )
    fig_scale_strength.update_layout(
        xaxis_title="Product Count",
        yaxis_title="Brand Strength Score",
        coloraxis_colorbar_title="Avg Price",
        margin=dict(l=20, r=20, t=60, b=20)
    )

    st.plotly_chart(fig_scale_strength, use_container_width=True)
else:
    st.info("Required columns for the scale vs strength chart are missing.")

st.divider()

# =========================================================
# B) What kind of players are they?
# =========================================================
st.header("B. What kind of players are they?")

left, right = st.columns(2)

with left:
    st.subheader("Brand Breadth Map")
    st.markdown(
        """
        This chart distinguishes specialist brands from broader portfolio players.
        """
    )

    required_cols_breadth = {"brand", "product_types_count", "animal_types_count"}
    if required_cols_breadth.issubset(brand_summary_filtered.columns):
        breadth_df = brand_summary_filtered.copy()

        if "product_count" not in breadth_df.columns:
            breadth_df["product_count"] = 1

        if "demand_proxy" not in breadth_df.columns:
            breadth_df["demand_proxy"] = 1

        breadth_df = breadth_df.sort_values("demand_proxy", ascending=False).head(30)

        fig_breadth = px.scatter(
            breadth_df,
            x="product_types_count",
            y="animal_types_count",
            size="product_count",
            color="demand_proxy",
            text="brand",
            title="Breadth Map: Product-Type vs Animal-Type Coverage",
            hover_data={
                "brand": True,
                "product_types_count": True,
                "animal_types_count": True,
                "product_count": True,
                "demand_proxy": ":,.0f",
                "avg_price": ":.2f" if "avg_price" in breadth_df.columns else False,
                "avg_rating": ":.2f" if "avg_rating" in breadth_df.columns else False
            },
            color_continuous_scale="Tealgrn"
        )

        fig_breadth.update_traces(
            textposition="top center",
            marker=dict(line=dict(width=1, color="white"))
        )
        fig_breadth.update_layout(
            xaxis_title="Distinct Product Types",
            yaxis_title="Distinct Animal Types",
            coloraxis_colorbar_title="Demand Proxy",
            margin=dict(l=20, r=20, t=60, b=20)
        )

        st.plotly_chart(fig_breadth, use_container_width=True)
    else:
        st.info("Required columns for the breadth map are missing.")

with right:
    st.subheader("Price Positioning Map")
    st.markdown(
        """
        This chart shows how leading brands are positioned by price and perceived quality.
        """
    )

    price_col = "median_price" if "median_price" in brand_summary_filtered.columns else "avg_price"
    rating_col = "avg_rating" if "avg_rating" in brand_summary_filtered.columns else None

    if price_col in brand_summary_filtered.columns and rating_col is not None:
        position_df = brand_summary_filtered.copy()

        if "demand_proxy" not in position_df.columns:
            position_df["demand_proxy"] = 1

        position_df = position_df.sort_values("demand_proxy", ascending=False).head(30)

        fig_position = px.scatter(
            position_df,
            x=price_col,
            y=rating_col,
            size="demand_proxy",
            color="brand_strength_score" if "brand_strength_score" in position_df.columns else None,
            text="brand",
            title="Price Positioning of Leading Brands",
            hover_data={
                "brand": True,
                price_col: ":.2f",
                rating_col: ":.2f",
                "demand_proxy": ":,.0f",
                "product_count": True if "product_count" in position_df.columns else False,
                "product_types_count": True if "product_types_count" in position_df.columns else False,
                "animal_types_count": True if "animal_types_count" in position_df.columns else False
            },
            color_continuous_scale="Sunset"
        )

        fig_position.update_traces(
            textposition="top center",
            marker=dict(line=dict(width=1, color="white"))
        )
        fig_position.update_layout(
            xaxis_title="Median Price" if price_col == "median_price" else "Average Price",
            yaxis_title="Average Rating",
            coloraxis_colorbar_title="Brand Strength",
            margin=dict(l=20, r=20, t=60, b=20)
        )

        st.plotly_chart(fig_position, use_container_width=True)
    else:
        st.info("Required columns for the price positioning map are missing.")

st.divider()

# =========================================================
# C) Where are they specialized?
# =========================================================
st.header("C. Where are brands specialized?")

# Top brands to show in heatmaps
if "demand_proxy" in brand_summary_filtered.columns:
    heatmap_brands = (
        brand_summary_filtered.sort_values("demand_proxy", ascending=False)
        .head(15)["brand"]
        .tolist()
    )
else:
    heatmap_brands = (
        brand_summary_filtered.sort_values("product_count", ascending=False)
        .head(15)["brand"]
        .tolist()
        if "product_count" in brand_summary_filtered.columns else brand_summary_filtered["brand"].head(15).tolist()
    )

left, right = st.columns(2)

with left:
    st.subheader("Brand Specialization by Animal Type")
    st.markdown(
        """
        Darker cells indicate stronger presence within each animal market.
        """
    )

    if {"brand", "animal_type"}.issubset(brand_animal_matrix.columns):
        animal_value_col = "demand_proxy" if "demand_proxy" in brand_animal_matrix.columns else "product_count"

        animal_heat = (
            brand_animal_matrix[
                brand_animal_matrix["brand"].isin(heatmap_brands)
            ]
            .groupby(["brand", "animal_type"], as_index=False)[animal_value_col]
            .sum()
        )

        animal_matrix = animal_heat.pivot(
            index="brand",
            columns="animal_type",
            values=animal_value_col
        ).fillna(0)

        animal_matrix = animal_matrix.reindex(index=heatmap_brands)
        animal_matrix = animal_matrix[[c for c in valid_animal_order if c in animal_matrix.columns]]

        fig_animal_heat = px.imshow(
            animal_matrix,
            labels=dict(
                x="Animal Type",
                y="Brand",
                color="Demand Proxy" if animal_value_col == "demand_proxy" else "Product Count"
            ),
            aspect="auto",
            color_continuous_scale="Purples",
            title="Top Brands Across Animal Markets"
        )

        fig_animal_heat.update_layout(
            margin=dict(l=20, r=20, t=60, b=20)
        )

        st.plotly_chart(fig_animal_heat, use_container_width=True)
    else:
        st.info("Required columns for the animal specialization heatmap are missing.")

with right:
    st.subheader("Brand Specialization by Product Type")
    st.markdown(
        """
        This view highlights the product-type DNA of each leading brand.
        """
    )

    if {"brand", "product_type_clean"}.issubset(brand_product_matrix.columns):
        product_value_col = "product_count" if "product_count" in brand_product_matrix.columns else None

        if product_value_col is not None:
            top_product_types = (
                brand_product_matrix.groupby("product_type_clean")[product_value_col]
                .sum()
                .sort_values(ascending=False)
                .head(12)
                .index.tolist()
            )

            product_heat = (
                brand_product_matrix[
                    brand_product_matrix["brand"].isin(heatmap_brands) &
                    brand_product_matrix["product_type_clean"].isin(top_product_types)
                ]
                .groupby(["brand", "product_type_clean"], as_index=False)[product_value_col]
                .sum()
            )

            product_matrix = product_heat.pivot(
                index="brand",
                columns="product_type_clean",
                values=product_value_col
            ).fillna(0)

            product_matrix = product_matrix.reindex(index=heatmap_brands)

            ordered_cols = (
                product_matrix.sum(axis=0).sort_values(ascending=False).index.tolist()
            )
            product_matrix = product_matrix[ordered_cols]

            fig_product_heat = px.imshow(
                product_matrix,
                labels=dict(
                    x="Product Type",
                    y="Brand",
                    color="Product Count"
                ),
                aspect="auto",
                color_continuous_scale="Blues",
                title="Top Brands Across Product Types"
            )

            fig_product_heat.update_layout(
                margin=dict(l=20, r=20, t=60, b=20)
            )

            st.plotly_chart(fig_product_heat, use_container_width=True)
        else:
            st.info("Required product count column is missing.")
    else:
        st.info("Required columns for the product specialization heatmap are missing.")
