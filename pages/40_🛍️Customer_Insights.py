import streamlit as st
import pandas as pd
import plotly.express as px

st.title("Customer Insights")
st.markdown(
    """
This section is designed for shoppers and customer-oriented teams.
It highlights what tends to drive stronger product performance and
what kinds of products customers appear to value most.

It focuses on:
- what drives product success
- price vs satisfaction
- top-rated customer favorites
- preferred price ranges
- distribution of product success
"""
)

# ---------------------------------------------------
# Load data
# ---------------------------------------------------
@st.cache_data
def load_data():
    products = pd.read_csv("data/exports/products_master.csv")
    top_products = pd.read_csv("data/exports/top_products.csv")
    success_scores = pd.read_csv("data/exports/product_success_score.csv")
    feature_importance = pd.read_csv("data/exports/product_success_feature_importance.csv")
    price_segments = pd.read_csv("data/exports/price_segments.csv")
    return products, top_products, success_scores, feature_importance, price_segments


try:
    products, top_products, success_scores, feature_importance, price_segments = load_data()

    # ---------------------------------------------------
    # Data cleaning
    # ---------------------------------------------------
    products = products.copy()
    products = products.dropna(subset=["price", "average_rating", "rating_number"])
    products = products[products["price"] > 0]

    success_scores = success_scores.copy()
    success_scores = success_scores.dropna(subset=["success_score"])

    # ---------------------------------------------------
    # KPI cards
    # ---------------------------------------------------
    avg_rating = products["average_rating"].mean()
    median_price = products["price"].median()
    avg_demand = products["rating_number"].mean()

    c1, c2, c3 = st.columns(3)
    c1.metric("Average Product Rating", f"{avg_rating:.2f}")
    c2.metric("Median Price", f"${median_price:.2f}")
    c3.metric("Average Ratings per Product", f"{avg_demand:,.0f}")

    st.markdown("---")

    # ---------------------------------------------------
    # 1. What drives product success
    # ---------------------------------------------------
    st.subheader("What Drives Product Success")

    fi = feature_importance.copy().sort_values("importance_mean", ascending=False)

    fig1 = px.bar(
        fi.sort_values("importance_mean", ascending=True),
        x="importance_mean",
        y="feature",
        orientation="h",
        error_x="importance_std",
        title="Feature Importance in the Product Success Model",
        labels={"importance_mean": "Mean Importance", "feature": ""}
    )
    fig1.update_layout(height=500)
    st.plotly_chart(fig1, use_container_width=True)

    # ---------------------------------------------------
    # 2. Price vs customer satisfaction
    # ---------------------------------------------------
    st.subheader("Price vs Customer Satisfaction")

    scatter_df = products.copy()
    scatter_df["segment"] = scatter_df["category_l2"].astype(str) + " | " + scatter_df["category_l3"].astype(str)

    fig2 = px.scatter(
        scatter_df,
        x="price",
        y="average_rating",
        size="rating_number",
        color="category_l2",
        hover_name="product_title",
        hover_data={
            "brand": True,
            "category_l3": True,
            "rating_number": True,
            "review_count": True,
            "value_score": ":.2f"
        },
        title="Price vs Rating Across Products",
        labels={
            "price": "Price",
            "average_rating": "Average Rating"
        }
    )
    fig2.update_layout(height=600)
    st.plotly_chart(fig2, use_container_width=True)

    st.caption(
        "This view helps identify where customers seem satisfied across different price levels."
    )

    # ---------------------------------------------------
    # 3. Most loved products
    # ---------------------------------------------------
    st.subheader("Most Loved Products")

    loved = top_products.copy()
    loved = loved[
        (loved["average_rating"] >= 4.7) &
        (loved["rating_number"] >= 1000)
    ].sort_values(
        ["average_rating", "rating_number"],
        ascending=[False, False]
    )

    loved_cols = [
        "product_title",
        "brand",
        "category_l2",
        "category_l3",
        "price",
        "average_rating",
        "rating_number",
        "value_score"
    ]

    st.dataframe(
        loved[loved_cols].head(20),
        use_container_width=True
    )

    # ---------------------------------------------------
    # 4. Customer sweet spot by price segment
    # ---------------------------------------------------
    st.subheader("Customer Sweet Spot by Price Segment")

    price_view = price_segments.copy()
    price_view["price_segment"] = price_view["price_segment"].astype(str)

    fig3 = px.bar(
        price_view,
        x="price_segment",
        y="avg_rating",
        color="demand_share_pct",
        hover_data={
            "product_count": True,
            "brand_count": True,
            "avg_price": ":.2f",
            "median_price": ":.2f",
            "avg_value_score": ":.2f",
            "demand_share_pct": ":.2f"
        },
        title="Average Rating Across Price Segments",
        labels={
            "price_segment": "Price Segment",
            "avg_rating": "Average Rating",
            "demand_share_pct": "Demand Share (%)"
        }
    )
    fig3.update_layout(height=500)
    st.plotly_chart(fig3, use_container_width=True)

    # ---------------------------------------------------
    # 5. Product success distribution
    # ---------------------------------------------------
    st.subheader("Product Success Distribution")

    fig4 = px.histogram(
        success_scores,
        x="success_score",
        nbins=30,
        color="success_tier",
        title="Distribution of Product Success Scores",
        labels={"success_score": "Success Score"}
    )
    fig4.update_layout(height=500)
    st.plotly_chart(fig4, use_container_width=True)

    # Optional top success products
    with st.expander("Show top products by success score"):
        top_success = success_scores.sort_values("success_score", ascending=False).head(20)
        st.dataframe(
            top_success[
                [
                    "product_title",
                    "brand",
                    "category_l2",
                    "category_l3",
                    "price",
                    "average_rating",
                    "rating_number",
                    "success_score",
                    "success_tier",
                ]
            ],
            use_container_width=True
        )

