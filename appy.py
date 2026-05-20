import streamlit as st
import yfinance as yf
import pandas as pd
import datetime

# 1. Config and Interface
st.set_page_config(page_title="Algo Builder", layout="centered")
st.title("🛠️ Custom Algo Strategy Builder")
st.write("Adjust the parameters below to build, edit, and test your custom trading rules instantly.")

# ==========================================
# 2. THE ALGORITHM CONTROL PANEL (UI EDITING)
# ==========================================
st.sidebar.header("🎛️ Edit Your Algorithm Rules")

ticker = st.sidebar.text_input("Stock Ticker:", "AAPL").upper()

# Sliders that let you dynamically change the logic of your algorithm
fast_sma_window = st.sidebar.slider("Fast Moving Average (Days)", min_value=5, max_value=50, value=10)
slow_sma_window = st.sidebar.slider("Slow Moving Average (Days)", min_value=20, max_value=200, value=50)

st.sidebar.markdown("---")
st.sidebar.header("🛡️ Risk Management Rules")
use_stop_loss = st.sidebar.checkbox("Enable Stop Loss", value=True)
stop_loss_pct = st.sidebar.slider("Stop Loss Trigger (%)", min_value=1, max_value=20, value=5) / 100

# Date inputs
col_date1, col_date2 = st.columns(2)
with col_date1:
    start_date = st.date_input("Start Date", datetime.date(2020, 1, 1))
with col_date2:
    end_date = st.date_input("End Date", datetime.date(2024, 1, 1))

# Safety Check
if start_date >= end_date:
    st.error("Error: Start Date must be earlier than End Date.")
elif fast_sma_window >= slow_sma_window:
    st.sidebar.error("❌ The 'Fast' average must be smaller than the 'Slow' average!")
else:
    # Fetch data with an extra buffer to handle the largest possible moving average window
    buffer_days = datetime.timedelta(days=slow_sma_window + 50)
    fetch_start = start_date - buffer_days

    @st.cache_data(ttl=3600)
    def fetch_historical_data(symbol, start, end):
        return yf.Ticker(symbol).history(start=start, end=end)

    try:
        df = fetch_historical_data(ticker, fetch_start, end_date)
        
        if df.empty:
            st.error("No data found for this period. Try a different date or ticker.")
        else:
            df.index = df.index.tz_localize(None)
            
            # 3. Dynamic Math Engine (Reads directly from your iPad sliders!)
            df['Fast_SMA'] = df['Close'].rolling(window=fast_sma_window).mean()
            df['Slow_SMA'] = df['Close'].rolling(window=slow_sma_window).mean()
            
            # Slice the dataset down to your requested test window
            df_test = df.loc[pd.to_datetime(start_date):pd.to_datetime(end_date)].copy()
            
            if df_test.empty:
                st.error("Insufficient market days found in this specific window.")
            else:
                # 4. Upgraded Simulation Loop
                starting_cash = 10000.0
                cash = starting_cash
                shares = 0
                holding = False
                buy_price = 0.0
                portfolio_history = []
                trade_log = []
                
                for idx, row in df_test.iterrows():
                    price = row['Close']
                    fast_sma = row['Fast_SMA']
                    slow_sma = row['Slow_SMA']
                    
                    # Skip rows where indicators aren't ready yet
                    if pd.isna(fast_sma) or pd.isna(slow_sma):
                        portfolio_history.append(cash)
                        continue
                    
                    # EMERGENCY STOP LOSS CHECK
                    if holding and use_stop_loss and (price <= buy_price * (1 - stop_loss_pct)):
                        cash = shares * price
                        shares = 0
                        holding = False
                        trade_log.append(f"🚨 STOP LOSS TRIGGERED: Sold at ${price:.2f}")
                    
                    # ALGO BUY RULE: Fast line crosses ABOVE Slow line (Bullish Momentum)
                    elif price > fast_sma and fast_sma > slow_sma and not holding:
                        shares = cash / price
                        cash = 0
                        holding = True
                        buy_price = price
                        trade_log.append(f"🟢 ALGO BUY SIGNAL: Bought at ${price:.2f}")
                        
                    # ALGO SELL RULE: Fast line crosses BELOW Slow line (Bearish Momentum)
                    elif fast_sma < slow_sma and holding:
                        cash = shares * price
                        shares = 0
                        holding = False
                        trade_log.append(f"🔴 ALGO SELL SIGNAL: Sold at ${price:.2f}")
                        
                    # End of day calculation
                    current_net_worth = (shares * price) if holding else cash
                    portfolio_history.append(current_net_worth)
                    
                df_test['Portfolio_Value'] = portfolio_history
                
                # 5. Scorecard Calculations
                final_portfolio_value = portfolio_history[-1]
                algo_pct_return = ((final_portfolio_value - starting_cash) / starting_cash) * 100
                
                initial_stock_price = df_test['Close'].iloc[0]
                final_stock_price = df_test['Close'].iloc[-1]
                bench_pct_return = ((final_stock_price - initial_stock_price) / initial_stock_price) * 100
                final_benchmark_value = starting_cash * (1 + (bench_pct_return / 100))
                
                # 6. Display Interactive Dashboard
                st.subheader("📊 Performance Scorecard")
                metric_col1, metric_col2 = st.columns(2)
                
                metric_col1.metric("Your Custom Algo Value", f"${final_portfolio_value:,.2f}", f"{algo_pct_return:+.2f}%")
                metric_col2.metric("Standard Buy & Hold", f"${final_benchmark_value:,.2f}", f"{bench_pct_return:+.2f}%")
                
                alpha_score = algo_pct_return - bench_pct_return
                if alpha_score > 0:
                    st.success(f"🔥 Success! Your custom settings beat the market by {alpha_score:.2f}%.")
                else:
                    st.warning(f"⚠️ Market Underperformance. Your rules lost to standard buy-and-hold by {abs(alpha_score):.2f}%.")

                st.subheader("📈 Custom Strategy Performance Curve")
                st.line_chart(df_test['Portfolio_Value'])
                
                st.subheader("Visualized Rule Context (Stock vs. Your Two Custom Lines)")
                st.line_chart(df_test[['Close', 'Fast_SMA', 'Slow_SMA']])
                
                # 7. Transparency: Show what the brain did
                if trade_log:
                    with st.expander("📝 View Strategy Execution Log"):
                        for log in trade_log:
                            st.write(log)
                            
    except Exception as error_msg:
        st.error(f"System Error: {error_msg}")