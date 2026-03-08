import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

from utils.load_data import load_product_velocity

st.title("Product Velocity")
st.markdown(
    """
This page tracks momentum signals across products, using velocity-style metrics
to identify fast-rising items, validated fast movers, and emerging performers.
"""
)

# =========================================================
# Load data
# =========================================================
velocity = load_product_velocity().copy()

# =========================================================
# Basic cleaning
# =========================================================
for col in velocity.columns:
    if velocity[col].dtype == "object":
        velocity[col] = velocity[col].astype(str).str.strip()

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

if "category_l2" in velocity.columns:
    velocity["animal_type"] = velocity["category_l2"].map(animal_mapping)
    velocity = velocity[velocity["animal_type"].isin(valid_animal_order)].copy()
else:
    velocity["animal_type"] = np.nan

if "category_l3" in velocity.columns:
    velocity["product_type"] = velocity["category_l3"].astype(str).str.strip()
    velocity = velocity[~velocity["product_type"].isin(invalid_labels)].copy()
else:
    velocity["product_type"] = "Unknown"

for col in ["brand", "product_title"]:
    if col in velocity.columns:
        velocity[col] = velocity[col].astype(str).str.strip()

numeric_cols = [
    "price",
    "average_rating",
    "rating_number",
    "review_count",
    "lifespan_days",
    "lifespan_months",
    "reviews_per_month",
    "reviews_per_day",
    "rating_number_per_month",
    "velocity_score",
]

for col in numeric_cols:
    if col in velocity.columns:
        velocity[col] = pd.to_numeric(velocity[col], errors="coerce")

required_cols = ["price", "average_rating", "velocity_score"]
velocity = velocity.dropna(subset=[c for c in required_cols if c in velocity.columns]).copy()
velocity = velocity[velocity["price"] > 0].copy()

# Fallbacks
if "review_count" not in velocity.columns and "rating_number" in velocity.columns:
    velocity["review_count"] = velocity["rating_number"]

if "lifespan_days" not in velocity.columns:
    velocity["lifespan_days"] = np.nan

if "rating_number" not in velocity.columns:
    velocity["rating_number"] = 0

if "reviews_per_month" not in velocity.columns:
    velocity["reviews_per_month"] = np.nan

# Readable label
if "product_title" in velocity.columns:
    velocity["product_label"] = velocity["product_title"].fillna("Unknown Product")
else:
    velocity["product_label"] = "Unknown Product"

# Cap bubble sizes for cleaner plots
if "rating_number" in velocity.columns:
    rating_cap = velocity["rating_number"].quantile(0.95)
    velocity["rating_number_capped"] = velocity["rating_number"].clip(upper=rating_cap)
else:
    velocity["rating_number_capped"] = 1

if "reviews_per_month" in velocity.columns:
    rpm_cap = velocity["reviews_per_month"].quantile(0.95)
    velocity["reviews_per_month_capped"] = velocity["reviews_per_month"].clip(upper=rpm_cap)
else:
    velocity["reviews_per_month_capped"] = 1

# =========================================================
# Credibility segmentation
# =========================================================
if {"lifespan_days", "rating_number"}.issubset(velocity.columns):
    velocity["credibility_segment"] = np.select(
        [
            (velocity["lifespan_days"] >= 60) & (velocity["rating_number"] >= 30),
            (velocity["lifespan_days"] < 60) & (velocity["rating_number"] >= 10),
        ],
        [
            "Established Fast Movers",
            "Emerging Fast Movers",
        ],
        default="Low-Validation Products"
    )
else:
    velocity["credibility_segment"] = "Unclassified"

