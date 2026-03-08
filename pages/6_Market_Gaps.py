import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

from utils.load_data import load_market_gaps

st.title("Market Gap Analysis")
st.markdown(
    """
This page identifies potential whitespace areas in the market:
segments that may show room for new products, stronger positioning, or unmet demand.
"""
)

# =========================================================
# Load data
# =========================================================
gaps = load_market_gaps().copy()

# =========================================================
# Basic cleaning
# =========================================================
for col in gaps.columns:
    if gaps[col].dtype == "object":
        gaps[col] = gaps[col].astype(str).str.strip()

invalid_labels = ["", "nan", "None", "Unknown", "unknown", "N/A"]

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

if "animal_type" in gaps.columns:
    gaps["animal_type"] = gaps["animal_type"].map(animal_mapping)
    gaps = gaps[gaps["animal_type"].isin(valid_animal_order)].copy()

if "product_type" in gaps.columns:
    gaps = gaps[~gaps["product_type"].isin(invalid_labels)].copy()

numeric_cols = [
    "product_count",
    "brand_count",
    "avg_price",
    "avg_rating",
    "total_rating_number",
    "demand_proxy",
    "demand_per_brand",
    "competition_score",
    "gap_score",
    "gap_rank",
    "opportunity_score",
    "opportunity_rank",
]

for col in numeric_cols:
    if col in gaps.columns:
        gaps[col] = pd.to_numeric(gaps[col], errors="coerce")

required_cols = ["animal_type", "product_type", "gap_score"]
gaps = gaps.dropna(subset=[c for c in required_cols if c in gaps.columns]).copy()

gaps["subcategory"] = gaps["animal_type"] + " — " + gaps["product_type"]

# Cap size driver for cleaner bubble charts
if "product_count" in gaps.columns:
    product_cap = gaps["product_count"].quantile(0.95)
    gaps["product_count_capped"] = gaps["product_count"].clip(upper=product_cap)
else:
    gaps["product_count_capped"] = 1

# Validated gap score: penalizes tiny/unsupported gaps a bit less aggressively
if {"gap_score", "product_count", "total_rating_number"}.issubset(gaps.columns):
    gaps["validated_gap_score"] = (
        gaps["gap_score"]
        * np.log1p(gaps["product_count"])
        * np.log1p(gaps["total_rating_number"])
    )
else:
    gaps["validated_gap_score"] = np.nan

# ---------------------------------------------------------
# Optional competition tier if not already present
# ---------------------------------------------------------
if "competition_tier" not in gaps.columns and "competition_score" in gaps.columns:
    q1 = gaps["competition_score"].quantile(0.33)
    q2 = gaps["competition_score"].quantile(0.66)

    def assign_comp_tier(x):
        if pd.isna(x):
            return np.nan
        if x <= q1:
            return "Low Competition"
        elif x <= q2:
            return "Medium Competition"
        return "High Competition"

    gaps["competition_tier"] = gaps["competition_score"].apply(assign_comp_tier)

# ---------------------------------------------------------
# Gap archetypes
# ---------------------------------------------------------
if {"gap_score", "demand_per_brand", "competition_score", "avg_price"}.issubset(gaps.columns):
    gap_q = gaps["gap_score"].quantile(0.67)
    demand_q = gaps["demand_per_brand"].quantile(0.67)
    comp_q_low = gaps["competition_score"].quantile(0.33)
    price_q_high = gaps["avg_price"].quantile(0.67)

    def classify_gap(row):
        if pd.isna(row["gap_score"]) or pd.isna(row["competition_score"]) or pd.isna(row["demand_per_brand"]):
            return "Unclassified"
        if row["gap_score"] >= gap_q and row["demand_per_brand"] >= demand_q and row["competition_score"] <= comp_q_low:
            return "High-Demand Whitespace"
        if row["gap_score"] >= gap_q and row["avg_price"] >= price_q_high:
            return "Premium Gap"
        if row["gap_score"] >= gap_q and row["competition_score"] <= comp_q_low:
            return "Low-Competition Niche"
        if row["gap_score"] >= gap_q:
            return "Emerging Gap"
        return "Low-Priority Gap"

    gaps["gap_archetype"] = gaps.apply(classify_gap, axis=1)
