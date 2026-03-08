import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from utils.load_data import load_products

st.title("Market Structure")
st.markdown(
    """
This section explores how the Amazon Pet Products market is structurally organized
across price tiers, animal types, product types, and brand portfolios.
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

products["brand"] = products["brand"].astype(str).str.strip()
products["animal_type"] = products["category_l2"].astype(str).str.strip()
products["product_type"] = products["category_l3"].astype(str).str.strip()

invalid_labels = ["", "nan", "None", "Unknown", "unknown", "N/A"]

products = products[
    ~products["brand"].isin(invalid_labels) &
    ~products["animal_type"].isin(invalid_labels) &
    ~products["product_type"].isin(invalid_labels)
].copy()

# Optional price cap for cleaner visuals
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
total_product_types = products["product_type"].nunique()
median_price = products["price"].median()
avg_price = products["price"].mean()

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Products", f"{total_products:,}")
c2.metric("Brands", f"{total_brands:,}")
c3.metric("Animal Types", f"{total_animal_types:,}")
c4.metric("Product Types", f"{total_product_types:,}")
c5.metric("Avg Price", f"${avg_price:,.2f}")
c6.metric("Median Price", f"${median_price:,.2f}")

st.divider()

# =========================================================
# 1) Brand distribution by price segment
# =========================================================
st.subheader("1. Brand Distribution Across Price Segments")
st.markdown(
    """
This view shows how many distinct brands compete in each price tier,
together with the number of products available in that segment.
"""
)

brand_price_summary = (
    plot_products.groupby("price_segment", observed=False)
    .agg(
        brand_count=("brand", "nunique"),
        product_count=("parent_asin", "nunique"),
        avg_rating=("average_rating", "mean"),
        avg_price=("price", "mean")
    )
    .reset_index()
)

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
It helps identify where price dispersion is tighter or broader.
"""
)

animal_order = (
    plot_products.groupby("animal_type")
    .size()
    .sort_values(ascending=False)
    .index.tolist()
)

