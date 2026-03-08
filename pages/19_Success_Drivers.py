import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

from utils.load_data import load_feature_importance, load_product_success_score

st.title("Success Drivers")

st.markdown(
"""
This page explains which variables contribute most strongly to the product
success scoring framework and how these drivers relate to real market signals.
"""
)

# =========================================================
# Load data
# =========================================================
importance = load_feature_importance().copy()

try:
    success = load_product_success_score().copy()
except:
    success = None

# =========================================================
# Basic cleaning
# =========================================================
for col in importance.columns:
    if importance[col].dtype == "object":
        importance[col] = importance[col].astype(str).str.strip()

for col in ["importance_mean", "importance_std"]:
    if col in importance.columns:
        importance[col] = pd.to_numeric(importance[col], errors="coerce")

importance = importance.dropna(subset=["importance_mean"]).copy()

# =========================================================
# KPI block
# =========================================================
top_feature = importance.sort_values("importance_mean", ascending=False).iloc[0]["feature"]
avg_importance = importance["importance_mean"].mean()
num_features = len(importance)

c1, c2, c3 = st.columns(3)

c1.metric("Features in Model", f"{num_features}")
c2.metric("Top Driver", top_feature)
c3.metric("Avg Feature Importance", f"{avg_importance:.3f}")

st.divider()

# =========================================================
# 1 Feature importance ranking
# =========================================================
st.subheader("1. Feature Importance Ranking")

st.markdown(
"""
This ranking shows which variables contribute most strongly to the product success model.
"""
)

top_features = (
    importance.sort_values("importance_mean", ascending=False)
    .head(15)
    .sort_values("importance_mean")
)

fig_importance = px.bar(
    top_features,
    x="importance_mean",
    y="feature",
    orientation="h",
    error_x="importance_std" if "importance_std" in top_features.columns else None,
    title="Top Model Drivers of Product Success",
)

fig_importance.update_layout(
    xaxis_title="Mean Importance",
    yaxis_title="Feature",
    margin=dict(l=20, r=20, t=60, b=20)
)

st.plotly_chart(fig_importance, use_container_width=True)

st.divider()

# =========================================================
# 2 Cumulative importance
# =========================================================
st.subheader("2. Cumulative Model Importance")

importance_sorted = importance.sort_values("importance_mean", ascending=False).copy()
importance_sorted["cumulative_importance"] = importance_sorted["importance_mean"].cumsum()
importance_sorted["cumulative_importance"] = (
    importance_sorted["cumulative_importance"] /
    importance_sorted["importance_mean"].sum()
)

fig_cum = px.line(
    importance_sorted,
    x=np.arange(1, len(importance_sorted) + 1),
    y="cumulative_importance",
    markers=True,
    title="Cumulative Contribution of Model Features"
)

fig_cum.update_layout(
    xaxis_title="Number of Features",
    yaxis_title="Cumulative Importance",
    margin=dict(l=20, r=20, t=60, b=20)
)

st.plotly_chart(fig_cum, use_container_width=True)

st.divider()

# =========================================================
# 3 Feature interpretation
# =========================================================
st.subheader("3. Business Interpretation of Drivers")

feature_explanations = {
    "price": "Product pricing influences perceived value positioning.",
    "average_rating": "Customer satisfaction strongly impacts product success.",
    "rating_number": "Products with more ratings usually signal stronger validation.",
    "review_count": "High review counts often correlate with demand and visibility.",
    "reviews_per_month": "Fast review accumulation indicates strong momentum.",
    "rating_number_per_month": "A proxy for product growth velocity.",
    "value_score": "Captures perceived value relative to price and rating.",
}

importance_sorted["interpretation"] = importance_sorted["feature"].map(
    feature_explanations
)

st.dataframe(
    importance_sorted[["feature", "importance_mean", "interpretation"]],
    use_container_width=True
)

st.divider()

# =========================================================
# 4 Correlation with success score
# =========================================================
st.subheader("4. Relationship Between Drivers and Success Score")

if success is not None and "success_score" in success.columns:

    numeric_cols = success.select_dtypes(include="number").columns.tolist()

    if len(numeric_cols) > 2:

        corr = success[numeric_cols].corr()["success_score"].drop("success_score")
        corr_df = corr.reset_index()
        corr_df.columns = ["feature", "correlation"]

        corr_df = corr_df.sort_values("correlation", ascending=False)

        fig_corr = px.bar(
            corr_df.head(12).sort_values("correlation"),
            x="correlation",
            y="feature",
            orientation="h",
            title="Correlation Between Drivers and Success Score"
        )

        fig_corr.update_layout(
            xaxis_title="Correlation with Success Score",
            yaxis_title="Feature",
            margin=dict(l=20, r=20, t=60, b=20)
        )

        st.plotly_chart(fig_corr, use_container_width=True)

else:
    st.info("Success score dataset not available to compute correlations.")

st.divider()

# =========================================================
# 5 Driver explorer
# =========================================================
st.subheader("5. Driver Explorer")

selected_feature = st.selectbox(
    "Select a model feature",
    importance_sorted["feature"].tolist()
)

selected_row = importance_sorted[importance_sorted["feature"] == selected_feature].iloc[0]

st.metric(
    "Feature Importance",
    f"{selected_row['importance_mean']:.4f}"
)

if "interpretation" in selected_row and pd.notna(selected_row["interpretation"]):
    st.write(selected_row["interpretation"])
else:
    st.write("No business interpretation available for this feature.")

st.divider()

with st.expander("View raw feature importance table"):
    st.dataframe(importance.sort_values("importance_mean", ascending=False),
                 use_container_width=True)