else:
    gaps["gap_archetype"] = "Unclassified"

# =========================================================
# KPI block
# =========================================================
total_subcategories = len(gaps)
total_animals = gaps["animal_type"].nunique() if "animal_type" in gaps.columns else 0
total_product_types = gaps["product_type"].nunique() if "product_type" in gaps.columns else 0
avg_gap = gaps["gap_score"].mean() if "gap_score" in gaps.columns else np.nan
avg_demand_per_brand = gaps["demand_per_brand"].mean() if "demand_per_brand" in gaps.columns else np.nan
avg_competition = gaps["competition_score"].mean() if "competition_score" in gaps.columns else np.nan

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Subcategories", f"{total_subcategories:,}")
c2.metric("Animal Types", f"{total_animals:,}")
c3.metric("Product Types", f"{total_product_types:,}")
c4.metric("Avg Gap Score", f"{avg_gap:.2f}" if pd.notna(avg_gap) else "NA")
c5.metric("Avg Demand / Brand", f"{avg_demand_per_brand:,.1f}" if pd.notna(avg_demand_per_brand) else "NA")
c6.metric("Avg Competition", f"{avg_competition:.2f}" if pd.notna(avg_competition) else "NA")

st.divider()

# =========================================================
# 1) Top gaps by gap score
# =========================================================
st.subheader("1. Top Market Gaps")
st.markdown(
    """
This ranking highlights the strongest whitespace signals based on the raw gap score.
"""
)

if {"subcategory", "gap_score"}.issubset(gaps.columns):
    top_gaps = (
        gaps.sort_values("gap_score", ascending=False)
        .head(15)
        .sort_values("gap_score", ascending=True)
    )

    fig_top_gaps = px.bar(
        top_gaps,
        x="gap_score",
        y="subcategory",
        orientation="h",
        color="competition_tier" if "competition_tier" in top_gaps.columns else None,
        title="Top Subcategories by Gap Score",
        hover_data={
            "animal_type": True if "animal_type" in top_gaps.columns else False,
            "product_type": True if "product_type" in top_gaps.columns else False,
            "gap_score": ":.2f",
            "opportunity_score": ":.2f" if "opportunity_score" in top_gaps.columns else False,
            "product_count": True if "product_count" in top_gaps.columns else False,
            "brand_count": True if "brand_count" in top_gaps.columns else False,
            "demand_per_brand": ":,.1f" if "demand_per_brand" in top_gaps.columns else False,
            "avg_price": ":.2f" if "avg_price" in top_gaps.columns else False,
        }
    )

    fig_top_gaps.update_layout(
        xaxis_title="Gap Score",
        yaxis_title="Subcategory",
        legend_title="Competition Tier",
        margin=dict(l=20, r=20, t=60, b=20)
    )

    st.plotly_chart(fig_top_gaps, use_container_width=True)
else:
    st.info("Required columns for the top gap ranking are missing.")

st.divider()

# =========================================================
# 2) Gap score vs opportunity score
# =========================================================
st.subheader("2. Gap Score vs Opportunity Score")
st.markdown(
    """
This chart separates spaces that look generally attractive from those that appear specifically underserved.
"""
)