# =========================================================
# KPI block
# =========================================================
total_products = len(velocity)
avg_velocity = velocity["velocity_score"].mean() if "velocity_score" in velocity.columns else np.nan
avg_reviews_per_month = velocity["reviews_per_month"].mean() if "reviews_per_month" in velocity.columns else np.nan
avg_rating = velocity["average_rating"].mean() if "average_rating" in velocity.columns else np.nan
established_count = (velocity["credibility_segment"] == "Established Fast Movers").sum()
emerging_count = (velocity["credibility_segment"] == "Emerging Fast Movers").sum()

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Products", f"{total_products:,}")
c2.metric("Avg Velocity", f"{avg_velocity:.2f}" if pd.notna(avg_velocity) else "NA")
c3.metric("Avg Reviews / Month", f"{avg_reviews_per_month:,.1f}" if pd.notna(avg_reviews_per_month) else "NA")
c4.metric("Avg Rating", f"{avg_rating:.2f}" if pd.notna(avg_rating) else "NA")
c5.metric("Established Movers", f"{established_count:,}")
c6.metric("Emerging Movers", f"{emerging_count:,}")

st.divider()

# =========================================================
# Filters
# =========================================================
st.subheader("Filters")

f1, f2, f3 = st.columns(3)

animal_options = ["All"] + [a for a in valid_animal_order if a in velocity["animal_type"].dropna().unique().tolist()]
selected_animal = f1.selectbox("Animal Type", options=animal_options)

if selected_animal == "All":
    product_options = ["All"] + sorted(velocity["product_type"].dropna().unique().tolist())
else:
    product_options = ["All"] + sorted(
        velocity.loc[velocity["animal_type"] == selected_animal, "product_type"].dropna().unique().tolist()
    )
selected_product = f2.selectbox("Product Type", options=product_options)

credibility_options = ["All", "Established Fast Movers", "Emerging Fast Movers", "Low-Validation Products"]
selected_segment = f3.selectbox("Velocity Segment", options=credibility_options)

plot_velocity = velocity.copy()

if selected_animal != "All":
    plot_velocity = plot_velocity[plot_velocity["animal_type"] == selected_animal].copy()

if selected_product != "All":
    plot_velocity = plot_velocity[plot_velocity["product_type"] == selected_product].copy()

if selected_segment != "All":
    plot_velocity = plot_velocity[plot_velocity["credibility_segment"] == selected_segment].copy()

if plot_velocity.empty:
    st.warning("No products match the selected filters.")
    st.stop()

st.divider()

# =========================================================
# 1) Top fast-moving products
# =========================================================
st.subheader("1. Top Fast-Moving Products")
st.markdown(
    """
This ranking prioritizes faster-moving products while avoiding the most extreme low-history outliers.
"""
)

leaderboard_df = plot_velocity.copy()

if {"lifespan_days", "rating_number"}.issubset(leaderboard_df.columns):
    leaderboard_df = leaderboard_df[
        (leaderboard_df["lifespan_days"] >= 30) &
        (leaderboard_df["rating_number"] >= 10)
    ].copy()

if leaderboard_df.empty:
    st.info("No products meet the minimum validation threshold for the leaderboard.")
else:
    leaderboard_df = (
        leaderboard_df.sort_values("velocity_score", ascending=False)
        .head(15)
        .sort_values("velocity_score", ascending=True)
    )

    fig_top_velocity = px.bar(
        leaderboard_df,
        x="velocity_score",
        y="product_label",
        orientation="h",
        color="average_rating" if "average_rating" in leaderboard_df.columns else None,
        title="Top Products by Velocity Score",
        hover_data={
            "brand": True if "brand" in leaderboard_df.columns else False,
            "animal_type": True if "animal_type" in leaderboard_df.columns else False,
            "product_type": True if "product_type" in leaderboard_df.columns else False,
            "price": ":.2f" if "price" in leaderboard_df.columns else False,
            "average_rating": ":.2f" if "average_rating" in leaderboard_df.columns else False,
            "rating_number": ":,.0f" if "rating_number" in leaderboard_df.columns else False,
            "reviews_per_month": ":,.1f" if "reviews_per_month" in leaderboard_df.columns else False,
            "lifespan_days": ":,.0f" if "lifespan_days" in leaderboard_df.columns else False,
            "velocity_score": ":.2f"
        },
        color_continuous_scale="Tealgrn"
    )

    fig_top_velocity.update_layout(
        xaxis_title="Velocity Score",
        yaxis_title="Product",
        coloraxis_colorbar_title="Avg Rating",
        margin=dict(l=20, r=20, t=60, b=20)
    )

    st.plotly_chart(fig_top_velocity, use_container_width=True)

