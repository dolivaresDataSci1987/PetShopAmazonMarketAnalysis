import pandas as pd
import streamlit as st

DATA_PATH = "data/exports/"


@st.cache_data
def load_products():
    return pd.read_csv(DATA_PATH + "products_master.csv")


@st.cache_data
def load_brand_summary():
    return pd.read_csv(DATA_PATH + "brand_summary.csv")


@st.cache_data
def load_brand_product_matrix():
    return pd.read_csv(DATA_PATH + "brand_product_matrix.csv")


@st.cache_data
def load_brand_animal_matrix():
    return pd.read_csv(DATA_PATH + "brand_animal_matrix.csv")


@st.cache_data
def load_price_segments():
    return pd.read_csv(DATA_PATH + "price_segments.csv")


@st.cache_data
def load_product_types():
    return pd.read_csv(DATA_PATH + "product_type_summary.csv")


@st.cache_data
def load_animal_categories():
    return pd.read_csv(DATA_PATH + "animal_category_summary.csv")


@st.cache_data
def load_category_competition():
    return pd.read_csv(DATA_PATH + "category_competition.csv")


@st.cache_data
def load_category_opportunity():
    return pd.read_csv(DATA_PATH + "category_opportunity.csv")


@st.cache_data
def load_market_gaps():
    return pd.read_csv(DATA_PATH + "market_gap_analysis.csv")


@st.cache_data
def load_product_velocity():
    return pd.read_csv(DATA_PATH + "product_velocity.csv")


@st.cache_data
def load_top_products():
    return pd.read_csv(DATA_PATH + "top_products.csv")


@st.cache_data
def load_product_success():
    return pd.read_csv(DATA_PATH + "product_success_score.csv")


@st.cache_data
def load_feature_importance():
    return pd.read_csv(DATA_PATH + "product_success_feature_importance.csv")
