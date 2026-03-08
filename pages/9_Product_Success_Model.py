import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

from utils.load_data import (
    load_product_success_score,
    load_product_success_feature_importance
)

st.title("Product Success Model")
st.markdown(
    """
This page summarizes the product success model, highlighting top-ranked products,
model-driven success tiers, and the features that contribute most to predicted success.
"""
)

# =========================================================
# Load data
# =========================================================
success = load_product_success_score().copy()
feature_importance = load_product_success_feature_importance().copy()

# =========================================================
# Helpers
# =========================================================
def shorten_title(title, max_words=12):
    if not isinstance(title, str):
        return str(title)
    words = title.split()
    if len(words) <= max_words:
        return title
    return " ".join(words[:max_words]) + "..."

# =========================================================
# Basic cleaning
# =========================================================
for df in [success, feature_importance]:
    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = df[col].astype(str).str.strip()

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

if "brand" in success.columns:
    success = success[~success["brand"].isin(invalid_labels)].copy()

if "category_l2" in success.columns:
    success["animal_type"] = success["category_l2"].map(animal_mapping)
    success = success[success["animal_type"].isin(valid_animal_order)].copy()
else:
    success["animal_type"] = "Unknown"

if "category_l3" in success.columns:
    success["product_type"] = success["category_l3"].astype(str).str.strip()
    success = success[~success["product_type"].isin(invalid_labels)].copy()
else:
    success["product_type"] = "Unknown"

numeric_cols = [
    "price",
    "average_rating",
    "rating_number",
    "review_count",
    "reviews_per_month",
    "rating_number_per_month",
    "value_score",
    "success_probability",
    "success_score",
    "success_rank"
]

for col in numeric_cols:
    if col in success.columns:
        success[col] = pd.to_numeric(success[col], errors="coerce")

for col in ["importance_mean", "importance_std"]:
    if col in feature_importance.columns:
        feature_importance[col] = pd.to_numeric(feature_importance[col], errors="coerce")

if "product_title" in success.columns:
    success["short_title"] = success["product_title"].apply(lambda x: shorten_title(x, max_words=12))
else:
    success["product_title"] = "Unknown Product"
    success["short_title"] = "Unknown Product"

success = success.dropna(subset=[c for c in ["success_score", "success_probability"] if c in success.columns]).copy()

# Cap point sizes
if "rating_number" in success.columns:
    rating_cap = success["rating_number"].quantile(0.95)
    success["rating_number_capped"] = success["rating_number"].clip(upper=rating_cap)
else:
    success["rating_number_capped"] = 1

if "price" in success.columns:
    price_cap = success["price"].quantile(0.95)
    success["price_capped"] = success["price"].clip(upper=price_cap)
else:
    success["price_capped"] = 1

# =========================================================
# KPI block
# =========================================================
total_products = len(success)
avg_success_score = success["success_score"].mean() if "success_score" in success.columns else np.nan
avg_success_probability = success["success_probability"].mean() if "success_probability" in success.columns else np.nan
avg_value_score = success["value_score"].mean() if "value_score" in success.columns else np.nan
very_high_count = (success["success_tier"] == "Very High").sum() if "success_tier" in success.columns else 0
high_count = (success["success_tier"] == "High").sum() if "success_tier" in success.columns else 0

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Products Scored", f"{total_products:,}")
c2.metric("Avg Success Score", f"{avg_success_score:.2f}" if pd.notna(avg_success_score) else "NA")
c3.metric("Avg Success Probability", f"{avg_success_probability:.2%}" if pd.notna(avg_success_probability) else "NA")
c4.metric("Avg Value Score", f"{avg_value_score:.2f}" if pd.notna(avg_value_score) else "NA")
c5.metric("Very High Tier", f"{very_high_count:,}")
c6.metric("High Tier", f"{high_count:,}")

st.divider()

# =========================================================
# Filters
# =========================================================
st.subheader("Filters")

f1, f2, f3 = st.columns(3)

