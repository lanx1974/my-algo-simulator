import streamlit as st
import pandas as pd
import numpy as np

# 1. Config and Wide Interface
st.set_page_config(page_title="Wealth Runway Engine", layout="wide")
st.title("💰 Personal Wealth Runway & Compound Engine")
st.write("Stop trying to beat the market. Start optimizing the mathematical inputs of your personal net worth.")

# ==========================================
# 2. THE WEALTH CONTROL PANEL (SIDEBAR)
# ==========================================
st.sidebar.header("🎛️ Financial Inputs")

current_net_worth = st.sidebar.number_input("Current Net Worth ($)", min_value=0, value=10000, step=5000)
monthly_contribution = st.sidebar.slider("Monthly Savings/Investment ($)", min_value=0, max_value=10000, value=1000, step=100)

st.sidebar.subheader("📈 Growth & Inflation Assumptions")
# 8% to 10% is the historical long-term average for the S&P 500
expected_return = st.sidebar.slider("Expected Market Annual Return (%)", min_value=3.0, max_value=12.0, value=8.5, step=0.1) / 100
inflation_rate = st.sidebar.slider("Assumed Annual Inflation Rate (%)", min_value=0.0, max_value=6.0, value=2.5, step=0.1) / 100

st.sidebar.subheader("🏁 The Freedom Target")
desired_monthly_income = st.sidebar.number_input("Desired Monthly Income in Retirement ($)", min_value=1000, value=5000, step=500)

# ==========================================
# 3. FINANCIAL FREEDOM MATHEMATICS
# ==========================================
# Real return adjusted for inflation drag
real_annual_return = expected_return - inflation_rate
real_monthly_return = (1 + real_annual_return) ** (1/12) - 1

# The 4% Rule states you need 25x your annual expenses to live off your portfolio indefinitely
annual_expenses_target = desired_monthly_income * 12
fi_number = annual_expenses_target / 0.04

# Simulation projection loop (Max 50 years into the future to find the milestone)
months_to_simulate = 50 * 12
balances = []
total_contributions = []
total_interest_earned = []

current_balance = current_net_worth
cumulative_contributions = current_net_worth
cumulative_interest = 0.0

fi_achieved_month = None

for month in range(1, months_to_simulate + 1):
    # Calculate monthly compound interest growth
    interest_this_month = current_balance * real_monthly_return
    cumulative_interest += interest_this_month
    
    # Inject monthly savings injection
    current_balance += interest_this_month + monthly_contribution
    cumulative_contributions += monthly_contribution
    
    balances.append(current_balance)
    total_contributions.append(cumulative_contributions)
    total_interest_earned.append(cumulative_interest)
    
    # Check if the milestone number is hit
    if current_balance >= fi_number and fi_achieved_month is None:
        fi_achieved_month = month

# Build DataFrame for timelines
timeline_months = np.arange(1, months_to_simulate + 1)
df_projector = pd.DataFrame({
    "Net Worth (Inflation Adjusted)": balances,
    "Principal Contributions": total_contributions,
    "Total Compound Gains": total_interest_earned
}, index=timeline_months / 12) # Index displayed cleanly as fractional years
df_projector.index.name = "Years from Now"

# ==========================================
# 4. SCORECARD INTERFACE DISPLAY
# ==========================================
st.subheader("🏁 Your Strategic Milestones")
col_m1, col_m2, col_m3 = st.columns(3)

col_m1.metric("Target Freedom Capital (FI Number)", f"${fi_number:,.0f}", "Based on 4% Rule")
col_m2.metric("Real Growth Rate (Net of Inflation)", f"{real_annual_return * 100:.2f}%")

if fi_achieved_month:
    years_to_fi = fi_achieved_month / 12
    col_m3.metric("Time to Complete Financial Freedom", f"{years_to_fi:.1f} Years", f"Target Hit at Age +{int(years_to_fi)}")
else:
    col_m3.metric("Time to Complete Financial Freedom", "50+ Years", "Increase savings or market allocation")

st.markdown("---")
st.subheader("📈 The Compounding Curve Matrix")
st.write("Watch the intersection where **Total Compound Gains** overtakes your **Principal Contributions**. That is the inflection point where your money works harder than you do.")

# Render stream chart to emphasize the raw scaling power of compound interest
st.area_chart(df_projector[["Principal Contributions", "Total Compound Gains"]], use_container_width=True)

# Data breakdown tables for precision scannability on iPad
with st.expander("📊 View Detailed Decade-by-Decide Wealth Breakdown"):
    # Pull status slices at year 5, 10, 15, 20, 30, and 40
    intervals = [5, 10, 15, 20, 30, 40]
    breakdown_rows = []
    
    for year in intervals:
        month_idx = int(year * 12) - 1
        if month_idx < len(balances):
            breakdown_rows.append({
                "Timeline": f"Year {year}",
                "Projected Net Worth": f"${balances[month_idx]:,.2f}",
                "Your Invested Cash": f"${total_contributions[month_idx]:,.2f}",
                "Free Money Harvested (Interest)": f"${total_interest_earned[month_idx]:,.2f}"
            })
            
    st.dataframe(pd.DataFrame(breakdown_rows), use_container_width=True, hide_index=True)