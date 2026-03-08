import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

from utils.load_data import load_category_opportunity

st.title("Opportunity Map")
st.markdown(
    """
This section highlights category-level opportunity signals to identify promising
animal × product spaces for expansion, differentiation, or strategic entry.
"""
)

# =========================================================
# Load data
# =========================================================
opportunity = load_category_opportunity().copy()

# =========================================================
# Basic cleaning
# =========================================================
for col in opportunity.columns:
    if opportunity[col].dtype == "object":
        opportunity[col] = opportunity[col].astype(str).str.strip()

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

if "animal_type" in opportunity.columns:
    opportunity["animal_type"] = opportunity["animal_type"].map(animal_mapping)
    opportunity = opportunity[opportunity["animal_type"].isin(valid_animal_order)].copy()

if "product_type" in opportunity.columns:
    opportunity = opportunity[~opportunity["product_type"].isin(invalid_labels)].copy()

numeric_cols = [
    "product_count",
    "brand_count",
    "avg_price",
    "avg_rating",
    "total_rating_number",
    "opportunity_score",
    "opportunity_rank"
]

for col in numeric_cols:
    if col in opportunity.columns:
        opportunity[col] = pd.to_numeric(opportunity[col], errors="coerce")

required_cols = ["animal_type", "product_type", "opportunity_score"]
opportunity = opportunity.dropna(subset=[c for c in required_cols if c in opportunity.columns]).copy()

opportunity["subcategory"] = opportunity["animal_type"] + " — " + opportunity["product_type"]

# Cap size driver for cleaner scatter plots
if "product_count" in opportunity.columns:
    product_cap = opportunity["product_count"].quantile(0.95)
    opportunity["product_count_capped"] = opportunity["product_count"].clip(upper=product_cap)
else:
    opportunity["product_count_capped"] = 1

# A more conservative / scalable signal
if {"opportunity_score", "brand_count", "product_count"}.issubset(opportunity.columns):
    opportunity["scaled_opportunity_score"] = (
        opportunity["opportunity_score"] * np.log1p(opportunity["product_count"]) * np.log1p(opportunity["brand_count"])
    )
else:
    opportunity["scaled_opportunity_score"] = np.nan

# =========================================================
# KPI block
# =========================================================
total_subcategories = len(opportunity)
total_animals = opportunity["animal_type"].nunique() if "animal_type" in opportunity.columns else 0
total_product_types = opportunity["product_type"].nunique() if "product_type" in opportunity.columns else 0
avg_opportunity = opportunity["opportunity_score"].mean() if "opportunity_score" in opportunity.columns else np.nan
avg_price = opportunity["avg_price"].mean() if "avg_price" in opportunity.columns else np.nan
avg_brands = opportunity["brand_count"].mean() if "brand_count" in opportunity.columns else np.nan

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Subcategories", f"{total_subcategories:,}")
c2.metric("Animal Types", f"{total_animals:,}")
c3.metric("Product Types", f"{total_product_types:,}")
c4.metric("Avg Opportunity", f"{avg_opportunity:.2f}" if pd.notna(avg_opportunity) else "NA")
c5.metric("Avg Price", f"${avg_price:,.2f}" if pd.notna(avg_price) else "NA")
c6.metric("Avg Brands / Subcategory", f"{avg_brands:.1f}" if pd.notna(avg_brands) else "NA")

st.divider()

# =========================================================
# 1) Top opportunity spaces
# =========================================================
st.subheader("1. Top Opportunity Spaces")
st.markdown(
    """
This ranking highlights the subcategories with the strongest raw opportunity signal.
"""
)

if {"subcategory", "opportunity_score"}.issubset(opportunity.columns):
    top_opp = (
        opportunity.sort_values("opportunity_score", ascending=False)
        .head(15)
        .sort_values("opportunity_score", ascending=True)
    )

    fig_top_opp = px.bar(
        top_opp,
        x="opportunity_score",
        y="subcategory",
        orientation="h",
        color="brand_count" if "brand_count" in top_opp.columns else None,
        title="Top Subcategories by Opportunity Score",
        hover_data={
            "animal_type": True if "animal_type" in top_opp.columns else False,
            "product_type": True if "product_type" in top_opp.columns else False,
            "opportunity_score": ":.2f",
            "product_count": True if "product_count" in top_opp.columns else False,
            "brand_count": True if "brand_count" in top_opp.columns else False,
            "avg_price": ":.2f" if "avg_price" in top_opp.columns else False,
            "avg_rating": ":.2f" if "avg_rating" in top_opp.columns else False,
            "total_rating_number": ":,.0f" if "total_rating_number" in top_opp.columns else False
        },
        color_continuous_scale="Tealgrn"
    )

    fig_top_opp.update_layout(
        xaxis_title="Opportunity Score",
        yaxis_title="Subcategory",
        coloraxis_colorbar_title="Brand Count",
        margin=dict(l=20, r=20, t=60, b=20)
    )

    st.plotly_chart(fig_top_opp, use_container_width=True)
