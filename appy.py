import streamlit as st
import pandas as pd
import numpy as np

# 1. Page Config
st.set_page_config(page_title="16-Year Catch-Up Engine", layout="wide")
st.title("🚀 The 16-Year Accelerated Retirement Matrix")
st.write("A customized wealth-compounding framework engineered for maximum efficiency between age 52 and 68.")

# ==========================================
# 2. CONTROL PANEL (SIDEBAR)
# ==========================================
st.sidebar.header("🎛️ Your Current Position")

current_age = 52
target_age = 68
years_running = target_age - current_age

initial_pot = st.sidebar.number_input("Current Retirement Pot (£)", min_value=0, value=50000, step=10000)
net_monthly_out_of_pocket = st.sidebar.slider("Net Monthly Cash You Can Invest (£)", min_value=100, max_value=5000, value=1000, step=100)

st.sidebar.markdown("---")
st.sidebar.header("⚡ Tax Arbitrage Boost")
tax_bracket = st.sidebar.selectbox(
    "Your UK Income Tax Bracket:",
    ["Basic Rate (20% Tax Relief)", "Higher Rate (40% Tax Relief)", "Additional Rate (45% Tax Relief)"]
)

st.sidebar.markdown("---")
st.sidebar.header("📈 Market Settings")
market_return = st.sidebar.slider("Expected Annual Index Return (%)", min_value=4.0, max_value=10.0, value=7.5, step=0.5) / 100
inflation_drag = st.sidebar.slider("Assumed Inflation (%)", min_value=0.0, max_value=5.0, value=2.5, step=0.1) / 100

# ==========================================
# 3. MATHEMATICAL COMPUTATIONS
# ==========================================
# Compute the instant percentage boost from tax relief
if "Basic" in tax_bracket:
    boost_factor = 1 / (1 - 0.20)  # Grosses up £80 to £100 (25% boost)
    tax_gained_pct = "25%"
elif "Higher" in tax_bracket:
    boost_factor = 1 / (1 - 0.40)  # Grosses up £60 to £100 (66.6% boost)
    tax_gained_pct = "66.6%"
else:
    boost_factor = 1 / (1 - 0.45)  # Grosses up £55 to £100 (81.8% boost)
    tax_gained_pct = "81.8%"

# Calculate the actual gross amount entering the investment pot monthly
gross_monthly_contribution = net_monthly_out_of_pocket * boost_factor

# Calculate real rate of return net of inflation
real_annual_growth = market_return - inflation_drag
real_monthly_growth = (1 + real_annual_growth) ** (1/12) - 1

# Simulation Loop for 16 years (192 months)
total_months = years_running * 12
pot_balances = []
out_of_pocket_total = []
government_contributions = []

running_pot = initial_pot
cumulative_out_of_pocket = initial_pot
cumulative_gov_boost = 0.0

for m in range(1, total_months + 1):
    # Market growth on existing pot
    growth_earnings = running_pot * real_monthly_growth
    
    # Calculate government's free addition this month
    monthly_gov_boost = gross_monthly_contribution - net_monthly_out_of_pocket
    
    # Update running totals
    running_pot += growth_earnings + gross_monthly_contribution
    cumulative_out_of_pocket += net_monthly_out_of_pocket
    cumulative_gov_boost += monthly_gov_boost
    
    # Track data points
    pot_balances.append(running_pot)
    out_of_pocket_total.append(cumulative_out_of_pocket)
    government_contributions.append(cumulative_gov_boost)

# Build Time Matrix DataFrame
timeline_years = np.arange(1, total_months + 1) / 12
df_timeline = pd.DataFrame({
    "Total Retirement Pot": pot_balances,
    "Your Cash Contributed": out_of_pocket_total,
    "Free Gov Tax Relief Boost": government_contributions
}, index=timeline_years + current_age)
df_timeline.index.name = "Your Age"

# Final values for display
final_pot_size = pot_balances[-1]
total_cash_put_in = out_of_pocket_total[-1]
total_free_gov_money = government_contributions[-1]
compound_growth_gained = final_pot_size - total_cash_put_in - total_free_gov_money

# Safe sustainable annual income using a standard conservative 3.5% withdrawal rate at age 68
annual_retirement_income = final_pot_size * 0.035

# ==========================================
# 4. DASHBOARD DISPLAY
# ==========================================
st.subheader(f"📊 The Age 68 Projection Scorecard ({years_running} Year Sprint)")
col1, col2, col3, col4 = st.columns(4)

col1.metric("Projected Pot Size at 68", f"£{final_pot_size:,.0f}", "Inflation Adjusted")
col2.metric("Instant Tax Return Boost", f"+{tax_gained_pct}", "Day-One Alpha")
col3.metric("Free Gov Money Harvested", f"£{total_free_gov_money:,.0f}")
col4.metric("Est. Sustainable Yearly Income", f"£{annual_retirement_income:,.0f}", "At 3.5% Withdrawal")

st.markdown("---")
st.subheader("📈 Runway Trajectory Profile")
st.write("See how combining your cash, the immediate government tax boost, and market index compounding builds your base:")
st.area_chart(df_timeline[["Your Cash Contributed", "Free Gov Tax Relief Boost", "Total Retirement Pot"]])

with st.expander("📝 Year-by-Year Strategic Breakdown"):
    breakdown_data = []
    for year in range(1, years_running + 1):
        m_idx = (year * 12) - 1
        age_label = current_age + year
        breakdown_data.append({
            "Your Age": int(age_label),
            "Total Pot Value": f"£{pot_balances[m_idx]:,.2f}",
            "Your Invested Capital": f"£{out_of_pocket_total[m_idx]:,.2f}",
            "Total Government Boost": f"£{government_contributions[m_idx]:,.2f}"
        })
    st.dataframe(pd.DataFrame(breakdown_data), use_container_width=True, hide_index=True)