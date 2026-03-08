import streamlit as st


def add_brand_filter(df, column="brand", key="brand_filter"):
    if column not in df.columns:
        return df

    brands = sorted([b for b in df[column].dropna().unique().tolist() if str(b).strip() != ""])
    selected = st.multiselect("Select brand(s)", brands, default=[], key=key)

    if selected:
        df = df[df[column].isin(selected)]

    return df


def add_animal_filter(df, column="animal_type", key="animal_filter"):
    if column not in df.columns:
        return df

    animals = sorted([a for a in df[column].dropna().unique().tolist() if str(a).strip() != ""])
    selected = st.multiselect("Select animal type(s)", animals, default=[], key=key)

    if selected:
        df = df[df[column].isin(selected)]

    return df


def add_price_filter(df, column="price", key="price_filter"):
    if column not in df.columns or df.empty:
        return df

    min_price = float(df[column].min())
    max_price = float(df[column].max())

    selected_range = st.slider(
        "Select price range",
        min_value=float(min_price),
        max_value=float(max_price),
        value=(float(min_price), float(max_price)),
        key=key
    )

    df = df[(df[column] >= selected_range[0]) & (df[column] <= selected_range[1])]
    return df
