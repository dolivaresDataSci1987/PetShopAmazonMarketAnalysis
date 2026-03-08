import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

from utils.load_data import load_category_competition

st.title("Category Competition")
st.markdown(
    """
This page explores where competition is most intense across animal × product submarkets,
where competitive pressure may still be worth it, and which spaces look more crowded or promising.
"""
)

# =========================================================
# Load data
# =========================================================
competition = load_category_competition().copy()

# =========================================================
# Basic cleaning
# =========================================================
for col in competition.columns:
    if competition[col].dtype == "object":
        competition[col] = competition[col].astype(str).str.strip()

invalid_labels = ["", "nan", "None", "Unknown", "unknown", "N/A"]

# Normalize animal types
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

if "animal_type" in competition.columns:
    competition["animal_type"] = competition["animal_type"].map(animal_mapping)
    competition = competition[competition["animal_type"].isin(valid_animal_order)].copy()

if "product_type" in competition.columns:
    competition["product_type"] = competition["product_type"].astype(str).str.strip()
    competition = competition[~competition["product_type"].isin(invalid_labels)].copy()

# Numeric cleanup
numeric_cols = [
    "product_count",
    "brand_count",
    "avg_price",
    "avg_rating",
    "total_rating_number",
    "competition_score",
    "demand_per_brand",
    "competition_rank"
]

for col in numeric_cols:
    if col in competition.columns:
        competition[col] = pd.to_numeric(competition[col], errors="coerce")

# Drop rows missing key metrics
required_base = ["animal_type", "product_type", "competition_score", "demand_per_brand"]
existing_required = [c for c in required_base if c in competition.columns]
competition = competition.dropna(subset=existing_required).copy()

# Create a readable subcategory label
competition["subcategory"] = competition["animal_type"] + " — " + competition["product_type"]

# Optional filtering of extreme outliers for cleaner scatter sizing
if "product_count" in competition.columns:
    product_cap = competition["product_count"].quantile(0.99)
    competition["product_count_capped"] = competition["product_count"].clip(upper=product_cap)
else:
    competition["product_count_capped"] = 1

# Opportunity signal
if {"demand_per_brand", "competition_score"}.issubset(competition.columns):
    competition["opportunity_signal"] = (
        competition["demand_per_brand"] / (competition["competition_score"] + 1)
    )
else:
    competition["opportunity_signal"] = np.nan

# Crowded signal
if {"competition_score", "brand_count"}.issubset(competition.columns):
    competition["crowded_signal"] = competition["competition_score"] * competition["brand_count"]
else:
    competition["crowded_signal"] = np.nan

# =========================================================
# KPI block
# =========================================================
total_subcategories = len(competition)
total_animals = competition["animal_type"].nunique() if "animal_type" in competition.columns else 0
total_product_types = competition["product_type"].nunique() if "product_type" in competition.columns else 0
avg_competition = competition["competition_score"].mean() if "competition_score" in competition.columns else np.nan
avg_demand_per_brand = competition["demand_per_brand"].mean() if "demand_per_brand" in competition.columns else np.nan
avg_brand_count = competition["brand_count"].mean() if "brand_count" in competition.columns else np.nan

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Subcategories", f"{total_subcategories:,}")
c2.metric("Animal Types", f"{total_animals:,}")
c3.metric("Product Types", f"{total_product_types:,}")
c4.metric("Avg Competition", f"{avg_competition:.2f}" if pd.notna(avg_competition) else "NA")
c5.metric("Avg Demand / Brand", f"{avg_demand_per_brand:,.1f}" if pd.notna(avg_demand_per_brand) else "NA")
c6.metric("Avg Brands / Subcategory", f"{avg_brand_count:.1f}" if pd.notna(avg_brand_count) else "NA")

st.divider()

# =========================================================
# 1) Top categories by competition score
# =========================================================
st.subheader("1. Most Competitive Subcategories")
st.markdown(
    """
This ranking highlights the animal × product spaces with the highest competitive pressure.
"""
)

if {"subcategory", "competition_score"}.issubset(competition.columns):
    top_comp = (
        competition.sort_values("competition_score", ascending=False)
        .head(15)
        .sort_values("competition_score", ascending=True)
    )

    fig_top_comp = px.bar(
        top_comp,
        x="competition_score",
        y="subcategory",
        orientation="h",
        color="brand_count" if "brand_count" in top_comp.columns else None,
        title="Top Subcategories by Competition Score",
        hover_data={
            "animal_type": True if "animal_type" in top_comp.columns else False,
            "product_type": True if "product_type" in top_comp.columns else False,
            "competition_score": ":.2f",
            "brand_count": True if "brand_count" in top_comp.columns else False,
            "product_count": True if "product_count" in top_comp.columns else False,
            "demand_per_brand": ":,.1f" if "demand_per_brand" in top_comp.columns else False,
            "avg_price": ":.2f" if "avg_price" in top_comp.columns else False
        },
        color_continuous_scale="Reds"
    )

    fig_top_comp.update_layout(
        xaxis_title="Competition Score",
        yaxis_title="Subcategory",
        coloraxis_colorbar_title="Brand Count",
        margin=dict(l=20, r=20, t=60, b=20)
    )

    st.plotly_chart(fig_top_comp, use_container_width=True)