required_gap_opp = {"gap_score", "opportunity_score", "subcategory"}
if required_gap_opp.issubset(gaps.columns):
    fig_gap_opp = px.scatter(
        gaps,
        x="opportunity_score",
        y="gap_score",
        size="product_count_capped",
        color="competition_tier" if "competition_tier" in gaps.columns else None,
        text="subcategory",
        title="Opportunity vs Whitespace Signal",
        hover_data={
            "animal_type": True if "animal_type" in gaps.columns else False,
            "product_type": True if "product_type" in gaps.columns else False,
            "gap_score": ":.2f",
            "opportunity_score": ":.2f",
            "competition_score": ":.2f" if "competition_score" in gaps.columns else False,
            "demand_per_brand": ":,.1f" if "demand_per_brand" in gaps.columns else False,
            "product_count": True if "product_count" in gaps.columns else False,
            "brand_count": True if "brand_count" in gaps.columns else False,
        }
    )

    fig_gap_opp.update_traces(
        textposition="top center",
        marker=dict(line=dict(width=1, color="white"))
    )
    fig_gap_opp.update_layout(
        xaxis_title="Opportunity Score",
        yaxis_title="Gap Score",
        legend_title="Competition Tier",
        margin=dict(l=20, r=20, t=60, b=20)
    )

    st.plotly_chart(fig_gap_opp, use_container_width=True)
else:
    st.info("Required columns for the gap vs opportunity chart are missing.")

st.divider()

# =========================================================
# 3) Gap validation map
# =========================================================
st.subheader("3. Gap Validation Map")
st.markdown(
    """
This chart helps validate whether a market gap is backed by stronger demand-per-brand
under relatively lower competitive pressure.
"""
)

required_validation = {"competition_score", "demand_per_brand", "gap_score", "subcategory"}
if required_validation.issubset(gaps.columns):
    plot_df = gaps.copy()

    x_mid = plot_df["competition_score"].median()
    y_mid = plot_df["demand_per_brand"].median()

    fig_validation = px.scatter(
        plot_df,
        x="competition_score",
        y="demand_per_brand",
        size="product_count_capped",
        color="gap_score",
        text="subcategory",
        title="Competition Pressure vs Demand per Brand",
        hover_data={
            "animal_type": True if "animal_type" in plot_df.columns else False,
            "product_type": True if "product_type" in plot_df.columns else False,
            "gap_score": ":.2f",
            "opportunity_score": ":.2f" if "opportunity_score" in plot_df.columns else False,
            "competition_score": ":.2f",
            "demand_per_brand": ":,.1f",
            "product_count": True if "product_count" in plot_df.columns else False,
            "brand_count": True if "brand_count" in plot_df.columns else False,
            "avg_price": ":.2f" if "avg_price" in plot_df.columns else False,
        },
        color_continuous_scale="Tealgrn"
    )

    fig_validation.update_traces(
        textposition="top center",
        marker=dict(line=dict(width=1, color="white"))
    )
    fig_validation.add_vline(x=x_mid, line_dash="dash", opacity=0.5)
    fig_validation.add_hline(y=y_mid, line_dash="dash", opacity=0.5)

    fig_validation.update_layout(
        xaxis_title="Competition Score",
        yaxis_title="Demand per Brand",
        coloraxis_colorbar_title="Gap Score",
        margin=dict(l=20, r=20, t=60, b=20)
    )

    st.plotly_chart(fig_validation, use_container_width=True)
else:
    st.info("Required columns for the gap validation map are missing.")

st.divider()

# =========================================================
# 4) Gap heatmap
# =========================================================
st.subheader("4. Gap Heatmap by Animal Type and Product Type")
st.markdown(
    """
This heatmap shows where whitespace signals are structurally concentrated across animal × product markets.
"""
)

if {"animal_type", "product_type", "gap_score"}.issubset(gaps.columns):
    gap_heat = (
        gaps.groupby(["animal_type", "product_type"], as_index=False)["gap_score"]
        .mean()
    )

    gap_matrix = gap_heat.pivot(
        index="animal_type",
        columns="product_type",
        values="gap_score"
    ).fillna(0)

    gap_matrix = gap_matrix.reindex([a for a in valid_animal_order if a in gap_matrix.index])

    top_cols = gap_matrix.mean(axis=0).sort_values(ascending=False).head(12).index.tolist()
    gap_matrix = gap_matrix[top_cols]

    fig_heat = px.imshow(
        gap_matrix,
        labels=dict(x="Product Type", y="Animal Type", color="Gap Score"),
        aspect="auto",
        color_continuous_scale="Purples",
        title="Whitespace Signals Across Animal × Product Markets"
    )

    fig_heat.update_layout(
        margin=dict(l=20, r=20, t=60, b=20)
    )

    st.plotly_chart(fig_heat, use_container_width=True)