st.divider()

# =========================================================
# 2) Velocity vs validation map
# =========================================================
st.subheader("2. Velocity vs Market Validation")
st.markdown(
    """
This chart separates products that are moving fast with stronger market validation
from newer or thinner signals.
"""
)

required_scatter = {"velocity_score", "rating_number", "product_label"}
if required_scatter.issubset(plot_velocity.columns):
    scatter_df = plot_velocity.copy()

    # label only top few to avoid clutter
    scatter_df["label_to_show"] = ""
    top_label_idx = scatter_df.sort_values("velocity_score", ascending=False).head(12).index
    scatter_df.loc[top_label_idx, "label_to_show"] = scatter_df.loc[top_label_idx, "product_label"]

    fig_validation = px.scatter(
        scatter_df,
        x="velocity_score",
        y="rating_number",
        size="reviews_per_month_capped" if "reviews_per_month_capped" in scatter_df.columns else None,
        color="average_rating" if "average_rating" in scatter_df.columns else None,
        symbol="credibility_segment" if "credibility_segment" in scatter_df.columns else None,
        text="label_to_show",
        title="Velocity Score vs Rating Count",
        hover_data={
            "brand": True if "brand" in scatter_df.columns else False,
            "animal_type": True if "animal_type" in scatter_df.columns else False,
            "product_type": True if "product_type" in scatter_df.columns else False,
            "price": ":.2f" if "price" in scatter_df.columns else False,
            "average_rating": ":.2f" if "average_rating" in scatter_df.columns else False,
            "rating_number": ":,.0f",
            "review_count": ":,.0f" if "review_count" in scatter_df.columns else False,
            "reviews_per_month": ":,.1f" if "reviews_per_month" in scatter_df.columns else False,
            "lifespan_days": ":,.0f" if "lifespan_days" in scatter_df.columns else False,
            "velocity_score": ":.2f"
        },
        color_continuous_scale="Viridis"
    )

    fig_validation.update_traces(
        textposition="top center",
        marker=dict(line=dict(width=1, color="white"))
    )

    fig_validation.update_layout(
        xaxis_title="Velocity Score",
        yaxis_title="Rating Count",
        coloraxis_colorbar_title="Avg Rating",
        margin=dict(l=20, r=20, t=60, b=20)
    )

    st.plotly_chart(fig_validation, use_container_width=True)
else:
    st.info("Required columns for the validation map are missing.")

st.divider()

# =========================================================
# 3) Velocity heatmap
# =========================================================
st.subheader("3. Velocity Heatmap by Animal Type and Product Type")
st.markdown(
    """
This heatmap shows where product momentum is structurally concentrated across animal × product spaces.
"""
)

if {"animal_type", "product_type", "velocity_score"}.issubset(plot_velocity.columns):
    heat_df = (
        plot_velocity.groupby(["animal_type", "product_type"], as_index=False)["velocity_score"]
        .mean()
    )

    heat_matrix = heat_df.pivot(
        index="animal_type",
        columns="product_type",
        values="velocity_score"
    ).fillna(0)

    heat_matrix = heat_matrix.reindex([a for a in valid_animal_order if a in heat_matrix.index])

    top_cols = heat_matrix.mean(axis=0).sort_values(ascending=False).head(12).index.tolist()
    heat_matrix = heat_matrix[top_cols]

    fig_heat = px.imshow(
        heat_matrix,
        labels=dict(x="Product Type", y="Animal Type", color="Velocity Score"),
        aspect="auto",
        color_continuous_scale="Blues",
        title="Velocity Across Animal × Product Markets"
    )

    fig_heat.update_layout(
        margin=dict(l=20, r=20, t=60, b=20)
    )

    st.plotly_chart(fig_heat, use_container_width=True)