else:
    st.info("Required columns for competition ranking are missing.")

st.divider()

# =========================================================
# 2) Competition vs demand per brand
# =========================================================
st.subheader("2. Competition vs Demand per Brand")
st.markdown(
    """
This bubble chart helps distinguish crowded battlegrounds from structurally attractive spaces.
"""
)

required_scatter = {"subcategory", "competition_score", "demand_per_brand"}
if required_scatter.issubset(competition.columns):
    scatter_df = competition.copy()

    # Midlines for quadrant reading
    x_mid = scatter_df["competition_score"].median()
    y_mid = scatter_df["demand_per_brand"].median()

    fig_scatter = px.scatter(
        scatter_df,
        x="competition_score",
        y="demand_per_brand",
        size="product_count_capped",
        color="avg_price" if "avg_price" in scatter_df.columns else None,
        text="subcategory",
        title="Competitive Pressure vs Demand per Brand",
        hover_data={
            "animal_type": True if "animal_type" in scatter_df.columns else False,
            "product_type": True if "product_type" in scatter_df.columns else False,
            "competition_score": ":.2f",
            "demand_per_brand": ":,.1f",
            "brand_count": True if "brand_count" in scatter_df.columns else False,
            "product_count": True if "product_count" in scatter_df.columns else False,
            "avg_price": ":.2f" if "avg_price" in scatter_df.columns else False,
            "avg_rating": ":.2f" if "avg_rating" in scatter_df.columns else False
        },
        color_continuous_scale="Tealgrn"
    )

    fig_scatter.update_traces(
        textposition="top center",
        marker=dict(line=dict(width=1, color="white"))
    )

    fig_scatter.add_vline(x=x_mid, line_dash="dash", opacity=0.5)
    fig_scatter.add_hline(y=y_mid, line_dash="dash", opacity=0.5)

    fig_scatter.update_layout(
        xaxis_title="Competition Score",
        yaxis_title="Demand per Brand",
        coloraxis_colorbar_title="Avg Price",
        margin=dict(l=20, r=20, t=60, b=20)
    )

    st.plotly_chart(fig_scatter, use_container_width=True)
else:
    st.info("Required columns for competition vs demand scatter are missing.")

st.divider()

# =========================================================
# 3) Heatmap: competition score
# =========================================================
st.subheader("3. Competition Heatmap by Animal Type and Product Type")
st.markdown(
    """
This heatmap shows where competitive intensity is structurally concentrated across the market.
"""
)

if {"animal_type", "product_type", "competition_score"}.issubset(competition.columns):
    comp_heat = (
        competition.groupby(["animal_type", "product_type"], as_index=False)["competition_score"]
        .mean()
    )

    comp_matrix = comp_heat.pivot(
        index="animal_type",
        columns="product_type",
        values="competition_score"
    ).fillna(0)

    comp_matrix = comp_matrix.reindex(
        [a for a in valid_animal_order if a in comp_matrix.index]
    )

    # keep most relevant product types only
    ordered_cols = comp_matrix.mean(axis=0).sort_values(ascending=False).head(12).index.tolist()
    comp_matrix = comp_matrix[ordered_cols]

    fig_comp_heat = px.imshow(
        comp_matrix,
        labels=dict(x="Product Type", y="Animal Type", color="Competition Score"),
        aspect="auto",
        color_continuous_scale="Reds",
        title="Competition Score Across Animal × Product Markets"
    )

    fig_comp_heat.update_layout(
        margin=dict(l=20, r=20, t=60, b=20)
    )

    st.plotly_chart(fig_comp_heat, use_container_width=True)
else:
    st.info("Required columns for competition heatmap are missing.")

st.divider()

# =========================================================
# 4) Heatmap: demand per brand
# =========================================================
st.subheader("4. Demand-per-Brand Heatmap by Animal Type and Product Type")
st.markdown(
    """
This heatmap shows where each competing brand captures more demand on average.
"""
)