else:
    st.info("Required columns for the opportunity ranking are missing.")

st.divider()

# =========================================================
# 2) Opportunity positioning map
# =========================================================
st.subheader("2. Opportunity Positioning Map")
st.markdown(
    """
This chart contrasts competitive presence with market signal. It helps identify
spaces that combine lower brand density with stronger opportunity.
"""
)

required_scatter = {"brand_count", "total_rating_number", "opportunity_score", "subcategory"}
if required_scatter.issubset(opportunity.columns):
    plot_df = opportunity.copy()

    x_mid = plot_df["brand_count"].median()
    y_mid = plot_df["total_rating_number"].median()

    fig_position = px.scatter(
        plot_df,
        x="brand_count",
        y="total_rating_number",
        size="product_count_capped",
        color="opportunity_score",
        text="subcategory",
        title="Brand Density vs Market Signal",
        hover_data={
            "animal_type": True if "animal_type" in plot_df.columns else False,
            "product_type": True if "product_type" in plot_df.columns else False,
            "product_count": True if "product_count" in plot_df.columns else False,
            "brand_count": True,
            "avg_price": ":.2f" if "avg_price" in plot_df.columns else False,
            "avg_rating": ":.2f" if "avg_rating" in plot_df.columns else False,
            "total_rating_number": ":,.0f",
            "opportunity_score": ":.2f"
        },
        color_continuous_scale="Viridis"
    )

    fig_position.update_traces(
        textposition="top center",
        marker=dict(line=dict(width=1, color="white"))
    )
    fig_position.add_vline(x=x_mid, line_dash="dash", opacity=0.5)
    fig_position.add_hline(y=y_mid, line_dash="dash", opacity=0.5)

    fig_position.update_layout(
        xaxis_title="Brand Count",
        yaxis_title="Total Rating Volume",
        coloraxis_colorbar_title="Opportunity",
        margin=dict(l=20, r=20, t=60, b=20)
    )

    st.plotly_chart(fig_position, use_container_width=True)
else:
    st.info("Required columns for the opportunity positioning map are missing.")

st.divider()

# =========================================================
# 3) Opportunity heatmap
# =========================================================
st.subheader("3. Opportunity Heatmap by Animal Type and Product Type")
st.markdown(
    """
This heatmap shows where opportunity is structurally concentrated across animal × product spaces.
"""
)

if {"animal_type", "product_type", "opportunity_score"}.issubset(opportunity.columns):
    opp_heat = (
        opportunity.groupby(["animal_type", "product_type"], as_index=False)["opportunity_score"]
        .mean()
    )

    opp_matrix = opp_heat.pivot(
        index="animal_type",
        columns="product_type",
        values="opportunity_score"
    ).fillna(0)

    opp_matrix = opp_matrix.reindex([a for a in valid_animal_order if a in opp_matrix.index])

    top_cols = opp_matrix.mean(axis=0).sort_values(ascending=False).head(12).index.tolist()
    opp_matrix = opp_matrix[top_cols]

    fig_heat = px.imshow(
        opp_matrix,
        labels=dict(x="Product Type", y="Animal Type", color="Opportunity Score"),
        aspect="auto",
        color_continuous_scale="Tealgrn",
        title="Opportunity Across Animal × Product Markets"
    )

    fig_heat.update_layout(
        margin=dict(l=20, r=20, t=60, b=20)
    )

    st.plotly_chart(fig_heat, use_container_width=True)
else:
    st.info("Required columns for the opportunity heatmap are missing.")

st.divider()

# =========================================================
# 4) Price positioning of opportunities
# =========================================================
st.subheader("4. Price Positioning of Opportunity Spaces")
st.markdown(
    """
This chart shows whether the strongest opportunity signals cluster in lower-priced,
mid-market, or more premium spaces.
"""
)