else:
    st.info("Required columns for the velocity heatmap are missing.")

st.divider()

# =========================================================
# 4) Velocity distribution by animal type
# =========================================================
st.subheader("4. Velocity Distribution by Animal Type")
st.markdown(
    """
This box plot shows how product momentum is distributed within each animal market.
"""
)

if {"animal_type", "velocity_score"}.issubset(plot_velocity.columns):
    fig_box = px.box(
        plot_velocity,
        x="animal_type",
        y="velocity_score",
        color="animal_type",
        category_orders={"animal_type": valid_animal_order},
        points=False,
        title="Velocity Score per Product by Animal Type"
    )

    fig_box.update_layout(
        xaxis_title="Animal Type",
        yaxis_title="Velocity Score",
        showlegend=False,
        margin=dict(l=20, r=20, t=60, b=20)
    )

    st.plotly_chart(fig_box, use_container_width=True)
else:
    st.info("Required columns for the velocity box plot are missing.")

st.divider()

# =========================================================
# 5) Price vs velocity
# =========================================================
st.subheader("5. Price vs Velocity")
st.markdown(
    """
This chart shows whether faster-moving products cluster more strongly in lower-priced,
mid-market, or premium spaces.
"""
)

required_price_velocity = {"price", "velocity_score", "product_label"}
if required_price_velocity.issubset(plot_velocity.columns):
    price_df = plot_velocity.copy()
    price_df["label_to_show"] = ""
    top_label_idx = price_df.sort_values("velocity_score", ascending=False).head(10).index
    price_df.loc[top_label_idx, "label_to_show"] = price_df.loc[top_label_idx, "product_label"]

    fig_price_velocity = px.scatter(
        price_df,
        x="price",
        y="velocity_score",
        size="rating_number_capped" if "rating_number_capped" in price_df.columns else None,
        color="average_rating" if "average_rating" in price_df.columns else None,
        text="label_to_show",
        title="Average Price vs Velocity Score",
        hover_data={
            "brand": True if "brand" in price_df.columns else False,
            "animal_type": True if "animal_type" in price_df.columns else False,
            "product_type": True if "product_type" in price_df.columns else False,
            "price": ":.2f",
            "average_rating": ":.2f" if "average_rating" in price_df.columns else False,
            "rating_number": ":,.0f" if "rating_number" in price_df.columns else False,
            "reviews_per_month": ":,.1f" if "reviews_per_month" in price_df.columns else False,
            "lifespan_days": ":,.0f" if "lifespan_days" in price_df.columns else False,
            "velocity_score": ":.2f"
        },
        color_continuous_scale="Sunset"
    )

    fig_price_velocity.update_traces(
        textposition="top center",
        marker=dict(line=dict(width=1, color="white"))
    )

    fig_price_velocity.update_layout(
        xaxis_title="Price",
        yaxis_title="Velocity Score",
        coloraxis_colorbar_title="Avg Rating",
        margin=dict(l=20, r=20, t=60, b=20)
    )

    st.plotly_chart(fig_price_velocity, use_container_width=True)
else:
    st.info("Required columns for the price vs velocity chart are missing.")

st.divider()

# =========================================================
# 6) Established vs emerging fast movers
# =========================================================
st.subheader("6. Established vs Emerging Fast Movers")
st.markdown(
    """
These rankings distinguish faster products with stronger market validation from newer rising stars.
"""
)

left, right = st.columns(2)