fig_box = px.box(
    plot_products,
    x="animal_type",
    y="price",
    color="animal_type",
    category_orders={"animal_type": animal_order},
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
# 3) Min / Mean / Max price by animal type
# =========================================================
st.subheader("3. Minimum, Average, and Maximum Price by Animal Type")
st.markdown(
    """
This dumbbell chart summarizes the price span of each animal type,
highlighting the average price within the observed minimum–maximum range.
"""
)

animal_price_stats = (
    plot_products.groupby("animal_type")
    .agg(
        min_price=("price", "min"),
        avg_price=("price", "mean"),
        max_price=("price", "max"),
        product_count=("parent_asin", "nunique")
    )
    .reset_index()
    .sort_values("avg_price", ascending=True)
)

fig_dumbbell = go.Figure()

# Range line
fig_dumbbell.add_trace(
    go.Scatter(
        x=animal_price_stats["min_price"],
        y=animal_price_stats["animal_type"],
        mode="markers",
        marker=dict(size=1, opacity=0),
        showlegend=False,
        hoverinfo="skip"
    )
)

for _, row in animal_price_stats.iterrows():
    fig_dumbbell.add_trace(
        go.Scatter(
            x=[row["min_price"], row["max_price"]],
            y=[row["animal_type"], row["animal_type"]],
            mode="lines",
            line=dict(width=5),
            showlegend=False,
            hoverinfo="skip"
        )
    )

# Min markers
fig_dumbbell.add_trace(
    go.Scatter(
        x=animal_price_stats["min_price"],
        y=animal_price_stats["animal_type"],
        mode="markers",
        name="Min Price",
        marker=dict(size=9, symbol="circle"),
        hovertemplate="Animal Type: %{y}<br>Min Price: $%{x:.2f}<extra></extra>"
    )
)

# Mean markers
fig_dumbbell.add_trace(
    go.Scatter(
        x=animal_price_stats["avg_price"],
        y=animal_price_stats["animal_type"],
        mode="markers",
        name="Average Price",
        marker=dict(size=12, symbol="diamond"),
        hovertemplate="Animal Type: %{y}<br>Avg Price: $%{x:.2f}<extra></extra>"
    )
)

# Max markers
fig_dumbbell.add_trace(
    go.Scatter(
        x=animal_price_stats["max_price"],
        y=animal_price_stats["animal_type"],
        mode="markers",
        name="Max Price",
        marker=dict(size=9, symbol="circle-open"),
        hovertemplate="Animal Type: %{y}<br>Max Price: $%{x:.2f}<extra></extra>"
    )
)

fig_dumbbell.update_layout(
    title="Price Span by Animal Type",
    xaxis_title="Price",
    yaxis_title="Animal Type",
    margin=dict(l=20, r=20, t=60, b=20),
    legend_title=""
)

st.plotly_chart(fig_dumbbell, use_container_width=True)

st.divider()

# =========================================================
# 4) Product type by brand
# =========================================================
st.subheader("4. Product-Type Portfolio by Brand")
st.markdown(
    """
This heatmap shows how the top brands are distributed across major product types.
Darker cells indicate a stronger brand presence in that category.
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
    plot_products.groupby("product_type")
    .size()
    .sort_values(ascending=False)
    .head(12)
    .index.tolist()
)

brand_product_heatmap = (
    plot_products[
        plot_products["brand"].isin(top_brands) &
        plot_products["product_type"].isin(top_product_types)
    ]
    .groupby(["brand", "product_type"])
    .size()
    .reset_index(name="product_count")
)

heatmap_matrix = brand_product_heatmap.pivot(
    index="brand",
    columns="product_type",
    values="product_count"
).fillna(0)

# Order rows by total portfolio size
heatmap_matrix = heatmap_matrix.loc[
    heatmap_matrix.sum(axis=1).sort_values(ascending=False).index
]

fig_heatmap = px.imshow(
    heatmap_matrix,
    labels=dict(x="Product Type", y="Brand", color="Product Count"),
    aspect="auto",
    color_continuous_scale="Blues",
    title="Top Brands vs Top Product Types"
)

fig_heatmap.update_layout(
    margin=dict(l=20, r=20, t=60, b=20)
)

st.plotly_chart(fig_heatmap, use_container_width=True)

st.divider()

# =========================================================
# 5) Additional non-redundant view:
# Supply share vs demand share by animal type
# =========================================================
st.subheader("5. Supply vs Demand Balance by Animal Type")
st.markdown(
    """
This additional view compares each animal type's share of total products
against its share of total demand proxy. It helps identify categories
that may be overrepresented or underrepresented structurally.
"""
)

animal_balance = (
    products.groupby("animal_type")
    .agg(
        product_count=("parent_asin", "nunique"),
        brand_count=("brand", "nunique"),
        avg_price=("price", "mean"),
        demand_proxy=("rating_number", "sum")
    )
    .reset_index()
)

animal_balance["product_share_pct"] = (
    animal_balance["product_count"] / animal_balance["product_count"].sum() * 100
)

animal_balance["demand_share_pct"] = (
    animal_balance["demand_proxy"] / animal_balance["demand_proxy"].sum() * 100
)

fig_balance = px.scatter(
    animal_balance,
    x="product_share_pct",
    y="demand_share_pct",
    size="brand_count",
    color="avg_price",
    text="animal_type",
    title="Category Balance: Product Share vs Demand Share",
    hover_data={
        "animal_type": True,
        "product_count": True,
        "brand_count": True,
        "avg_price": ":.2f",
        "product_share_pct": ":.1f",
        "demand_share_pct": ":.1f"
    },
    color_continuous_scale="Tealgrn"
)

fig_balance.update_traces(
    textposition="top center",
    marker=dict(line=dict(width=1, color="white"))
)

# Diagonal reference line
max_axis = max(
    animal_balance["product_share_pct"].max(),
    animal_balance["demand_share_pct"].max()
) * 1.08

fig_balance.add_shape(
    type="line",
    x0=0, y0=0, x1=max_axis, y1=max_axis,
    line=dict(dash="dash")
)

fig_balance.update_layout(
    xaxis_title="Share of Total Products (%)",
    yaxis_title="Share of Total Demand Proxy (%)",
    coloraxis_colorbar_title="Avg Price",
    margin=dict(l=20, r=20, t=60, b=20)
)

st.plotly_chart(fig_balance, use_container_width=True)