animal_options = ["All"] + [a for a in valid_animal_order if a in success["animal_type"].dropna().unique().tolist()]
selected_animal = f1.selectbox("Animal Type", options=animal_options)

if selected_animal == "All":
    product_options = ["All"] + sorted(success["product_type"].dropna().unique().tolist())
else:
    product_options = ["All"] + sorted(
        success.loc[success["animal_type"] == selected_animal, "product_type"].dropna().unique().tolist()
    )
selected_product = f2.selectbox("Product Type", options=product_options)

tier_options = ["All"] + sorted(success["success_tier"].dropna().unique().tolist()) if "success_tier" in success.columns else ["All"]
selected_tier = f3.selectbox("Success Tier", options=tier_options)

plot_success = success.copy()

if selected_animal != "All":
    plot_success = plot_success[plot_success["animal_type"] == selected_animal].copy()

if selected_product != "All":
    plot_success = plot_success[plot_success["product_type"] == selected_product].copy()

if selected_tier != "All" and "success_tier" in plot_success.columns:
    plot_success = plot_success[plot_success["success_tier"] == selected_tier].copy()

if plot_success.empty:
    st.warning("No products match the selected filters.")
    st.stop()

st.divider()

# =========================================================
# 1) Top products by success score
# =========================================================
st.subheader("1. Top Products by Success Score")
st.markdown(
    """
This ranking shows the products with the strongest predicted success according to the model.
"""
)

top_success = (
    plot_success.sort_values("success_score", ascending=False)
    .head(20)
    .sort_values("success_score", ascending=True)
)

fig_top_success = px.bar(
    top_success,
    x="success_score",
    y="short_title",
    orientation="h",
    color="average_rating" if "average_rating" in top_success.columns else None,
    title="Top 20 Products by Success Score",
    hover_data={
        "product_title": True,
        "brand": True if "brand" in top_success.columns else False,
        "animal_type": True if "animal_type" in top_success.columns else False,
        "product_type": True if "product_type" in top_success.columns else False,
        "price": ":.2f" if "price" in top_success.columns else False,
        "average_rating": ":.2f" if "average_rating" in top_success.columns else False,
        "rating_number": ":,.0f" if "rating_number" in top_success.columns else False,
        "value_score": ":.2f" if "value_score" in top_success.columns else False,
        "success_probability": ":.2%" if "success_probability" in top_success.columns else False,
        "success_score": ":.2f"
    },
    color_continuous_scale="Tealgrn"
)

fig_top_success.update_layout(
    xaxis_title="Success Score",
    yaxis_title="Product",
    coloraxis_colorbar_title="Avg Rating",
    margin=dict(l=20, r=20, t=60, b=20)
)

st.plotly_chart(fig_top_success, use_container_width=True)

st.divider()

# =========================================================
# 2) Success score distribution + tier distribution
# =========================================================
left, right = st.columns(2)

with left:
    st.subheader("2. Success Score Distribution")

    fig_dist = px.histogram(
        plot_success,
        x="success_score",
        nbins=30,
        title="Distribution of Success Score"
    )

    fig_dist.update_layout(
        xaxis_title="Success Score",
        yaxis_title="Product Count",
        margin=dict(l=20, r=20, t=60, b=20)
    )

    st.plotly_chart(fig_dist, use_container_width=True)

with right:
    st.subheader("3. Success Tier Distribution")

    if "success_tier" in plot_success.columns:
        tier_counts = (
            plot_success.groupby("success_tier")
            .size()
            .reset_index(name="product_count")
            .sort_values("product_count", ascending=False)
        )

        fig_tier = px.bar(
            tier_counts,
            x="success_tier",
            y="product_count",
            color="success_tier",
            title="Products by Success Tier"
        )

        fig_tier.update_layout(
            xaxis_title="Success Tier",
            yaxis_title="Product Count",
            showlegend=False,
            margin=dict(l=20, r=20, t=60, b=20)
        )

        st.plotly_chart(fig_tier, use_container_width=True)
    else:
        st.info("Success tier column is not available.")

st.divider()