with left:
    st.markdown("**Established Fast Movers**")

    established_df = plot_velocity[
        plot_velocity["credibility_segment"] == "Established Fast Movers"
    ].copy()

    if not established_df.empty:
        established_df = (
            established_df.sort_values("velocity_score", ascending=False)
            .head(10)
            .sort_values("velocity_score", ascending=True)
        )

        fig_established = px.bar(
            established_df,
            x="velocity_score",
            y="product_label",
            orientation="h",
            color="average_rating" if "average_rating" in established_df.columns else None,
            title="Established Fast Movers",
            hover_data={
                "brand": True if "brand" in established_df.columns else False,
                "animal_type": True if "animal_type" in established_df.columns else False,
                "product_type": True if "product_type" in established_df.columns else False,
                "rating_number": ":,.0f" if "rating_number" in established_df.columns else False,
                "reviews_per_month": ":,.1f" if "reviews_per_month" in established_df.columns else False,
                "lifespan_days": ":,.0f" if "lifespan_days" in established_df.columns else False,
                "velocity_score": ":.2f"
            },
            color_continuous_scale="Blues"
        )

        fig_established.update_layout(
            xaxis_title="Velocity Score",
            yaxis_title="Product",
            coloraxis_colorbar_title="Avg Rating",
            margin=dict(l=20, r=20, t=60, b=20)
        )

        st.plotly_chart(fig_established, use_container_width=True)
    else:
        st.info("No established fast movers match the current filters.")

with right:
    st.markdown("**Emerging Fast Movers**")

    emerging_df = plot_velocity[
        plot_velocity["credibility_segment"] == "Emerging Fast Movers"
    ].copy()

    if not emerging_df.empty:
        emerging_df = (
            emerging_df.sort_values("velocity_score", ascending=False)
            .head(10)
            .sort_values("velocity_score", ascending=True)
        )

        fig_emerging = px.bar(
            emerging_df,
            x="velocity_score",
            y="product_label",
            orientation="h",
            color="average_rating" if "average_rating" in emerging_df.columns else None,
            title="Emerging Fast Movers",
            hover_data={
                "brand": True if "brand" in emerging_df.columns else False,
                "animal_type": True if "animal_type" in emerging_df.columns else False,
                "product_type": True if "product_type" in emerging_df.columns else False,
                "rating_number": ":,.0f" if "rating_number" in emerging_df.columns else False,
                "reviews_per_month": ":,.1f" if "reviews_per_month" in emerging_df.columns else False,
                "lifespan_days": ":,.0f" if "lifespan_days" in emerging_df.columns else False,
                "velocity_score": ":.2f"
            },
            color_continuous_scale="Tealgrn"
        )

        fig_emerging.update_layout(
            xaxis_title="Velocity Score",
            yaxis_title="Product",
            coloraxis_colorbar_title="Avg Rating",
            margin=dict(l=20, r=20, t=60, b=20)
        )

        st.plotly_chart(fig_emerging, use_container_width=True)
    else:
        st.info("No emerging fast movers match the current filters.")

st.divider()

# =========================================================
# 7) Product drill-down
# =========================================================
st.subheader("7. Product Drill-Down")
st.markdown(
    """
Inspect a specific product and compare its momentum profile against the current filtered market.
"""
)

drill_candidates = (
    plot_velocity.sort_values("velocity_score", ascending=False)["product_label"]
    .dropna()
    .unique()
    .tolist()
)

selected_product_label = st.selectbox(
    "Select product",
    options=drill_candidates,
    key="velocity_product"
) if drill_candidates else None

