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