# =========================================================
# 4) Feature importance
# =========================================================
st.subheader("4. Model Feature Importance")
st.markdown(
    """
These are the features that contribute most to the success model.
"""
)

if {"feature", "importance_mean"}.issubset(feature_importance.columns):
    fi_plot = (
        feature_importance.dropna(subset=["importance_mean"])
        .sort_values("importance_mean", ascending=False)
        .head(15)
        .sort_values("importance_mean", ascending=True)
    )

    fig_fi = px.bar(
        fi_plot,
        x="importance_mean",
        y="feature",
        orientation="h",
        error_x="importance_std" if "importance_std" in fi_plot.columns else None,
        title="Top Features Driving Product Success"
    )

    fig_fi.update_layout(
        xaxis_title="Mean Importance",
        yaxis_title="Feature",
        margin=dict(l=20, r=20, t=60, b=20)
    )

    st.plotly_chart(fig_fi, use_container_width=True)
else:
    st.info("Feature importance data is not available.")

st.divider()

# =========================================================
# 5) Success positioning map
# =========================================================
st.subheader("5. Success Positioning Map")
st.markdown(
    """
This chart compares model-predicted success against market validation.
"""
)

required_scatter = {"success_score", "rating_number", "product_title"}
if required_scatter.issubset(plot_success.columns):
    scatter_df = plot_success.copy()

    # Force numeric columns safely
    for col in ["success_score", "rating_number", "price_capped", "average_rating"]:
        if col in scatter_df.columns:
            scatter_df[col] = pd.to_numeric(scatter_df[col], errors="coerce")

    # Keep only valid rows for plotting
    scatter_df = scatter_df.dropna(subset=["success_score", "rating_number"])

    # Optional size column
    size_col = None
    if "price_capped" in scatter_df.columns:
        scatter_df = scatter_df.dropna(subset=["price_capped"])
        scatter_df = scatter_df[scatter_df["price_capped"] > 0].copy()
        if not scatter_df.empty:
            size_col = "price_capped"

    # Optional color column
    color_col = None
    if "average_rating" in scatter_df.columns:
        scatter_df = scatter_df.dropna(subset=["average_rating"])
        if not scatter_df.empty:
            color_col = "average_rating"

    # Optional symbol column
    symbol_col = "success_tier" if "success_tier" in scatter_df.columns else None

    if not scatter_df.empty:
        scatter_df["label_to_show"] = ""
        top_label_idx = scatter_df.sort_values("success_score", ascending=False).head(12).index
        scatter_df.loc[top_label_idx, "label_to_show"] = scatter_df.loc[top_label_idx, "short_title"]

        hover_cols = [
            c for c in [
                "product_title",
                "brand",
                "animal_type",
                "product_type",
                "price",
                "average_rating",
                "rating_number",
                "value_score",
                "success_probability",
                "success_score",
                "success_tier"
            ]
            if c in scatter_df.columns
        ]

        fig_position = px.scatter(
            scatter_df,
            x="success_score",
            y="rating_number",
            size=size_col,
            color=color_col,
            symbol=symbol_col,
            text="label_to_show",
            hover_name="short_title" if "short_title" in scatter_df.columns else None,
            hover_data=hover_cols,
            title="Predicted Success vs Rating Count",
            color_continuous_scale="Viridis"
        )

        fig_position.update_traces(
            textposition="top center",
            marker=dict(line=dict(width=1, color="white"))
        )

        fig_position.update_layout(
            xaxis_title="Success Score",
            yaxis_title="Rating Count",
            coloraxis_colorbar_title="Avg Rating" if color_col else "",
            margin=dict(l=20, r=20, t=60, b=20)
        )

        st.plotly_chart(fig_position, use_container_width=True)
    else:
        st.info("Not enough valid data to display the success positioning map.")
else:
    st.info("Required columns for the success positioning map are missing.")

# =========================================================
# 6) Validated winners vs hidden gems
# =========================================================
st.subheader("6. Validated Winners vs Hidden Gems")
st.markdown(
    """
These rankings separate products that already combine high predicted success with strong market validation
from products that score well but still have a smaller proof base.
"""
)

