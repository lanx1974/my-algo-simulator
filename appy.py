import streamlit as st
import pandas as pd
import numpy as np

# 1. Page Configuration
st.set_page_config(page_title="Power Cost Projector", layout="wide")
st.title("⚡ UK Electricity 25-Year Forward Cost Projector")
st.write("Demonstrating the real-world impact of historical compound inflation on future electricity overheads.")

# ==========================================
# 2. CUSTOMER INPUT CONTROLS (SIDEBAR)
# ==========================================
st.sidebar.header("👤 Customer Profile")

# Let the user input or slide to the customer's exact power requirements
kwh_needed = st.sidebar.number_input(
    "Customer Annual Power Needed (kWh):", 
    min_value=500, 
    max_value=100000, 
    value=2900, 
    step=100,
    help="Ofgem benchmarks: Small Flat ~1,800 kWh | Medium Home ~2,900 kWh | Large Home ~4,100 kWh"
)

st.sidebar.markdown("---")
st.sidebar.header("⚙️ Growth Parameters")

# Hardcoded defaults matching our 25-year empirical data, but adjustable if needed
base_year_price = 25.10  # 2026 price in pence per kWh
historical_cagr = 5.2    # Annualized CAGR from 2001 to 2026

cagr_input = st.sidebar.slider(
    "Projected Annual Compound Rate (%):", 
    min_value=1.0, 
    max_value=12.0, 
    value=historical_cagr, 
    step=0.1,
    help="Default is locked to the official 25-year historical UK compound rate (5.2%)"
) / 100

# ==========================================
# 3. HISTORICAL DATA EMBED
# ==========================================
hist_years = list(range(2001, 2027))
hist_prices = [
    7.00, 7.04, 7.11, 7.53, 8.34, 10.15, 10.96, 12.67, 13.24, 12.91, 
    13.84, 14.63, 15.71, 16.57, 16.52, 16.49, 17.59, 19.10, 20.48, 20.52, 
    21.87, 32.61, 34.00, 24.50, 25.80, 25.10
]

# ==========================================
# 4. FORWARD PROJECTION MATHEMATICS
# ==========================================
proj_years = list(range(2026, 2052))  # 25 years forward from 2026 base
proj_prices = []
annual_costs = []
accumulated_costs = []

running_total_spend = 0.0

for i, year in enumerate(proj_years):
    # Calculate projected unit rate based on compound interest formula
    n = year - 2026
    projected_unit_rate = base_year_price * ((1 + cagr_input) ** n)
    proj_prices.append(projected_unit_rate)
    
    # Calculate customer's annual cost in pounds: (kWh * pence) / 100
    yearly_cost_pounds = (kwh_needed * projected_unit_rate) / 100
    annual_costs.append(yearly_cost_pounds)
    
    # Track cumulative total overhead spend over the 25-year window
    running_total_spend += yearly_cost_pounds
    accumulated_costs.append(running_total_spend)

# Build cleanly structured projection DataFrame
df_projection = pd.DataFrame({
    "Year": proj_years,
    "Projected Unit Price (p/kWh)": proj_prices,
    "Annual Cost to Customer (£)": annual_costs,
    "Accumulated Cost Over Time (£)": accumulated_costs
})

# ==========================================
# 5. HIGH-IMPACT CUSTOMER SCORECARD
# ==========================================
st.subheader(f"📊 Financial Summary for a {kwh_needed:,} kWh/yr Power Requirement")
col1, col2, col3 = st.columns(3)

# Key closing metrics for presentations
col1.metric("Current 2026 Annual Cost", f"£{annual_costs[0]:,.2f}")
col2.metric("Projected 2051 Annual Cost", f"£{annual_costs[-1]:,.2f}", f"+{((proj_prices[-1]/base_year_price)-1)*100:.0f}% rate rise")
col3.metric("Total 25-Year Accumulated Cost", f"£{running_total_spend:,.2f}", "Total cash paid to grid")

st.markdown("---")

# ==========================================
# 6. GRAPHICAL PRESENTATION OVERLAYS
# ==========================================
col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    st.subheader("📈 The Annual Price Escalation Curve")
    st.write("Customer's individual projected bill per single year:")
    # Render line chart mapping the annual cost vector
    df_chart_annual = df_projection.set_index("Year")[["Annual Cost to Customer (£)"]]
    st.line_chart(df_chart_annual, color="#FF4B4B")

with col_chart2:
    st.subheader("💰 The Accumulated Wealth Drain")
    st.write("The running total of all checks written to the utility company:")
    # Render area chart to emphasize the heavy stacking nature of cumulative costs
    df_chart_accum = df_projection.set_index("Year")[["Accumulated Cost Over Time (£)"]]
    st.area_chart(df_chart_accum, color="#29B5E8")

st.markdown("---")

# ==========================================
# 7. AUDITABLE DATA MATRIX TABLE
# ==========================================
st.subheader("🔍 Year-by-Year Projected Ledger for Customers")
st.write("Full data printout showing compound trajectory step-by-step:")

# Clean display modifications for client clarity
df_display = df_projection.copy()
df_display["Projected Unit Price (p/kWh)"] = df_display["Projected Unit Price (p/kWh)"].map("{:.2f}p".format)
df_display["Annual Cost to Customer (£)"] = df_display["Annual Cost to Customer (£)"].map("£{:,.2f}".format)
df_display["Accumulated Cost Over Time (£)"] = df_display["Accumulated Cost Over Time (£)"].map("£{:,.2f}".format)

st.dataframe(df_display, use_container_width=True, hide_index=True)

# Expandable historical verification to prove credibility to savvy customers
with st.expander("📊 View Historical Verification Data (2001 - 2026) used to back this CAGR"):
    hist_df = pd.DataFrame({
        "Year": hist_years,
        "Official Avg Unit Rate": [f"{p:.2f}p" for p in hist_prices]
    })
    st.dataframe(hist_df.T, use_container_width=True)