required_price_map = {"avg_price", "opportunity_score", "subcategory"}
if required_price_map.issubset(opportunity.columns):
    fig_price_opp = px.scatter(
        opportunity,
        x="avg_price",
        y="opportunity_score",
        size="product_count_capped",
        color="avg_rating" if "avg_rating" in opportunity.columns else None,
        text="subcategory",
        title="Average Price vs Opportunity Score",
        hover_data={
            "animal_type": True if "animal_type" in opportunity.columns else False,
            "product_type": True if "product_type" in opportunity.columns else False,
            "product_count": True if "product_count" in opportunity.columns else False,
            "brand_count": True if "brand_count" in opportunity.columns else False,
            "avg_price": ":.2f",
            "avg_rating": ":.2f" if "avg_rating" in opportunity.columns else False,
            "total_rating_number": ":,.0f" if "total_rating_number" in opportunity.columns else False,
            "opportunity_score": ":.2f"
        },
        color_continuous_scale="Sunset"
    )

    fig_price_opp.update_traces(
        textposition="top center",
        marker=dict(line=dict(width=1, color="white"))
    )

    fig_price_opp.update_layout(
        xaxis_title="Average Price",
        yaxis_title="Opportunity Score",
        coloraxis_colorbar_title="Avg Rating",
        margin=dict(l=20, r=20, t=60, b=20)
    )

    st.plotly_chart(fig_price_opp, use_container_width=True)
else:
    st.info("Required columns for the price positioning chart are missing.")

st.divider()

# =========================================================
# 5) Raw vs scalable opportunities
# =========================================================
st.subheader("5. Raw vs Scalable Opportunities")
st.markdown(
    """
These two rankings separate the strongest raw signals from opportunities that also
have more structural depth and market footprint.
"""
)

left, right = st.columns(2)

with left:
    st.markdown("**Highest Raw Opportunity**")

    raw_df = (
        opportunity.sort_values("opportunity_score", ascending=False)
        .head(10)
        .sort_values("opportunity_score", ascending=True)
    )

    fig_raw = px.bar(
        raw_df,
        x="opportunity_score",
        y="subcategory",
        orientation="h",
        color="total_rating_number" if "total_rating_number" in raw_df.columns else None,
        title="Highest Raw Opportunity Score",
        hover_data={
            "product_count": True if "product_count" in raw_df.columns else False,
            "brand_count": True if "brand_count" in raw_df.columns else False,
            "avg_price": ":.2f" if "avg_price" in raw_df.columns else False,
            "avg_rating": ":.2f" if "avg_rating" in raw_df.columns else False,
            "total_rating_number": ":,.0f" if "total_rating_number" in raw_df.columns else False
        },
        color_continuous_scale="Viridis"
    )

    fig_raw.update_layout(
        xaxis_title="Opportunity Score",
        yaxis_title="Subcategory",
        coloraxis_colorbar_title="Rating Volume",
        margin=dict(l=20, r=20, t=60, b=20)
    )

    st.plotly_chart(fig_raw, use_container_width=True)

with right:
    st.markdown("**Most Scalable Opportunities**")

    scalable_df = opportunity.copy()

    # filter out extremely tiny spaces a bit
    if "product_count" in scalable_df.columns:
        scalable_df = scalable_df[scalable_df["product_count"] >= 2].copy()
    if "brand_count" in scalable_df.columns:
        scalable_df = scalable_df[scalable_df["brand_count"] >= 2].copy()

    if "scaled_opportunity_score" in scalable_df.columns:
        scalable_df = (
            scalable_df.dropna(subset=["scaled_opportunity_score"])
            .sort_values("scaled_opportunity_score", ascending=False)
            .head(10)
            .sort_values("scaled_opportunity_score", ascending=True)
        )

        fig_scalable = px.bar(
            scalable_df,
            x="scaled_opportunity_score",
            y="subcategory",
            orientation="h",
            color="avg_price" if "avg_price" in scalable_df.columns else None,
            title="Most Scalable Opportunity Spaces",
            hover_data={
                "opportunity_score": ":.2f" if "opportunity_score" in scalable_df.columns else False,
                "product_count": True if "product_count" in scalable_df.columns else False,
                "brand_count": True if "brand_count" in scalable_df.columns else False,
                "avg_price": ":.2f" if "avg_price" in scalable_df.columns else False,
                "avg_rating": ":.2f" if "avg_rating" in scalable_df.columns else False,
                "total_rating_number": ":,.0f" if "total_rating_number" in scalable_df.columns else False
            },
            color_continuous_scale="Blues"
        )

        fig_scalable.update_layout(
            xaxis_title="Scaled Opportunity Score",
            yaxis_title="Subcategory",
            coloraxis_colorbar_title="Avg Price",
            margin=dict(l=20, r=20, t=60, b=20)
        )

        st.plotly_chart(fig_scalable, use_container_width=True)
    else:
        st.info("Scaled opportunity score is not available.")

st.divider()

# =========================================================
# 6) Subcategory drill-down
# =========================================================
st.subheader("6. Opportunity Drill-Down")
st.markdown(
    """
Select an animal type and product type to inspect the opportunity profile of a specific subcategory.
"""
)

