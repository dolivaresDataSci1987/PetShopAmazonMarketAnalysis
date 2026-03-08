import streamlit as st

st.set_page_config(
    page_title="NOVAres | Pet Market Intelligence",
    page_icon="🐾",
    layout="wide"
)

# ---------------------------------------------------
# Sidebar logo
# ---------------------------------------------------

st.sidebar.image(
    "assets/novares_logo.png",
    use_container_width=True
)

st.set_page_config(
    page_title="Pet Shop Amazon Market Intelligence",
    layout="wide"
)

st.title("Pet Shop Amazon Market Intelligence")
st.caption("A data-driven market intelligence dashboard for Amazon pet product analysis.")

st.markdown(
    """
This platform explores the **Amazon Pet Products market** through a structured set of analytical views.

It combines descriptive, competitive, and opportunity-focused analytics to help answer questions such as:

- How is the market structured?
- Which brands dominate the landscape?
- Which categories are more saturated?
- Where do market gaps exist?
- What drives product success?
"""
)

st.divider()

c1, c2, c3 = st.columns(3)

with c1:
    st.subheader("Market Structure")
    st.markdown(
        """
Explore the composition of the market through:
        - price segmentation
        - product types
        - animal categories
        """
    )

with c2:
    st.subheader("Competition & Opportunity")
    st.markdown(
        """
Analyze:
        - brand landscape
        - category competition
        - opportunity spaces
        - market gaps
        """
    )

with c3:
    st.subheader("Product Intelligence")
    st.markdown(
        """
Evaluate:
        - top products
        - product velocity
        - success scoring
        - success drivers
        """
    )

st.divider()

st.info("Use the navigation menu on the left to explore each section of the dashboard.")
