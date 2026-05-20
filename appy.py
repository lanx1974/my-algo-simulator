import streamlit as st
import yfinance as yf
import pandas as pd
import datetime

# 1. Config and Interface
st.set_page_config(page_title="Macro Rotation Engine", layout="wide")
st.title("⚖️ Institutional Asset Class Rotation Engine")
st.write("This strategy rotates 100% of capital into whichever major asset class exhibits the strongest structural velocity.")

# ==========================================
# 2. CONTROL PANEL (SIDEBAR)
# ==========================================
st.sidebar.header("🎛️ Rotation Settings")

# Asset inputs default to the classic Stock vs Bond/Gold battle
asset_a = st.sidebar.text_input("Asset A (Risk-On / Growth):", "QQQ").upper()
asset_b = st.sidebar.text_input("Asset B (Risk-Off / Safety):", "TLT").upper()

# Momentum lookback window
momentum_lookback = st.sidebar.slider(
    "Momentum Measurement Window (Trading Days)", 
    min_value=10, 
    max_value=120, 
    value=60,
    help="How many days into the past the brain looks to determine which asset is currently stronger."
)

# Dates
col_date1, col_date2 = st.columns(2)
with col_date1:
    start_date = st.date_input("Start Date", datetime.date(2018, 1, 1))
with col_date2:
    end_date = st.date_input("End Date", datetime.date.today())

if start_date >= end_date:
    st.error("Error: Start Date must be earlier than End Date.")
else:
    # Buffer calculation to compute historical momentum from Day 1
    buffer_days = datetime.timedelta(days=momentum_lookback + 30)
    fetch_start = start_date - buffer_days

    @st.cache_data(ttl=3600)
    def fetch_data(ticker, start, end):
        return yf.Ticker(ticker).history(start=start, end=end)['Close']

    try:
        # Fetch both historical close datasets simultaneously
        price_a = fetch_data(asset_a, fetch_start, end_date)
        price_b = fetch_data(asset_b, fetch_start, end_date)
        
        if price_a.empty or price_b.empty:
            st.error("Error fetching data for one or both assets. Please check your symbols.")
        else:
            # Combine data into a single master index table
            df = pd.DataFrame({asset_a: price_a, asset_b: price_b}).ffill().dropna()
            df.index = df.index.tz_localize(None)
            
            # --- STRUCTURED MOMENTUM MATHEMATICS ---
            # Calculate the percentage change over the designated lookback window
            df[f'{asset_a}_Mom'] = df[asset_a].pct_change(periods=momentum_lookback)
            df[f'{asset_b}_Mom'] = df[asset_b].pct_change(periods=momentum_lookback)
            # ----------------------------------------
            
            # Slice down to your specific testing window
            df_test = df.loc[pd.to_datetime(start_date):pd.to_datetime(end_date)].copy()
            
            if df_test.empty:
                st.error("No overlap market data found in your designated window.")
            else:
                # 3. Macro Simulation Loop
                starting_cash = 10000.0
                current_value = starting_cash
                
                # Allocation: 0 means Cash/Safety Asset, 1 means Growth Asset
                current_allocation = None 
                units_held = 0.0
                
                portfolio_history = []
                allocation_log = []
                
                for idx, row in df_test.iterrows():
                    val_a = row[asset_a]
                    val_b = row[asset_b]
                    mom_a = row[f'{asset_a}_Mom']
                    mom_b = row[f'{asset_b}_Mom']
                    
                    # Wait for indicators to compute fully
                    if pd.isna(mom_a) or pd.isna(mom_b):
                        portfolio_history.append(current_value)
                        continue
                    
                    # SYSTEMATIC CHOICE: Which asset has the higher velocity?
                    target_allocation = asset_a if mom_a > mom_b else asset_b
                    
                    # IF OUR ALLOCATION HAS TO CHANGE (REBALANCE)
                    if current_allocation != target_allocation:
                        # Liquidate whatever we were holding yesterday into raw cash value
                        if current_allocation == asset_a:
                            current_value = units_held * val_a
                        elif current_allocation == asset_b:
                            current_value = units_held * val_b
                            
                        # Immediately deploy that cash into the winning asset
                        current_allocation = target_allocation
                        if current_allocation == asset_a:
                            units_held = current_value / val_a
                        else:
                            units_held = current_value / val_b
                            
                        allocation_log.append(f"🔄 ROTATION ON {idx.strftime('%Y-%m-%d')}: Moved 100% to {current_allocation} (Velocity A: {mom_a*100:.1f}%, B: {mom_b*100:.1f}%)")
                    
                    # Track running net worth at the end of each trading day
                    if current_allocation == asset_a:
                        day_worth = units_held * val_a
                    else:
                        day_worth = units_held * val_b
                        
                    portfolio_history.append(day_worth)
                    current_value = day_worth
                    
                df_test['Portfolio_Value'] = portfolio_history
                
                # 4. Global Scorecards vs Benchmarks
                final_portfolio_value = portfolio_history[-1]
                algo_return = ((final_portfolio_value - starting_cash) / starting_cash) * 100
                
                # Benchmark 1: What if you just bought and held Asset A the whole time?
                bench_a_ret = ((df_test[asset_a].iloc[-1] - df_test[asset_a].iloc[0]) / df_test[asset_a].iloc[0]) * 100
                # Benchmark 2: What if you just bought and held Asset B the whole time?
                bench_b_ret = ((df_test[asset_b].iloc[-1] - df_test[asset_b].iloc[0]) / df_test[asset_b].iloc[0]) * 100
                
                st.subheader("📊 Macro Allocation Results")
                col_m1, col_m2, col_m3 = st.columns(3)
                
                col_m1.metric("Rotation Strategy Value", f"${final_portfolio_value:,.2f}", f"{algo_return:+.2f}%")
                col_m2.metric(f"Pure Buy & Hold ({asset_a})", f"${starting_cash * (1 + bench_a_ret/100):,.2f}", f"{bench_a_ret:+.2f}%")
                col_m3.metric(f"Pure Buy & Hold ({asset_b})", f"${starting_cash * (1 + bench_b_ret/100):,.2f}", f"{bench_b_ret:+.2f}%")
                
                # Highlight Strategy Performance Context
                better_than_a = algo_return > bench_a_ret
                better_than_b = algo_return > bench_b_ret
                
                if better_than_a and better_than_b:
                    st.success("🔥 Complete Alpha: The rotation strategy successfully beat both standalone assets.")
                elif better_than_a or better_than_b:
                    st.warning("⚠️ Partial Alpha: The strategy beat one asset class but underperformed the other.")
                else:
                    st.error("❌ Drag Underperformance: The switching frequency caused structural performance drag.")

                st.subheader("📈 Capital Trajectory Comparison")
                # Normalize growth benchmarks for clear side-by-side visualization
                df_test['Growth_Strategy'] = df_test['Portfolio_Value']
                df_test[f'Growth_Hold_{asset_a}'] = (df_test[asset_a] / df_test[asset_a].iloc[0]) * starting_cash
                df_test[f'Growth_Hold_{asset_b}'] = (df_test[asset_b] / df_test[asset_b].iloc[0]) * starting_cash
                st.line_chart(df_test[['Growth_Strategy', f'Growth_Hold_{asset_a}', f'Growth_Hold_{asset_b}']])
                
                if allocation_log:
                    with st.expander("📝 System Rebalancing History Log"):
                        for event in allocation_log:
                            st.write(event)
                            
    except Exception as error_msg:
        st.error(f"Execution Error: {error_msg}")