else:
    st.info("Required columns for the gap heatmap are missing.")

st.divider()

# =========================================================
# 5) Raw vs validated gaps
# =========================================================
st.subheader("5. Raw vs Validated Gaps")
st.markdown(
    """
These rankings distinguish strong raw whitespace signals from gaps that also have more supporting market depth.
"""
)

left, right = st.columns(2)

with left:
    st.markdown("**Highest Raw Gaps**")

    raw_df = (
        gaps.sort_values("gap_score", ascending=False)
        .head(10)
        .sort_values("gap_score", ascending=True)
    )

    fig_raw = px.bar(
        raw_df,
        x="gap_score",
        y="subcategory",
        orientation="h",
        color="demand_per_brand" if "demand_per_brand" in raw_df.columns else None,
        title="Highest Raw Gap Score",
        hover_data={
            "product_count": True if "product_count" in raw_df.columns else False,
            "brand_count": True if "brand_count" in raw_df.columns else False,
            "demand_per_brand": ":,.1f" if "demand_per_brand" in raw_df.columns else False,
            "competition_score": ":.2f" if "competition_score" in raw_df.columns else False,
            "avg_price": ":.2f" if "avg_price" in raw_df.columns else False,
            "total_rating_number": ":,.0f" if "total_rating_number" in raw_df.columns else False,
        },
        color_continuous_scale="Tealgrn"
    )

    fig_raw.update_layout(
        xaxis_title="Gap Score",
        yaxis_title="Subcategory",
        coloraxis_colorbar_title="Demand / Brand",
        margin=dict(l=20, r=20, t=60, b=20)
    )

    st.plotly_chart(fig_raw, use_container_width=True)

with right:
    st.markdown("**Most Validated Gaps**")

    validated_df = gaps.copy()

    if "product_count" in validated_df.columns:
        validated_df = validated_df[validated_df["product_count"] >= 2].copy()
    if "brand_count" in validated_df.columns:
        validated_df = validated_df[validated_df["brand_count"] >= 2].copy()

    if "validated_gap_score" in validated_df.columns:
        validated_df = (
            validated_df.dropna(subset=["validated_gap_score"])
            .sort_values("validated_gap_score", ascending=False)
            .head(10)
            .sort_values("validated_gap_score", ascending=True)
        )

        fig_validated = px.bar(
            validated_df,
            x="validated_gap_score",
            y="subcategory",
            orientation="h",
            color="competition_score" if "competition_score" in validated_df.columns else None,
            title="Most Validated Gap Spaces",
            hover_data={
                "gap_score": ":.2f" if "gap_score" in validated_df.columns else False,
                "opportunity_score": ":.2f" if "opportunity_score" in validated_df.columns else False,
                "product_count": True if "product_count" in validated_df.columns else False,
                "brand_count": True if "brand_count" in validated_df.columns else False,
                "demand_per_brand": ":,.1f" if "demand_per_brand" in validated_df.columns else False,
                "competition_score": ":.2f" if "competition_score" in validated_df.columns else False,
            },
            color_continuous_scale="Blues"
        )

        fig_validated.update_layout(
            xaxis_title="Validated Gap Score",
            yaxis_title="Subcategory",
            coloraxis_colorbar_title="Competition",
            margin=dict(l=20, r=20, t=60, b=20)
        )

        st.plotly_chart(fig_validated, use_container_width=True)
    else:
        st.info("Validated gap score is not available.")

st.divider()

# =========================================================
# 6) Gap archetypes
# =========================================================
st.subheader("6. Gap Archetypes")
st.markdown(
    """
This view groups whitespace spaces into more interpretable strategic patterns.
"""
)