if selected_product_label is not None:
    selected_df = plot_velocity[plot_velocity["product_label"] == selected_product_label].copy()

    if selected_df.empty:
        st.info("No data available for the selected product.")
    else:
        row = selected_df.iloc[0]

        market_avg_velocity = plot_velocity["velocity_score"].mean() if "velocity_score" in plot_velocity.columns else np.nan
        market_avg_price = plot_velocity["price"].mean() if "price" in plot_velocity.columns else np.nan
        market_avg_rating = plot_velocity["average_rating"].mean() if "average_rating" in plot_velocity.columns else np.nan
        market_avg_rpm = plot_velocity["reviews_per_month"].mean() if "reviews_per_month" in plot_velocity.columns else np.nan
        market_avg_rating_count = plot_velocity["rating_number"].mean() if "rating_number" in plot_velocity.columns else np.nan

        st.markdown(f"### {selected_product_label}")

        c1, c2, c3, c4, c5, c6 = st.columns(6)

        c1.metric(
            "Velocity Score",
            f"{row['velocity_score']:.2f}" if pd.notna(row.get("velocity_score", np.nan)) else "NA",
            delta=(
                f"{row['velocity_score'] - market_avg_velocity:+.2f} vs filtered market"
                if pd.notna(row.get("velocity_score", np.nan)) and pd.notna(market_avg_velocity)
                else None
            )
        )
        c2.metric(
            "Price",
            f"${row['price']:,.2f}" if pd.notna(row.get("price", np.nan)) else "NA",
            delta=(
                f"{row['price'] - market_avg_price:+.2f} vs filtered market"
                if pd.notna(row.get("price", np.nan)) and pd.notna(market_avg_price)
                else None
            )
        )
        c3.metric(
            "Avg Rating",
            f"{row['average_rating']:.2f}" if pd.notna(row.get("average_rating", np.nan)) else "NA",
            delta=(
                f"{row['average_rating'] - market_avg_rating:+.2f} vs filtered market"
                if pd.notna(row.get("average_rating", np.nan)) and pd.notna(market_avg_rating)
                else None
            )
        )
        c4.metric(
            "Rating Count",
            f"{int(row['rating_number']):,}" if pd.notna(row.get("rating_number", np.nan)) else "NA",
            delta=(
                f"{row['rating_number'] - market_avg_rating_count:+,.0f} vs filtered market"
                if pd.notna(row.get("rating_number", np.nan)) and pd.notna(market_avg_rating_count)
                else None
            )
        )
        c5.metric(
            "Reviews / Month",
            f"{row['reviews_per_month']:,.1f}" if pd.notna(row.get("reviews_per_month", np.nan)) else "NA",
            delta=(
                f"{row['reviews_per_month'] - market_avg_rpm:+,.1f} vs filtered market"
                if pd.notna(row.get("reviews_per_month", np.nan)) and pd.notna(market_avg_rpm)
                else None
            )
        )
        c6.metric(
            "Lifespan (Days)",
            f"{int(row['lifespan_days']):,}" if pd.notna(row.get("lifespan_days", np.nan)) else "NA"
        )

        st.divider()

        st.markdown("**Position vs Filtered Market**")

        drill_plot = plot_velocity.copy()
        drill_plot["is_selected"] = drill_plot["product_label"] == selected_product_label

        fig_drill = px.scatter(
            drill_plot,
            x="velocity_score",
            y="rating_number",
            size="reviews_per_month_capped" if "reviews_per_month_capped" in drill_plot.columns else None,
            color="is_selected",
            hover_data=[
                c for c in [
                    "product_label",
                    "brand",
                    "animal_type",
                    "product_type",
                    "price",
                    "average_rating",
                    "rating_number",
                    "reviews_per_month",
                    "lifespan_days",
                    "credibility_segment"
                ] if c in drill_plot.columns
            ],
            title=f"Selected Product vs Filtered Market: {selected_product_label}",
            color_discrete_map={True: "#d62728", False: "#9aa0a6"}
        )

        fig_drill.update_layout(
            xaxis_title="Velocity Score",
            yaxis_title="Rating Count",
            showlegend=False,
            margin=dict(l=20, r=20, t=60, b=20)
        )

        st.plotly_chart(fig_drill, use_container_width=True)

with st.expander("View underlying product velocity table"):
    display_cols = [
        c for c in [
            "product_label",
            "brand",
            "animal_type",
            "product_type",
            "price",
            "average_rating",
            "rating_number",
            "review_count",
            "lifespan_days",
            "lifespan_months",
            "reviews_per_month",
            "reviews_per_day",
            "rating_number_per_month",
            "velocity_score",
            "credibility_segment",
        ]
        if c in plot_velocity.columns
    ]

    st.dataframe(
        plot_velocity[display_cols].sort_values("velocity_score", ascending=False),
        use_container_width=True
    )
