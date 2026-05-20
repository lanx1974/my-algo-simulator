import streamlit as st
import yfinance as yf
import pandas as pd
import datetime

# 1. Config and Interface
st.set_page_config(page_title="Friction-Adjusted Algo", layout="wide")
st.title("📊 Friction-Adjusted Macro Rotation Engine")
st.write("Enforces a strict monthly rebalancing interval and applies transactional cost penalties to simulate realistic performance.")

# ==========================================
# 2. CONTROL PANEL (SIDEBAR)
# ==========================================
st.sidebar.header("🎛️ System Parameters")

asset_a = st.sidebar.text_input("Asset A (Risk-On / Growth):", "QQQ").upper()
asset_b = st.sidebar.text_input("Asset B (Risk-Off / Safety):", "TLT").upper()

momentum_lookback = st.sidebar.slider(
    "Momentum Lookback (Trading Days)", 
    min_value=10, max_value=120, value=60
)

st.sidebar.markdown("---")
st.sidebar.header("💸 Transaction Friction Cost")
# 0.20% is standard for institutional retail modeling (accounts for slippage + broker fees)
fee_pct = st.sidebar.slider("Transaction Fee per Switch (%)", min_value=0.0, max_value=1.0, value=0.20, step=0.05) / 100

# Dates
col_date1, col_date2 = st.columns(2)
with col_date1:
    start_date = st.date_input("Start Date", datetime.date(2018, 1, 1))
with col_date2:
    end_date = st.date_input("End Date", datetime.date.today())

if start_date >= end_date:
    st.error("Error: Start Date must be earlier than End Date.")
else:
    buffer_days = datetime.timedelta(days=momentum_lookback + 30)
    fetch_start = start_date - buffer_days

    @st.cache_data(ttl=3600)
    def fetch_data(ticker, start, end):
        return yf.Ticker(ticker).history(start=start, end=end)['Close']

    try:
        price_a = fetch_data(asset_a, fetch_start, end_date)
        price_b = fetch_data(asset_b, fetch_start, end_date)
        
        if price_a.empty or price_b.empty:
            st.error("Error fetching historical data. Verify tickers.")
        else:
            df = pd.DataFrame({asset_a: price_a, asset_b: price_b}).ffill().dropna()
            df.index = df.index.tz_localize(None)
            
            # Math: Structural Momentum Changes
            df[f'{asset_a}_Mom'] = df[asset_a].pct_change(periods=momentum_lookback)
            df[f'{asset_b}_Mom'] = df[asset_b].pct_change(periods=momentum_lookback)
            
            df_test = df.loc[pd.to_datetime(start_date):pd.to_datetime(end_date)].copy()
            
            if df_test.empty:
                st.error("No overlap market data found.")
            else:
                # 🔥 ARCHITECTURAL UPGRADE 1: IDENTIFY LAST TRADING DAY OF EACH MONTH
                # We group data by year-month period and extract the absolute last chronological date entry.
                month_end_dates = df_test.groupby(df_test.index.to_period('M')).apply(lambda x: x.index[-1]).values
                
                # 3. Friction-Injected Simulation Loop
                starting_cash = 10000.0
                current_value = starting_cash
                current_allocation = None 
                units_held = 0.0
                
                portfolio_history = []
                allocation_log = []
                total_trades = 0
                total_fees_paid = 0.0
                
                for idx, row in df_test.iterrows():
                    val_a = row[asset_a]
                    val_b = row[asset_b]
                    mom_a = row[f'{asset_a}_Mom']
                    mom_b = row[f'{asset_b}_Mom']
                    
                    if pd.isna(mom_a) or pd.isna(mom_b):
                        portfolio_history.append(current_value)
                        continue
                    
                    # 🔥 ARCHITECTURAL UPGRADE 2: COERCED MONTHLY REBALANCING CLOCK
                    # The system reads daily price ticks to build charts, but logic triggers ONLY on month-ends
                    if idx in month_end_dates:
                        target_allocation = asset_a if mom_a > mom_b else asset_b
                        
                        # Execute Switch if asset velocity dominance has crossed over
                        if current_allocation != target_allocation:
                            # 1. Realize capital from yesterday's asset
                            if current_allocation == asset_a:
                                current_value = units_held * val_a
                            elif current_allocation == asset_b:
                                current_value = units_held * val_b
                            
                            # 2. APPLY THE FRICTION TAX 
                            # Deduct the cost penalty before deploying capital into the next asset
                            fee_deduction = current_value * fee_pct
                            current_value -= fee_deduction
                            total_fees_paid += fee_deduction
                            total_trades += 1
                            
                            # 3. Deploy remaining capital into the new trend leader
                            current_allocation = target_allocation
                            if current_allocation == asset_a:
                                units_held = current_value / val_a
                            else:
                                units_held = current_value / val_b
                                
                            allocation_log.append(
                                f"🔄 {idx.strftime('%Y-%m-%d')} | Rotated to {current_allocation} | "
                                f"Fee Paid: ${fee_deduction:.2f} | Remaining Portfolio: ${current_value:,.2f}"
                            )
                    
                    # Compute standard running valuation daily for high-fidelity charting
                    if current_allocation is None:
                        # Before first signal is evaluated at month end, sit in raw cash
                        day_worth = current_value
                    elif current_allocation == asset_a:
                        day_worth = units_held * val_a
                    else:
                        day_worth = units_held * val_b
                        
                    portfolio_history.append(day_worth)
                    current_value = day_worth
                    
                df_test['Portfolio_Value'] = portfolio_history
                
                # 4. Performance Diagnostics
                final_portfolio_value = portfolio_history[-1]
                algo_return = ((final_portfolio_value - starting_cash) / starting_cash) * 100
                bench_a_ret = ((df_test[asset_a].iloc[-1] - df_test[asset_a].iloc[0]) / df_test[asset_a].iloc[0]) * 100
                bench_b_ret = ((df_test[asset_b].iloc[-1] - df_test[asset_b].iloc[0]) / df_test[asset_b].iloc[0]) * 100
                
                # Display Metrics Panel
                st.subheader("🏁 Friction-Adjusted Strategy Scorecard")
                col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                
                col_m1.metric("Net Strategy Value", f"${final_portfolio_value:,.2f}", f"{algo_return:+.2f}%")
                col_m2.metric(f"Hold {asset_a}", f"${starting_cash * (1 + bench_a_ret/100):,.2f}", f"{bench_a_ret:+.2f}%")
                col_m3.metric("Total Executed Trades", f"{total_trades} Rebalances")
                col_m4.metric("Total Friction Overhead", f"${total_fees_paid:,.2f}", delta="Capital Deducted", delta_color="inverse")
                
                st.markdown("---")
                st.subheader("📈 Capital Growth Curves")
                
                df_test['Growth_Strategy'] = df_test['Portfolio_Value']
                df_test[f'Growth_Hold_{asset_a}'] = (df_test[asset_a] / df_test[asset_a].iloc[0]) * starting_cash
                df_test[f'Growth_Hold_{asset_b}'] = (df_test[asset_b] / df_test[asset_b].iloc[0]) * starting_cash
                st.line_chart(df_test[['Growth_Strategy', f'Growth_Hold_{asset_a}', f'Growth_Hold_{asset_b}']])
                
                if allocation_log:
                    with st.expander("📝 System Rebalancing History & Friction Logs"):
                        for event in allocation_log:
                            st.write(event)
                            
    except Exception as error_msg:
        st.error(f"Execution Error: {error_msg}")