left, right = st.columns(2)

with left:
    st.markdown("**Validated Winners**")

    winners_df = plot_success.copy()
    if "rating_number" in winners_df.columns:
        winners_df = winners_df[winners_df["rating_number"] >= winners_df["rating_number"].median()].copy()

    winners_df = (
        winners_df.sort_values(["success_score", "rating_number"], ascending=[False, False])
        .head(10)
        .sort_values("success_score", ascending=True)
    )

    fig_winners = px.bar(
        winners_df,
        x="success_score",
        y="short_title",
        orientation="h",
        color="rating_number" if "rating_number" in winners_df.columns else None,
        title="Validated Winners",
        hover_data={
            "product_title": True,
            "brand": True if "brand" in winners_df.columns else False,
            "price": ":.2f" if "price" in winners_df.columns else False,
            "average_rating": ":.2f" if "average_rating" in winners_df.columns else False,
            "rating_number": ":,.0f" if "rating_number" in winners_df.columns else False,
            "success_score": ":.2f"
        },
        color_continuous_scale="Blues"
    )

    fig_winners.update_layout(
        xaxis_title="Success Score",
        yaxis_title="Product",
        coloraxis_colorbar_title="Rating Count",
        margin=dict(l=20, r=20, t=60, b=20)
    )

    st.plotly_chart(fig_winners, use_container_width=True)

with right:
    st.markdown("**Hidden Gems**")

    gems_df = plot_success.copy()
    if "rating_number" in gems_df.columns:
        gems_df = gems_df[gems_df["rating_number"] < gems_df["rating_number"].median()].copy()

    gems_df = (
        gems_df.sort_values(["success_score", "average_rating"], ascending=[False, False])
        .head(10)
        .sort_values("success_score", ascending=True)
    )

    fig_gems = px.bar(
        gems_df,
        x="success_score",
        y="short_title",
        orientation="h",
        color="average_rating" if "average_rating" in gems_df.columns else None,
        title="Hidden Gems",
        hover_data={
            "product_title": True,
            "brand": True if "brand" in gems_df.columns else False,
            "price": ":.2f" if "price" in gems_df.columns else False,
            "average_rating": ":.2f" if "average_rating" in gems_df.columns else False,
            "rating_number": ":,.0f" if "rating_number" in gems_df.columns else False,
            "success_score": ":.2f"
        },
        color_continuous_scale="Sunset"
    )

    fig_gems.update_layout(
        xaxis_title="Success Score",
        yaxis_title="Product",
        coloraxis_colorbar_title="Avg Rating",
        margin=dict(l=20, r=20, t=60, b=20)
    )

    st.plotly_chart(fig_gems, use_container_width=True)

st.divider()

# =========================================================
# 7) Product drill-down
# =========================================================
st.subheader("7. Product Drill-Down")
st.markdown(
    """
Inspect a specific product and compare its success profile against the current filtered market.
"""
)

drill_candidates = (
    plot_success.sort_values("success_score", ascending=False)["product_title"]
    .dropna()
    .unique()
    .tolist()
)

selected_product = st.selectbox(
    "Select product",
    options=drill_candidates,
    key="success_product"
) if drill_candidates else None