animal_options = [a for a in valid_animal_order if a in opportunity["animal_type"].dropna().unique().tolist()]

selected_animal = st.selectbox(
    "Select animal type",
    options=animal_options,
    key="opp_animal"
) if animal_options else None

if selected_animal is not None:
    product_options = (
        opportunity.loc[opportunity["animal_type"] == selected_animal, "product_type"]
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
    key="opp_product"
) if product_options else None

if selected_animal is not None and selected_product is not None:
    subcat_df = opportunity[
        (opportunity["animal_type"] == selected_animal) &
        (opportunity["product_type"] == selected_product)
    ].copy()

    if subcat_df.empty:
        st.info("No data available for the selected subcategory.")
    else:
        row = subcat_df.iloc[0]

        market_avg_opp = opportunity["opportunity_score"].mean() if "opportunity_score" in opportunity.columns else np.nan
        market_avg_price = opportunity["avg_price"].mean() if "avg_price" in opportunity.columns else np.nan
        market_avg_brands = opportunity["brand_count"].mean() if "brand_count" in opportunity.columns else np.nan
        market_avg_rating = opportunity["avg_rating"].mean() if "avg_rating" in opportunity.columns else np.nan

        st.markdown(f"### {selected_animal} — {selected_product}")

        c1, c2, c3, c4, c5, c6 = st.columns(6)

        c1.metric(
            "Opportunity Score",
            f"{row['opportunity_score']:.2f}" if pd.notna(row.get("opportunity_score", np.nan)) else "NA",
            delta=(
                f"{row['opportunity_score'] - market_avg_opp:+.2f} vs market"
                if pd.notna(row.get("opportunity_score", np.nan)) and pd.notna(market_avg_opp)
                else None
            )
        )
        c2.metric(
            "Products",
            f"{int(row['product_count']):,}" if pd.notna(row.get("product_count", np.nan)) else "NA"
        )
        c3.metric(
            "Brands",
            f"{int(row['brand_count']):,}" if pd.notna(row.get("brand_count", np.nan)) else "NA",
            delta=(
                f"{row['brand_count'] - market_avg_brands:+.1f} vs market"
                if pd.notna(row.get("brand_count", np.nan)) and pd.notna(market_avg_brands)
                else None
            )
        )
        c4.metric(
            "Avg Price",
            f"${row['avg_price']:,.2f}" if pd.notna(row.get("avg_price", np.nan)) else "NA",
            delta=(
                f"{row['avg_price'] - market_avg_price:+.2f} vs market"
                if pd.notna(row.get("avg_price", np.nan)) and pd.notna(market_avg_price)
                else None
            )
        )
        c5.metric(
            "Avg Rating",
            f"{row['avg_rating']:.2f}" if pd.notna(row.get("avg_rating", np.nan)) else "NA",
            delta=(
                f"{row['avg_rating'] - market_avg_rating:+.2f} vs market"
                if pd.notna(row.get("avg_rating", np.nan)) and pd.notna(market_avg_rating)
                else None
            )
        )
        c6.metric(
            "Rating Volume",
            f"{int(row['total_rating_number']):,}" if pd.notna(row.get("total_rating_number", np.nan)) else "NA"
        )

        st.divider()

        st.markdown("**Position vs Full Market**")

        plot_df = opportunity.copy()
        plot_df["is_selected"] = (
            (plot_df["animal_type"] == selected_animal) &
            (plot_df["product_type"] == selected_product)
        )

        fig_drill = px.scatter(
            plot_df,
            x="brand_count",
            y="total_rating_number",
            size="product_count_capped",
            color="is_selected",
            hover_data=["animal_type", "product_type", "product_count", "brand_count", "avg_price", "avg_rating", "opportunity_score"],
            title=f"Selected Opportunity Space vs Full Market: {selected_animal} — {selected_product}",
            color_discrete_map={True: "#d62728", False: "#9aa0a6"}
        )

        fig_drill.update_layout(
            xaxis_title="Brand Count",
            yaxis_title="Total Rating Volume",
            showlegend=False,
            margin=dict(l=20, r=20, t=60, b=20)
        )

        st.plotly_chart(fig_drill, use_container_width=True)

with st.expander("View underlying opportunity table"):
    display_cols = [
        c for c in [
            "animal_type",
            "product_type",
            "product_count",
            "brand_count",
            "avg_price",
            "avg_rating",
            "total_rating_number",
            "opportunity_score",
            "opportunity_rank",
            "scaled_opportunity_score"
        ]
        if c in opportunity.columns
    ]
    st.dataframe(
        opportunity[display_cols].sort_values("opportunity_score", ascending=False),
        use_container_width=True
    )
