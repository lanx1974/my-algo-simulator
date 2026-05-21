import streamlit as st
import pandas as pd
import numpy as np

# 1. Page Configuration
st.set_page_config(page_title="UK Electricity Auditor", layout="wide")
st.title("⚡ UK Household Electricity Profiler & Cost Auditor")
st.write("A dedicated analytical engine designed to isolate, profile, and audit domestic electricity consumption against official Ofgem price cap limits.")

# ==========================================
# 2. HOUSEHOLD CONFIGURATION PANEL
# ==========================================
st.sidebar.header("🏡 Property Profile")

property_profile = st.sidebar.selectbox(
    "Select Your Property Size:",
    [
        "Small Flat / 1-Bed Mid-Terrace (Low Usage)",
        "Medium House / 3-Bed Semi-Detached (Average Usage)",
        "Large House / 4+ Bed Detached (High Usage)",
        "Custom Energy User (Manual Entry)"
    ]
)

# Map Ofgem Typical Domestic Consumption Values (TDCVs) for electricity
if "Small Flat" in property_profile:
    default_elec_kwh = 1800
    st.sidebar.info("📊 Benchmark applied: 1,800 kWh / year (Ofgem Low)")
elif "Medium" in property_profile:
    default_elec_kwh = 2900
    st.sidebar.info("📊 Benchmark applied: 2,900 kWh / year (Ofgem Medium)")
elif "Large" in property_profile:
    default_elec_kwh = 4100
    st.sidebar.info("📊 Benchmark applied: 4,100 kWh / year (Ofgem High)")
else:
    default_elec_kwh = 3000

# Interactive slider for fine-tuning exact usage
annual_elec_kwh = st.sidebar.slider("Annual Consumption (kWh)", min_value=500, max_value=15000, value=default_elec_kwh, step=100)

st.sidebar.markdown("---")
st.sidebar.header("💳 Payment Method")
payment_method = st.sidebar.radio(
    "Select Billing Method:",
    ["Monthly Direct Debit", "Prepayment Meter", "Standard Credit (Pay on Bill Receipt)"]
)

# ==========================================
# 3. OFFICIAL 2026 PRICE CAP ENGINE
# ==========================================
# Rates set by Ofgem for Q2 2026 national averages
if payment_method == "Monthly Direct Debit":
    elec_unit_rate = 0.2467       # 24.67p per kWh
    elec_standing_charge = 0.5721 # 57.21p per day
elif payment_method == "Prepayment Meter":
    elec_unit_rate = 0.2380       # 23.80p per kWh
    elec_standing_charge = 0.5600 # 56.00p per day
else: # Standard Credit
    elec_unit_rate = 0.2650       # 26.50p per kWh
    elec_standing_charge = 0.6200 # 62.00p per day

# Mathematical Calculations
days_in_year = 365.25

# Cost Computations
annual_usage_cost = annual_elec_kwh * elec_unit_rate
annual_standing_cost = elec_standing_charge * days_in_year
total_annual_bill = annual_usage_cost + annual_standing_cost

total_monthly_average = total_annual_bill / 12
total_daily_average = total_annual_bill / days_in_year

# ==========================================
# 4. INTERFACE DISPLAY & DATA VISUALS
# ==========================================
st.subheader(f"📊 Electricity Outlay Metrics ({payment_method})")
col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Annual Bill", f"£{total_annual_bill:,.2f}")
col2.metric("Average Monthly Cost", f"£{total_monthly_average:,.2f}")
col3.metric("Average Daily Cost", f"£{total_daily_average:,.2f}")
col4.metric("Annual Standing Charge", f"£{annual_standing_cost:,.2f}", f"{elec_standing_charge*100:.2f}p / day")

st.markdown("---")

col_left, col_right = st.columns([3, 2])

with col_left:
    st.subheader("📋 Structural Cost Composition")
    
    # Structural breakdown of where the money goes
    cost_breakdown_df = pd.DataFrame({
        "Cost Component": ["Active Electricity Consumption", "Fixed Standing Charge Infrastructure"],
        "Annual Cost (£)": [annual_usage_cost, annual_standing_cost]
    })
    
    st.bar_chart(data=cost_breakdown_df, x="Cost Component", y="Annual Cost (£)", use_container_width=True)

with col_right:
    st.subheader("🔍 Annual Cost Audit Itemization")
    
    audit_table = [
        {"Cost Center": "Unit Usage (Variable)", "Rate/Basis": f"{elec_unit_rate*100:.2f}p per kWh", "Annual Total": f"£{annual_usage_cost:,.2f}"},
        {"Cost Center": "Standing Charge (Fixed)", "Rate/Basis": f"{elec_standing_charge*100:.2f}p per Day", "Annual Total": f"£{annual_standing_cost:,.2f}"},
        {"Cost Center": "Grand Total Bill Summary", "Rate/Basis": f"{annual_elec_kwh:,} kWh/yr Total", "Annual Total": f"£{total_annual_bill:,.2f}"}
    ]
    st.dataframe(pd.DataFrame(audit_table), use_container_width=True, hide_index=True)

# ==========================================
# 5. EFFICIENCY & APPLIANCE MITIGATION
# ==========================================
st.markdown("---")
st.subheader("💡 Strategic Efficiency & Optimization Simulator")
st.write("Simulate the exact financial impact of lowering your electricity consumption through LED conversions, energy-efficient appliances, or solar additions.")

efficiency_saving_pct = st.slider("Simulated Electricity Consumption Reduction (%)", min_value=0, max_value=50, value=20, step=5)

new_usage_cost = annual_usage_cost * (1 - (efficiency_saving_pct / 100))
new_grand_total = new_usage_cost + annual_standing_cost
guaranteed_annual_savings = total_annual_bill - new_grand_total

col_sav1, col_sav2, col_sav3 = st.columns(3)
col_sav1.metric("Optimized Annual Total", f"£{new_grand_total:,.2f}")
col_sav2.metric("Annual Cash Kept", f"£{guaranteed_annual_savings:,.2f}", delta="Reduced Outgoings", delta_color="inverse")
col_sav3.metric("Optimized Monthly Average", f"£{new_grand_total/12:,.2f}")