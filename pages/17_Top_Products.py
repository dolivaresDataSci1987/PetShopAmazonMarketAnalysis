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

    # Force numeric types safely
    bubble_df["average_rating"] = pd.to_numeric(bubble_df["average_rating"], errors="coerce")
    bubble_df["rating_number"] = pd.to_numeric(bubble_df["rating_number"], errors="coerce")

    if "price" in bubble_df.columns:
        bubble_df["price"] = pd.to_numeric(bubble_df["price"], errors="coerce")

    # Remove invalid rows
    bubble_df = bubble_df.dropna(subset=["average_rating", "rating_number"])

    # Optional cap for bubble size so huge products do not dominate
    if "price" in bubble_df.columns:
        bubble_df = bubble_df.dropna(subset=["price"])
        bubble_df = bubble_df[bubble_df["price"] > 0].copy()
        price_cap = bubble_df["price"].quantile(0.95)
        bubble_df["price_capped"] = bubble_df["price"].clip(upper=price_cap)
        size_col = "price_capped"
    else:
        size_col = None

    if not bubble_df.empty:
        fig_bubble = px.scatter(
            bubble_df,
            x="average_rating",
            y="rating_number",
            size=size_col,
            color="brand" if "brand" in bubble_df.columns else None,
            hover_name="short_title" if "short_title" in bubble_df.columns else None,
            hover_data=[
                c for c in ["product_title", "brand", "price", "average_rating", "rating_number"]
                if c in bubble_df.columns
            ],
            title="Product Quality vs Market Validation"
        )

        fig_bubble.update_layout(
            xaxis_title="Average Rating",
            yaxis_title="Rating Count",
            margin=dict(l=20, r=20, t=60, b=20)
        )

        st.plotly_chart(fig_bubble, use_container_width=True)
    else:
        st.info("Not enough valid data to display the Rating vs Review Volume chart.")

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

st.divider()

# =========================================================
# Dynamic Top-20 Explorer
# =========================================================
st.header("Dynamic Top-20 Explorer")
st.markdown(
    """
Explore Top-20 product rankings dynamically by brand, animal type, or product type.
"""
)

# ---------------------------------------------------------
# Safe helpers
# ---------------------------------------------------------
def shorten_title(title, max_words=12):
    if not isinstance(title, str):
        return str(title)
    words = title.split()
    if len(words) <= max_words:
        return title
    return " ".join(words[:max_words]) + "..."

def safe_numeric(df, cols):
    for col in cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

# Ensure columns exist / are cleaned
explorer_df = top_products.copy()

for col in explorer_df.columns:
    if explorer_df[col].dtype == "object":
        explorer_df[col] = explorer_df[col].astype(str).str.strip()

explorer_df = safe_numeric(
    explorer_df,
    ["price", "average_rating", "rating_number", "review_count"]
)

if "product_title" in explorer_df.columns:
    explorer_df["short_title"] = explorer_df["product_title"].apply(lambda x: shorten_title(x, max_words=12))
else:
    explorer_df["product_title"] = "Unknown product"
    explorer_df["short_title"] = "Unknown product"

# Normalize animal/product columns if needed
animal_col = None
for c in ["animal_type", "category_l2"]:
    if c in explorer_df.columns:
        animal_col = c
        break

product_col = None
for c in ["product_type", "category_l3"]:
    if c in explorer_df.columns:
        product_col = c
        break

brand_col = "brand" if "brand" in explorer_df.columns else None

if animal_col is None:
    explorer_df["animal_type_fallback"] = "Unknown"
    animal_col = "animal_type_fallback"

if product_col is None:
    explorer_df["product_type_fallback"] = "Unknown"
    product_col = "product_type_fallback"

if brand_col is None:
    explorer_df["brand"] = "Unknown"
    brand_col = "brand"

# ---------------------------------------------------------
# Explorer mode selector
# ---------------------------------------------------------
mode = st.selectbox(
    "Select ranking view",
    options=[
        "Top 20 by Brand → Highest Price",
        "Top 20 by Brand → Lowest Price",
        "Top 20 by Brand → Best Rating",
        "Top 20 by Animal Type → Best Rating",
        "Top 20 by Product Type → Best Rating",
    ]
)