if {"gap_archetype", "subcategory", "gap_score"}.issubset(gaps.columns):
    archetype_counts = (
        gaps.groupby("gap_archetype")
        .size()
        .reset_index(name="subcategory_count")
        .sort_values("subcategory_count", ascending=False)
    )

    left, right = st.columns(2)

    with left:
        fig_arch_count = px.bar(
            archetype_counts,
            x="gap_archetype",
            y="subcategory_count",
            title="Number of Subcategories by Gap Archetype"
        )
        fig_arch_count.update_layout(
            xaxis_title="Gap Archetype",
            yaxis_title="Subcategory Count",
            margin=dict(l=20, r=20, t=60, b=20)
        )
        st.plotly_chart(fig_arch_count, use_container_width=True)

    with right:
        archetype_avg = (
            gaps.groupby("gap_archetype", as_index=False)
            .agg(
                avg_gap_score=("gap_score", "mean"),
                avg_demand_per_brand=("demand_per_brand", "mean") if "demand_per_brand" in gaps.columns else ("gap_score", "mean"),
                avg_competition_score=("competition_score", "mean") if "competition_score" in gaps.columns else ("gap_score", "mean"),
            )
        )

        fig_arch_profile = px.scatter(
            archetype_avg,
            x="avg_competition_score",
            y="avg_demand_per_brand",
            size="avg_gap_score",
            color="gap_archetype",
            text="gap_archetype",
            title="Strategic Profile of Gap Archetypes"
        )
        fig_arch_profile.update_traces(textposition="top center")
        fig_arch_profile.update_layout(
            xaxis_title="Average Competition Score",
            yaxis_title="Average Demand per Brand",
            showlegend=False,
            margin=dict(l=20, r=20, t=60, b=20)
        )
        st.plotly_chart(fig_arch_profile, use_container_width=True)
else:
    st.info("Gap archetype analysis is not available.")

st.divider()

# =========================================================
# 7) Gap drill-down
# =========================================================
st.subheader("7. Gap Drill-Down")
st.markdown(
    """
Select an animal type and product type to inspect the whitespace profile of a specific subcategory.
"""
)

animal_options = [a for a in valid_animal_order if a in gaps["animal_type"].dropna().unique().tolist()]

selected_animal = st.selectbox(
    "Select animal type",
    options=animal_options,
    key="gap_animal"
) if animal_options else None

if selected_animal is not None:
    product_options = (
        gaps.loc[gaps["animal_type"] == selected_animal, "product_type"]
        .dropna()
        .sort_values()
        .unique()
        .tolist()
    )
else:
    product_options = []

selected_product = st.selectbox(
    "Select product type",
    options=product_options,
    key="gap_product"
) if product_options else None