if {"animal_type", "product_type", "demand_per_brand"}.issubset(competition.columns):
    demand_heat = (
        competition.groupby(["animal_type", "product_type"], as_index=False)["demand_per_brand"]
        .mean()
    )

    demand_matrix = demand_heat.pivot(
        index="animal_type",
        columns="product_type",
        values="demand_per_brand"
    ).fillna(0)

    demand_matrix = demand_matrix.reindex(
        [a for a in valid_animal_order if a in demand_matrix.index]
    )

    ordered_cols = demand_matrix.mean(axis=0).sort_values(ascending=False).head(12).index.tolist()
    demand_matrix = demand_matrix[ordered_cols]

    fig_demand_heat = px.imshow(
        demand_matrix,
        labels=dict(x="Product Type", y="Animal Type", color="Demand per Brand"),
        aspect="auto",
        color_continuous_scale="Blues",
        title="Demand per Brand Across Animal × Product Markets"
    )

    fig_demand_heat.update_layout(
        margin=dict(l=20, r=20, t=60, b=20)
    )

    st.plotly_chart(fig_demand_heat, use_container_width=True)
else:
    st.info("Required columns for demand-per-brand heatmap are missing.")

st.divider()

# =========================================================
# 5) Crowded vs promising rankings
# =========================================================
st.subheader("5. Crowded vs Promising Subcategories")
st.markdown(
    """
These rankings separate the most crowded spaces from subcategories that may offer a better competition–reward balance.
"""
)

left, right = st.columns(2)

with left:
    st.markdown("**Most Crowded**")

    if {"subcategory", "crowded_signal"}.issubset(competition.columns):
        crowded_df = (
            competition.dropna(subset=["crowded_signal"])
            .sort_values("crowded_signal", ascending=False)
            .head(10)
            .sort_values("crowded_signal", ascending=True)
        )

        fig_crowded = px.bar(
            crowded_df,
            x="crowded_signal",
            y="subcategory",
            orientation="h",
            color="competition_score" if "competition_score" in crowded_df.columns else None,
            title="Most Crowded Subcategories",
            hover_data={
                "competition_score": ":.2f" if "competition_score" in crowded_df.columns else False,
                "brand_count": True if "brand_count" in crowded_df.columns else False,
                "product_count": True if "product_count" in crowded_df.columns else False,
                "demand_per_brand": ":,.1f" if "demand_per_brand" in crowded_df.columns else False
            },
            color_continuous_scale="Reds"
        )

        fig_crowded.update_layout(
            xaxis_title="Crowdedness Signal",
            yaxis_title="Subcategory",
            coloraxis_colorbar_title="Competition",
            margin=dict(l=20, r=20, t=60, b=20)
        )

        st.plotly_chart(fig_crowded, use_container_width=True)
    else:
        st.info("Crowdedness signal could not be computed.")

with right:
    st.markdown("**Most Promising**")

    if {"subcategory", "opportunity_signal"}.issubset(competition.columns):
        promising_df = competition.copy()

        # keep only lower-to-mid competition spaces for more realistic "promising" ranking
        if "competition_score" in promising_df.columns:
            comp_threshold = promising_df["competition_score"].quantile(0.65)
            promising_df = promising_df[promising_df["competition_score"] <= comp_threshold].copy()

        promising_df = (
            promising_df.dropna(subset=["opportunity_signal"])
            .sort_values("opportunity_signal", ascending=False)
            .head(10)
            .sort_values("opportunity_signal", ascending=True)
        )

        fig_promising = px.bar(
            promising_df,
            x="opportunity_signal",
            y="subcategory",
            orientation="h",
            color="demand_per_brand" if "demand_per_brand" in promising_df.columns else None,
            title="Most Promising Subcategories",
            hover_data={
                "competition_score": ":.2f" if "competition_score" in promising_df.columns else False,
                "demand_per_brand": ":,.1f" if "demand_per_brand" in promising_df.columns else False,
                "brand_count": True if "brand_count" in promising_df.columns else False,
                "product_count": True if "product_count" in promising_df.columns else False,
                "avg_price": ":.2f" if "avg_price" in promising_df.columns else False
            },
            color_continuous_scale="Blues"
        )

        fig_promising.update_layout(
            xaxis_title="Opportunity Signal",
            yaxis_title="Subcategory",
            coloraxis_colorbar_title="Demand / Brand",
            margin=dict(l=20, r=20, t=60, b=20)
        )

        st.plotly_chart(fig_promising, use_container_width=True)
    else:
        st.info("Opportunity signal could not be computed.")

st.divider()

# =========================================================
# Optional data view
# =========================================================
with st.expander("View underlying competition table"):
    display_cols = [
        c for c in [
            "animal_type",
            "product_type",
            "product_count",
            "brand_count",
            "avg_price",
            "avg_rating",
            "total_rating_number",
            "competition_score",
            "demand_per_brand",
            "competition_rank",
            "opportunity_signal"
        ]
        if c in competition.columns
    ]
    st.dataframe(
        competition[display_cols].sort_values(
            "competition_score", ascending=False
        ),
        use_container_width=True
    )
