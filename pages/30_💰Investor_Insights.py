import streamlit as st
import pandas as pd
import plotly.express as px

st.title("Investor Insights")
st.markdown(
    """
This section is designed for investors, founders, and operators exploring
where the Amazon pet products market may offer the best opportunities.

It focuses on:
- demand vs competition
- underserved niches
- price segment attractiveness
- fast-moving product areas
- brand dominance risk
"""
)

# ---------------------------------------------------
# Load data
# ---------------------------------------------------
@st.cache_data
def load_data():
    category_opportunity = pd.read_csv("data/exports/category_opportunity.csv")
    market_gap = pd.read_csv("data/exports/market_gap_analysis.csv")
    category_comp = pd.read_csv("data/exports/category_competition.csv")
    price_segments = pd.read_csv("data/exports/price_segments.csv")
    product_velocity = pd.read_csv("data/exports/product_velocity.csv")
    brand_summary = pd.read_csv("data/exports/brand_summary.csv")
    return (
        category_opportunity,
        market_gap,
        category_comp,
        price_segments,
        product_velocity,
        brand_summary,
    )


try:
    (
        category_opportunity,
        market_gap,
        category_comp,
        price_segments,
        product_velocity,
        brand_summary,
    ) = load_data()

    # ---------------------------------------------------
    # KPI cards
    # ---------------------------------------------------
    total_categories = category_comp["product_type"].nunique()
    total_brands = int(brand_summary["brand"].nunique())
    total_products = int(product_velocity["parent_asin"].nunique())

    c1, c2, c3 = st.columns(3)
    c1.metric("Categories Tracked", f"{total_categories:,}")
    c2.metric("Brands Tracked", f"{total_brands:,}")
    c3.metric("Products Tracked", f"{total_products:,}")

    st.markdown("---")

    # ---------------------------------------------------
    # 1. Market opportunity landscape
    # ---------------------------------------------------
    st.subheader("Market Opportunity Landscape")

    opp_plot = category_opportunity.copy()
    opp_plot = opp_plot.merge(
        category_comp[["animal_type", "product_type", "competition_score"]],
        on=["animal_type", "product_type"],
        how="left"
    )

    opp_plot["segment"] = opp_plot["animal_type"] + " | " + opp_plot["product_type"]

    fig = px.scatter(
        opp_plot,
        x="competition_score",
        y="total_rating_number",
        size="product_count",
        color="animal_type",
        hover_name="segment",
        hover_data={
            "avg_price": ":.2f",
            "avg_rating": ":.2f",
            "opportunity_score": ":.2f",
            "competition_score": ":.2f",
            "product_count": True,
            "total_rating_number": True
        },
        title="Demand vs Competition Across Product Segments",
        labels={
            "competition_score": "Competition Score",
            "total_rating_number": "Demand Proxy (Total Ratings)"
        }
    )
    fig.update_layout(height=550)
    st.plotly_chart(fig, use_container_width=True)

    st.caption(
        "Segments in the upper-left area combine stronger demand with lower competition, "
        "making them especially interesting for new entrants."
    )

    # ---------------------------------------------------
    # 2. Top underserved niches
    # ---------------------------------------------------
    st.subheader("Top Underserved Niches")

    gap_view = market_gap.copy()
    gap_view["segment"] = gap_view["animal_type"] + " | " + gap_view["product_type"]

    gap_view = gap_view.sort_values(
        ["gap_score", "opportunity_score"],
        ascending=False
    )

    display_cols = [
        "animal_type",
        "product_type",
        "product_count",
        "brand_count",
        "avg_price",
        "avg_rating",
        "total_rating_number",
        "competition_tier",
        "competition_score",
        "gap_score",
        "opportunity_score",
    ]

    st.dataframe(
        gap_view[display_cols].head(20),
        use_container_width=True
    )

    # ---------------------------------------------------
    # 3. Price segment attractiveness
    # ---------------------------------------------------
    st.subheader("Price Segment Attractiveness")

    price_plot = price_segments.copy()
    price_plot["price_segment"] = price_plot["price_segment"].astype(str)

    fig2 = px.scatter(
        price_plot,
        x="avg_price",
        y="demand_share_pct",
        size="product_count",
        color="avg_rating",
        hover_name="price_segment",
        hover_data={
            "avg_rating": ":.2f",
            "avg_value_score": ":.2f",
            "product_share_pct": ":.2f",
            "brand_count": True
        },
        title="Demand Share by Price Segment",
        labels={
            "avg_price": "Average Price",
            "demand_share_pct": "Demand Share (%)",
            "avg_rating": "Average Rating"
        }
    )
    fig2.update_layout(height=500)
    st.plotly_chart(fig2, use_container_width=True)

    # ---------------------------------------------------
    # 4. Fastest moving product segments
    # ---------------------------------------------------
    st.subheader("Fastest Moving Product Segments")

    velocity_seg = (
        product_velocity
        .groupby(["category_l2", "category_l3"], as_index=False)
        .agg(
            product_count=("parent_asin", "count"),
            avg_velocity_score=("velocity_score", "mean"),
            avg_reviews_per_month=("reviews_per_month", "mean"),
            total_rating_number=("rating_number", "sum"),
            avg_rating=("average_rating", "mean"),
            avg_price=("price", "mean"),
        )
    )

    velocity_seg["segment"] = velocity_seg["category_l2"] + " | " + velocity_seg["category_l3"]
    velocity_seg = velocity_seg.sort_values("avg_velocity_score", ascending=False).head(20)

    fig3 = px.bar(
        velocity_seg.sort_values("avg_velocity_score", ascending=True),
        x="avg_velocity_score",
        y="segment",
        color="category_l2",
        orientation="h",
        hover_data={
            "product_count": True,
            "avg_reviews_per_month": ":.2f",
            "total_rating_number": True,
            "avg_rating": ":.2f",
            "avg_price": ":.2f"
        },
        title="Top 20 Fastest Moving Segments",
        labels={"avg_velocity_score": "Average Velocity Score", "segment": ""}
    )
    fig3.update_layout(height=700, yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig3, use_container_width=True)

    # ---------------------------------------------------
    # 5. Brand dominance risk
    # ---------------------------------------------------
    st.subheader("Brand Dominance Risk")

    top_brands = (
        brand_summary
        .sort_values("demand_proxy", ascending=False)
        .head(15)
        .copy()
    )

    fig4 = px.bar(
        top_brands.sort_values("demand_proxy", ascending=True),
        x="demand_proxy",
        y="brand",
        orientation="h",
        color="brand_strength_score",
        hover_data={
            "product_count": True,
            "avg_price": ":.2f",
            "avg_rating": ":.2f",
            "product_types_count": True,
            "animal_types_count": True,
            "brand_strength_score": ":.2f"
        },
        title="Top Brands by Demand Proxy",
        labels={"demand_proxy": "Demand Proxy", "brand": ""}
    )
    fig4.update_layout(height=650)
    st.plotly_chart(fig4, use_container_width=True)

    st.info(
        "A market dominated by a few brands may be harder to enter. "
        "More fragmented spaces can offer better room for challenger brands."
    )

except FileNotFoundError as e:
    st.error(f"File not found: {e}")
except Exception as e:
    st.error(f"An error occurred while loading the Investor Insights page: {e}")