except FileNotFoundError as e:
    st.error(f"File not found: {e}")
except Exception as e:
    st.error(f"An error occurred while loading the Customer Insights page: {e}")

# ---------------------------------------------------
# Filters: product type and brand
# ---------------------------------------------------
st.subheader("Explore Ratings by Product Type and Brand")

filter_df = products.copy()

# Clean text fields
filter_df["category_l3"] = filter_df["category_l3"].fillna("Unknown").astype(str).str.strip()
filter_df["brand"] = filter_df["brand"].fillna("Unknown").astype(str).str.strip()

# Remove low-information labels if needed
filter_df = filter_df[
    ~filter_df["brand"].isin(["", "nan", "None"])
]

product_types = ["All"] + sorted(filter_df["category_l3"].dropna().unique().tolist())
selected_product_type = st.selectbox(
    "Select product type",
    product_types,
    index=0
)

if selected_product_type != "All":
    brand_options_df = filter_df[filter_df["category_l3"] == selected_product_type].copy()
else:
    brand_options_df = filter_df.copy()

brand_options = ["All"] + sorted(brand_options_df["brand"].dropna().unique().tolist())
selected_brand = st.selectbox(
    "Select brand",
    brand_options,
    index=0
)

filtered_ratings = filter_df.copy()

if selected_product_type != "All":
    filtered_ratings = filtered_ratings[
        filtered_ratings["category_l3"] == selected_product_type
    ]

if selected_brand != "All":
    filtered_ratings = filtered_ratings[
        filtered_ratings["brand"] == selected_brand
    ]

# Optional minimum review threshold
min_reviews = st.slider(
    "Minimum number of ratings",
    min_value=0,
    max_value=int(filter_df["rating_number"].fillna(0).max()),
    value=100,
    step=50
)

filtered_ratings = filtered_ratings[
    filtered_ratings["rating_number"].fillna(0) >= min_reviews
]

# Summary metrics for selection
m1, m2, m3 = st.columns(3)
m1.metric("Products in Selection", f"{len(filtered_ratings):,}")
m2.metric(
    "Average Rating",
    f"{filtered_ratings['average_rating'].mean():.2f}" if len(filtered_ratings) else "N/A"
)
m3.metric(
    "Average Price",
    f"${filtered_ratings['price'].mean():.2f}" if len(filtered_ratings) else "N/A"
)

# Brand / product type ranking by rating
ranking_mode = st.radio(
    "View ratings ranked by",
    ["Brand", "Product Type"],
    horizontal=True
)

if len(filtered_ratings) == 0:
    st.warning("No products match the selected filters.")
else:
    if ranking_mode == "Brand":
        brand_rank = (
            filtered_ratings
            .groupby("brand", as_index=False)
            .agg(
                avg_rating=("average_rating", "mean"),
                product_count=("product_title", "count"),
                total_ratings=("rating_number", "sum"),
                avg_price=("price", "mean")
            )
        )

        brand_rank = brand_rank[brand_rank["product_count"] >= 2]
        brand_rank = brand_rank.sort_values(
            ["avg_rating", "total_ratings"],
            ascending=[False, False]
        ).head(20)

        fig_filter = px.bar(
            brand_rank.sort_values("avg_rating", ascending=True),
            x="avg_rating",
            y="brand",
            orientation="h",
            color="total_ratings",
            hover_data={
                "product_count": True,
                "total_ratings": True,
                "avg_price": ":.2f"
            },
            title="Top Brands by Average Rating",
            labels={
                "avg_rating": "Average Rating",
                "brand": ""
            }
        )
        fig_filter.update_layout(height=600)
        st.plotly_chart(fig_filter, use_container_width=True)

        st.dataframe(
            brand_rank,
            use_container_width=True
        )

    else:
        type_rank = (
            filtered_ratings
            .groupby("category_l3", as_index=False)
            .agg(
                avg_rating=("average_rating", "mean"),
                product_count=("product_title", "count"),
                total_ratings=("rating_number", "sum"),
                avg_price=("price", "mean")
            )
        )

        type_rank = type_rank[type_rank["product_count"] >= 2]
        type_rank = type_rank.sort_values(
            ["avg_rating", "total_ratings"],
            ascending=[False, False]
        ).head(20)

        fig_filter = px.bar(
            type_rank.sort_values("avg_rating", ascending=True),
            x="avg_rating",
            y="category_l3",
            orientation="h",
            color="total_ratings",
            hover_data={
                "product_count": True,
                "total_ratings": True,
                "avg_price": ":.2f"
            },
            title="Top Product Types by Average Rating",
            labels={
                "avg_rating": "Average Rating",
                "category_l3": ""
            }
        )
        fig_filter.update_layout(height=600)
        st.plotly_chart(fig_filter, use_container_width=True)

        st.dataframe(
            type_rank,
            use_container_width=True
        )

st.markdown("---")