# ---------------------------------------------------------
# Mode 1/2/3: By Brand
# ---------------------------------------------------------
if mode in [
    "Top 20 by Brand → Highest Price",
    "Top 20 by Brand → Lowest Price",
    "Top 20 by Brand → Best Rating",
]:
    brand_options = sorted(explorer_df[brand_col].dropna().unique().tolist())
    selected_brand = st.selectbox("Select brand", options=brand_options)

    brand_df = explorer_df[explorer_df[brand_col] == selected_brand].copy()

    if mode == "Top 20 by Brand → Highest Price":
        brand_df = brand_df.dropna(subset=["price"]).sort_values("price", ascending=False).head(20)
        ranking_metric = "price"
        chart_title = f"Top 20 Products from {selected_brand} by Highest Price"

    elif mode == "Top 20 by Brand → Lowest Price":
        brand_df = brand_df.dropna(subset=["price"])
        brand_df = brand_df[brand_df["price"] > 0].sort_values("price", ascending=True).head(20)
        ranking_metric = "price"
        chart_title = f"Top 20 Products from {selected_brand} by Lowest Price"

    else:
        brand_df = brand_df.dropna(subset=["average_rating"]).sort_values(
            ["average_rating", "rating_number"],
            ascending=[False, False]
        ).head(20)
        ranking_metric = "average_rating"
        chart_title = f"Top 20 Products from {selected_brand} by Best Rating"

    if brand_df.empty:
        st.info("No products available for the selected ranking.")
    else:
        show_cols = [
            c for c in [
                "product_title",
                "brand",
                animal_col,
                product_col,
                "price",
                "average_rating",
                "rating_number",
                "review_count"
            ]
            if c in brand_df.columns
        ]

        st.dataframe(brand_df[show_cols], use_container_width=True)

        plot_df = brand_df.copy()

        if ranking_metric == "price":
            plot_df = plot_df.sort_values("price", ascending=True)
            fig = px.bar(
                plot_df,
                x="price",
                y="short_title",
                orientation="h",
                color="average_rating" if "average_rating" in plot_df.columns else None,
                title=chart_title,
                hover_data={
                    "product_title": True,
                    "brand": True,
                    animal_col: True,
                    product_col: True,
                    "price": ":.2f" if "price" in plot_df.columns else False,
                    "average_rating": ":.2f" if "average_rating" in plot_df.columns else False,
                    "rating_number": ":,.0f" if "rating_number" in plot_df.columns else False,
                },
                color_continuous_scale="Tealgrn"
            )
            fig.update_layout(
                xaxis_title="Price",
                yaxis_title="Product",
                margin=dict(l=20, r=20, t=60, b=20)
            )
            st.plotly_chart(fig, use_container_width=True)

        else:
            plot_df = plot_df.sort_values("average_rating", ascending=True)
            fig = px.bar(
                plot_df,
                x="average_rating",
                y="short_title",
                orientation="h",
                color="rating_number" if "rating_number" in plot_df.columns else None,
                title=chart_title,
                hover_data={
                    "product_title": True,
                    "brand": True,
                    animal_col: True,
                    product_col: True,
                    "price": ":.2f" if "price" in plot_df.columns else False,
                    "average_rating": ":.2f" if "average_rating" in plot_df.columns else False,
                    "rating_number": ":,.0f" if "rating_number" in plot_df.columns else False,
                },
                color_continuous_scale="Blues"
            )
            fig.update_layout(
                xaxis_title="Average Rating",
                yaxis_title="Product",
                margin=dict(l=20, r=20, t=60, b=20)
            )
            st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------
# Mode 4: By Animal Type
# ---------------------------------------------------------
elif mode == "Top 20 by Animal Type → Best Rating":
    animal_options = sorted(explorer_df[animal_col].dropna().unique().tolist())
    selected_animal = st.selectbox("Select animal type", options=animal_options)

    animal_df = explorer_df[explorer_df[animal_col] == selected_animal].copy()
    animal_df = animal_df.dropna(subset=["average_rating"]).sort_values(
        ["average_rating", "rating_number"],
        ascending=[False, False]
    ).head(20)

    if animal_df.empty:
        st.info("No products available for the selected animal type.")
    else:
        show_cols = [
            c for c in [
                "product_title",
                "brand",
                animal_col,
                product_col,
                "price",
                "average_rating",
                "rating_number",
                "review_count"
            ]
            if c in animal_df.columns
        ]

        st.dataframe(animal_df[show_cols], use_container_width=True)

        plot_df = animal_df.sort_values("average_rating", ascending=True)

        fig = px.bar(
            plot_df,
            x="average_rating",
            y="short_title",
            orientation="h",
            color="brand",
            title=f"Top 20 {selected_animal} Products by Best Rating",
            hover_data={
                "product_title": True,
                "brand": True,
                product_col: True,
                "price": ":.2f" if "price" in plot_df.columns else False,
                "average_rating": ":.2f" if "average_rating" in plot_df.columns else False,
                "rating_number": ":,.0f" if "rating_number" in plot_df.columns else False,
            }
        )

        fig.update_layout(
            xaxis_title="Average Rating",
            yaxis_title="Product",
            margin=dict(l=20, r=20, t=60, b=20)
        )

        st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------
# Mode 5: By Product Type
# ---------------------------------------------------------
elif mode == "Top 20 by Product Type → Best Rating":
    product_options = sorted(explorer_df[product_col].dropna().unique().tolist())
    selected_product_type = st.selectbox("Select product type", options=product_options)

    product_df = explorer_df[explorer_df[product_col] == selected_product_type].copy()
    product_df = product_df.dropna(subset=["average_rating"]).sort_values(
        ["average_rating", "rating_number"],
        ascending=[False, False]
    ).head(20)

    if product_df.empty:
        st.info("No products available for the selected product type.")
    else:
        show_cols = [
            c for c in [
                "product_title",
                "brand",
                animal_col,
                product_col,
                "price",
                "average_rating",
                "rating_number",
                "review_count"
            ]
            if c in product_df.columns
        ]

        st.dataframe(product_df[show_cols], use_container_width=True)

        plot_df = product_df.sort_values("average_rating", ascending=True)

        fig = px.bar(
            plot_df,
            x="average_rating",
            y="short_title",
            orientation="h",
            color="brand",
            title=f"Top 20 {selected_product_type} Products by Best Rating",
            hover_data={
                "product_title": True,
                "brand": True,
                animal_col: True,
                "price": ":.2f" if "price" in plot_df.columns else False,
                "average_rating": ":.2f" if "average_rating" in plot_df.columns else False,
                "rating_number": ":,.0f" if "rating_number" in plot_df.columns else False,
            }
        )

        fig.update_layout(
            xaxis_title="Average Rating",
            yaxis_title="Product",
            margin=dict(l=20, r=20, t=60, b=20)
        )

        st.plotly_chart(fig, use_container_width=True)
