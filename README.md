# PetShop Amazon Market Analysis
by David Olivares, 2026. 

Data-driven analysis of the Amazon pet products market, focused on understanding competition, product success drivers, and growth opportunities.

This project builds a **Market Intelligence platform** that transforms raw Amazon product data into strategic insights using data analytics and interactive dashboards.

The goal is to identify:

- market structure
- competitive landscape
- high-performing products
- growth opportunities
- drivers of product success

---

# Project Overview

The pet products category is one of the fastest growing segments in e-commerce. However, entering this market requires understanding:

- which categories are saturated
- which product types perform best
- where market gaps exist
- what factors drive product success

This project analyzes thousands of Amazon listings to build a **data-driven view of the Pet Shop market**.

The platform integrates multiple analytical layers:

- Market structure analysis
- Brand competition analysis
- Category opportunity mapping
- Product velocity tracking
- Product success scoring
- Market gap identification

---

# Analytical Layers

The project generates several datasets that capture different dimensions of the market.

### Market Structure

Understanding how the market is organized.

Examples:

- distribution of product types
- price segmentation
- product mix by animal category

Datasets:

- `price_segments.csv`
- `product_type_summary.csv`
- `animal_category_summary.csv`

---

### Competitive Landscape

Analyzing how brands compete across the market.

Examples:

- brand presence across product categories
- brand diversification
- brand product portfolios

Datasets:

- `brand_summary.csv`
- `brand_product_matrix.csv`
- `brand_animal_matrix.csv`

---

### Category Competition

Measuring how crowded each category is.

Examples:

- number of competing brands
- product density
- category saturation

Datasets:

- `category_competition.csv`

---

### Market Opportunities

Identifying areas with strong demand but limited competition.

Examples:

- opportunity score by category
- whitespace analysis
- potential product expansion areas

Datasets:

- `category_opportunity.csv`
- `market_gap_analysis.csv`

---

### Product Performance

Understanding which products perform best and why.

Examples:

- top-performing products
- product velocity (review growth)
- product success scoring

Datasets:

- `top_products.csv`
- `product_velocity.csv`
- `product_success_score.csv`

---

### Success Drivers

Interpreting the factors that explain product performance.

Examples:

- feature importance analysis
- price vs rating vs review impact

Datasets:

- `product_success_feature_importance.csv`

---

# Interactive Dashboard

The project includes an interactive **Streamlit dashboard** that allows exploration of the market.

Dashboard sections include:

- Market Overview
- Market Structure
- Brand Landscape
- Category Competition
- Opportunity Map
- Market Gap Analysis
- Product Velocity
- Top Products
- Product Success Model
- Success Drivers

---

# Technologies Used

- Python
- Pandas
- NumPy
- Streamlit
- Plotly