if selected_product is not None:
    selected_df = plot_success[plot_success["product_title"] == selected_product].copy()

    if not selected_df.empty:
        row = selected_df.iloc[0]

        market_avg_success = plot_success["success_score"].mean() if "success_score" in plot_success.columns else np.nan
        market_avg_prob = plot_success["success_probability"].mean() if "success_probability" in plot_success.columns else np.nan
        market_avg_price = plot_success["price"].mean() if "price" in plot_success.columns else np.nan
        market_avg_rating = plot_success["average_rating"].mean() if "average_rating" in plot_success.columns else np.nan
        market_avg_rating_count = plot_success["rating_number"].mean() if "rating_number" in plot_success.columns else np.nan
        market_avg_value = plot_success["value_score"].mean() if "value_score" in plot_success.columns else np.nan

        st.markdown(f"### {selected_product}")

        c1, c2, c3, c4, c5, c6 = st.columns(6)

        c1.metric(
            "Success Score",
            f"{row['success_score']:.2f}" if pd.notna(row.get("success_score", np.nan)) else "NA",
            delta=(
                f"{row['success_score'] - market_avg_success:+.2f} vs filtered market"
                if pd.notna(row.get("success_score", np.nan)) and pd.notna(market_avg_success)
                else None
            )
        )
        c2.metric(
            "Success Probability",
            f"{row['success_probability']:.2%}" if pd.notna(row.get("success_probability", np.nan)) else "NA",
            delta=(
                f"{row['success_probability'] - market_avg_prob:+.2%} vs filtered market"
                if pd.notna(row.get("success_probability", np.nan)) and pd.notna(market_avg_prob)
                else None
            )
        )
        c3.metric(
            "Value Score",
            f"{row['value_score']:.2f}" if pd.notna(row.get("value_score", np.nan)) else "NA",
            delta=(
                f"{row['value_score'] - market_avg_value:+.2f} vs filtered market"
                if pd.notna(row.get("value_score", np.nan)) and pd.notna(market_avg_value)
                else None
            )
        )
        c4.metric(
            "Price",
            f"${row['price']:,.2f}" if pd.notna(row.get("price", np.nan)) else "NA",
            delta=(
                f"{row['price'] - market_avg_price:+.2f} vs filtered market"
                if pd.notna(row.get("price", np.nan)) and pd.notna(market_avg_price)
                else None
            )
        )
        c5.metric(
            "Avg Rating",
            f"{row['average_rating']:.2f}" if pd.notna(row.get("average_rating", np.nan)) else "NA",
            delta=(
                f"{row['average_rating'] - market_avg_rating:+.2f} vs filtered market"
                if pd.notna(row.get("average_rating", np.nan)) and pd.notna(market_avg_rating)
                else None
            )
        )
        c6.metric(
            "Rating Count",
            f"{int(row['rating_number']):,}" if pd.notna(row.get("rating_number", np.nan)) else "NA",
            delta=(
                f"{row['rating_number'] - market_avg_rating_count:+,.0f} vs filtered market"
                if pd.notna(row.get("rating_number", np.nan)) and pd.notna(market_avg_rating_count)
                else None
            )
        )

        st.divider()

        st.markdown("**Position vs Filtered Market**")

        drill_plot = plot_success.copy()
        drill_plot["is_selected"] = drill_plot["product_title"] == selected_product

        fig_drill = px.scatter(
            drill_plot,
            x="success_score",
            y="rating_number",
            size="price_capped" if "price_capped" in drill_plot.columns else None,
            color="is_selected",
            hover_data=[
                c for c in [
                    "product_title",
                    "brand",
                    "animal_type",
                    "product_type",
                    "price",
                    "average_rating",
                    "rating_number",
                    "value_score",
                    "success_probability",
                    "success_tier"
                ] if c in drill_plot.columns
            ],
            title=f"Selected Product vs Filtered Market: {selected_product}",
            color_discrete_map={True: "#d62728", False: "#9aa0a6"}
        )

        fig_drill.update_layout(
            xaxis_title="Success Score",
            yaxis_title="Rating Count",
            showlegend=False,
            margin=dict(l=20, r=20, t=60, b=20)
        )

        st.plotly_chart(fig_drill, use_container_width=True)

st.divider()

with st.expander("View underlying success model table"):
    display_cols = [
        c for c in [
            "product_title",
            "brand",
            "animal_type",
            "product_type",
            "price",
            "average_rating",
            "rating_number",
            "review_count",
            "reviews_per_month",
            "rating_number_per_month",
            "value_score",
            "success_probability",
            "success_score",
            "success_tier",
            "success_rank",
        ]
        if c in plot_success.columns
    ]

    st.dataframe(
        plot_success[display_cols].sort_values("success_score", ascending=False),
        use_container_width=True
    )