if selected_animal is not None and selected_product is not None:
    subcat_df = gaps[
        (gaps["animal_type"] == selected_animal) &
        (gaps["product_type"] == selected_product)
    ].copy()

    if subcat_df.empty:
        st.info("No data available for the selected subcategory.")
    else:
        row = subcat_df.iloc[0]

        market_avg_gap = gaps["gap_score"].mean() if "gap_score" in gaps.columns else np.nan
        market_avg_opp = gaps["opportunity_score"].mean() if "opportunity_score" in gaps.columns else np.nan
        market_avg_comp = gaps["competition_score"].mean() if "competition_score" in gaps.columns else np.nan
        market_avg_demand = gaps["demand_per_brand"].mean() if "demand_per_brand" in gaps.columns else np.nan
        market_avg_price = gaps["avg_price"].mean() if "avg_price" in gaps.columns else np.nan
        market_avg_rating = gaps["avg_rating"].mean() if "avg_rating" in gaps.columns else np.nan

        st.markdown(f"### {selected_animal} — {selected_product}")

        c1, c2, c3, c4, c5, c6 = st.columns(6)

        c1.metric(
            "Gap Score",
            f"{row['gap_score']:.2f}" if pd.notna(row.get("gap_score", np.nan)) else "NA",
            delta=(
                f"{row['gap_score'] - market_avg_gap:+.2f} vs market"
                if pd.notna(row.get("gap_score", np.nan)) and pd.notna(market_avg_gap)
                else None
            )
        )
        c2.metric(
            "Opportunity Score",
            f"{row['opportunity_score']:.2f}" if pd.notna(row.get("opportunity_score", np.nan)) else "NA",
            delta=(
                f"{row['opportunity_score'] - market_avg_opp:+.2f} vs market"
                if pd.notna(row.get("opportunity_score", np.nan)) and pd.notna(market_avg_opp)
                else None
            )
        )
        c3.metric(
            "Competition Score",
            f"{row['competition_score']:.2f}" if pd.notna(row.get("competition_score", np.nan)) else "NA",
            delta=(
                f"{row['competition_score'] - market_avg_comp:+.2f} vs market"
                if pd.notna(row.get("competition_score", np.nan)) and pd.notna(market_avg_comp)
                else None
            )
        )
        c4.metric(
            "Demand / Brand",
            f"{row['demand_per_brand']:,.1f}" if pd.notna(row.get("demand_per_brand", np.nan)) else "NA",
            delta=(
                f"{row['demand_per_brand'] - market_avg_demand:+,.1f} vs market"
                if pd.notna(row.get("demand_per_brand", np.nan)) and pd.notna(market_avg_demand)
                else None
            )
        )
        c5.metric(
            "Avg Price",
            f"${row['avg_price']:,.2f}" if pd.notna(row.get("avg_price", np.nan)) else "NA",
            delta=(
                f"{row['avg_price'] - market_avg_price:+.2f} vs market"
                if pd.notna(row.get("avg_price", np.nan)) and pd.notna(market_avg_price)
                else None
            )
        )
        c6.metric(
            "Avg Rating",
            f"{row['avg_rating']:.2f}" if pd.notna(row.get("avg_rating", np.nan)) else "NA",
            delta=(
                f"{row['avg_rating'] - market_avg_rating:+.2f} vs market"
                if pd.notna(row.get("avg_rating", np.nan)) and pd.notna(market_avg_rating)
                else None
            )
        )

        st.divider()

        st.markdown("**Position vs Full Market**")

        plot_df = gaps.copy()
        plot_df["is_selected"] = (
            (plot_df["animal_type"] == selected_animal) &
            (plot_df["product_type"] == selected_product)
        )

        fig_drill = px.scatter(
            plot_df,
            x="competition_score",
            y="demand_per_brand",
            size="product_count_capped",
            color="is_selected",
            hover_data=[
                "animal_type",
                "product_type",
                "product_count",
                "brand_count",
                "avg_price",
                "avg_rating",
                "gap_score",
                "opportunity_score"
            ],
            title=f"Selected Gap Space vs Full Market: {selected_animal} — {selected_product}",
            color_discrete_map={True: "#d62728", False: "#9aa0a6"}
        )

        fig_drill.update_layout(
            xaxis_title="Competition Score",
            yaxis_title="Demand per Brand",
            showlegend=False,
            margin=dict(l=20, r=20, t=60, b=20)
        )

        st.plotly_chart(fig_drill, use_container_width=True)

with st.expander("View underlying market gap table"):
    display_cols = [
        c for c in [
            "animal_type",
            "product_type",
            "product_count",
            "brand_count",
            "avg_price",
            "avg_rating",
            "total_rating_number",
            "demand_proxy",
            "demand_per_brand",
            "competition_score",
            "competition_tier",
            "gap_score",
            "gap_rank",
            "opportunity_score",
            "opportunity_rank",
            "validated_gap_score",
            "gap_archetype",
        ]
        if c in gaps.columns
    ]

    sort_col = "gap_score" if "gap_score" in gaps.columns else display_cols[0]
    st.dataframe(
        gaps[display_cols].sort_values(sort_col, ascending=False),
        use_container_width=True
    )
