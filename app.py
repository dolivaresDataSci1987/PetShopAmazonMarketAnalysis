import streamlit as st

st.set_page_config(
    page_title="NOVAres | Pet Market Intelligence",
    page_icon="🐾",
    layout="wide"
)

GITHUB_URL = "https://github.com/dolivaresDataSci1987/PetShopAmazonMarketAnalysis/tree/main"

# ---------------------------------------------------
# Custom CSS
# ---------------------------------------------------
st.markdown(
    """
    <style>
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 1250px;
        }

.hero-box {
    background: linear-gradient(135deg, #2E145C 0%, #3A1C71 100%);
    border-radius: 0px;
    padding: 2.4rem 2.6rem;
    min-height: 220px;
}
        }

       .hero-kicker {
    font-size: 0.9rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: white !important;
}

        .hero-title {
            font-size: 3.25rem;
            font-weight: 800;
            line-height: 1.05;
            margin-bottom: 0.9rem;
            color: white;
        }

        .hero-subtitle {
            font-size: 1.18rem;
            line-height: 1.65;
            color: white;
            max-width: 90%;
            margin-bottom: 1.2rem;
        }

        .hero-meta {
            font-size: 0.98rem;
            color: white;
            font-weight: 500;
        }

        .logo-card {
            background: linear-gradient(135deg, #2E145C 0%, #3A1C71 100%);
            border-radius: 0px;
            min-height: 280px;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 2rem;
            box-shadow: 0 10px 28px rgba(0,0,0,0.12);
        }

        .section-text {
            font-size: 1.03rem;
            line-height: 1.75;
            color: #4B5563;
        }

        .card {
            background: white;
            border: 1px solid #E5E7EB;
            border-radius: 0px;
            padding: 1.4rem 1.3rem;
            min-height: 220px;
            box-shadow: 0 4px 14px rgba(0,0,0,0.04);
        }

        .card-title {
            font-size: 1.55rem;
            font-weight: 800;
            margin-bottom: 0.8rem;
            color: #1F2937;
        }

        .card-text {
            font-size: 1rem;
            line-height: 1.75;
            color: #4B5563;
        }

        .mini-pill {
            display: inline-block;
            padding: 0.35rem 0.7rem;
            border-radius: 999px;
            background: #F3F4F6;
            color: #374151;
            font-size: 0.85rem;
            font-weight: 600;
            margin-right: 0.4rem;
            margin-bottom: 0.5rem;
        }

        .cta-box {
            background: #EEF4FF;
            border: 1px solid #D9E7FF;
            border-radius: 16px;
            padding: 1rem 1.1rem;
            color: #1E5BB8;
            font-size: 1rem;
            font-weight: 600;
            margin-top: 1.2rem;
        }

        .meta-link {
            font-size: 0.96rem;
            color: #4B5563;
            margin-top: 0.5rem;
        }

        .meta-link a {
            color: #1E5BB8;
            text-decoration: none;
            font-weight: 600;
        }

        .meta-link a:hover {
            text-decoration: underline;
        }

        [data-testid="stSidebarNav"] {
            padding-top: 1rem;
        }
    </style>
    """,
    unsafe_allow_html=True

    [data-testid="stImage"] img {
    border-radius: 0px !important;
}
)

# ---------------------------------------------------
# Sidebar
# ---------------------------------------------------
st.sidebar.markdown("## NOVAres")
st.sidebar.caption("Pet Market Intelligence")
st.sidebar.markdown("**Author:** David Olivares")
st.sidebar.markdown("**Year:** 2026")
st.sidebar.markdown(f"[GitHub Project]({GITHUB_URL})")
st.sidebar.markdown("---")

# ---------------------------------------------------
# HERO
# ---------------------------------------------------

hero_left, hero_right = st.columns([4,1])

with hero_left:

    st.markdown(
        """
        <div class="hero-box">

        <div class="hero-kicker">
        NOVAres · Market Intelligence Dashboard
        </div>

        <div class="hero-title">
        Pet Shop Amazon Market Intelligence
        </div>

        <div class="hero-subtitle">
        A strategic analytics dashboard for exploring the Amazon pet products market,
        identifying competitive dynamics, whitespace opportunities,
        and product success patterns.
        </div>

        <div class="hero-meta">
        Author: <b>David Olivares</b> · 2026
        </div>

        </div>
        """,
        unsafe_allow_html=True
    )

with hero_right:
    st.image(
        "assets/novares_logo.png",
        width=220
    )

# ---------------------------------------------------
# Repo link under hero
# ---------------------------------------------------
st.markdown(
    f"""
    <div class="meta-link">
        Repository: <a href="{GITHUB_URL}" target="_blank">{GITHUB_URL}</a>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown("")

# ---------------------------------------------------
# Intro
# ---------------------------------------------------
st.markdown(
    """
    <div class="section-text">
        This platform explores the <b>Amazon Pet Products market</b> through a structured set of analytical views.
        It combines descriptive, competitive, and opportunity-focused analytics to support strategic questions such as:
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown("")

q1, q2 = st.columns(2)

with q1:
    st.markdown(
        """
        <div class="section-text">
        • How is the market structured?<br>
        • Which brands dominate the landscape?<br>
        • Which categories are more saturated?
        </div>
        """,
        unsafe_allow_html=True
    )

with q2:
    st.markdown(
        """
        <div class="section-text">
        • Where do market gaps exist?<br>
        • What drives product success?<br>
        • Where are the most attractive opportunities?
        </div>
        """,
        unsafe_allow_html=True
    )

st.divider()

# ---------------------------------------------------
# Main cards
# ---------------------------------------------------
c1, c2, c3 = st.columns(3)

with c1:
    st.markdown(
        """
        <div class="card">
            <div class="card-title">Market Structure</div>
            <div class="card-text">
                Understand how the market is composed across categories, animal types,
                price architecture, and product distribution.
            </div>
            <br>
            <span class="mini-pill">Overview</span>
            <span class="mini-pill">Market Structure</span>
            <span class="mini-pill">Top Products</span>
        </div>
        """,
        unsafe_allow_html=True
    )

with c2:
    st.markdown(
        """
        <div class="card">
            <div class="card-title">Competition & Opportunity</div>
            <div class="card-text">
                Identify crowded segments, whitespace opportunities, competitive pressure,
                and category-level gaps with strategic relevance.
            </div>
            <br>
            <span class="mini-pill">Brand Landscape</span>
            <span class="mini-pill">Category Competition</span>
            <span class="mini-pill">Opportunity Map</span>
            <span class="mini-pill">Market Gaps</span>
        </div>
        """,
        unsafe_allow_html=True
    )

with c3:
    st.markdown(
        """
        <div class="card">
            <div class="card-title">Product Intelligence</div>
            <div class="card-text">
                Explore product momentum, success scoring, and the variables most strongly
                associated with stronger product performance.
            </div>
            <br>
            <span class="mini-pill">Product Velocity</span>
            <span class="mini-pill">Success Model</span>
            <span class="mini-pill">Success Drivers</span>
            <span class="mini-pill">Customer Insights</span>
        </div>
        """,
        unsafe_allow_html=True
    )

st.divider()

# ---------------------------------------------------
# Strategic views
# ---------------------------------------------------
st.markdown("## Strategic Views")

s1, s2 = st.columns(2)

with s1:
    st.markdown(
        """
        <div class="card">
            <div class="card-title">💰 Investor Insights</div>
            <div class="card-text">
                A decision-oriented view for investors, founders, and operators exploring
                attractive market spaces, momentum, and competitive entry opportunities.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

with s2:
    st.markdown(
        """
        <div class="card">
            <div class="card-title">🛍️ Customer Insights</div>
            <div class="card-text">
                A buyer-oriented layer focused on ratings, preferences, price-value logic,
                and the kinds of products customers seem to reward most.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

st.markdown(
    """
    <div class="cta-box">
        Use the navigation menu on the left to explore each section of the dashboard.
    </div>
    """,
    unsafe_allow_html=True
)
