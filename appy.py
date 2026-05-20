import streamlit as st
import yfinance as yf
import pandas as pd
import datetime

# 1. Config and Interface
st.set_page_config(page_title="Momentum Algo", layout="centered")
st.title("🚀 Trend + Momentum Engine (RSI Filter)")
st.write("This engine uses an RSI Speedometer to prevent buying into exhausted overbought peaks.")

# ==========================================
# 2. CONTROL PANEL
# ==========================================
st.sidebar.header("🎛️ Strategy Parameters")
ticker = st.sidebar.text_input("Stock Ticker:", "AAPL").upper()

st.sidebar.subheader("1. Trend Filter (GPS)")
sma_window = st.sidebar.slider("Moving Average (Days)", min_value=20, max_value=200, value=50)

st.sidebar.subheader("2. Momentum Filter (Speedometer)")
rsi_min = st.sidebar.slider("Minimum RSI to Buy (Strength)", min_value=40, max_value=60, value=50)
rsi_max = st.sidebar.slider("Maximum RSI to Buy (Overbought Cap)", min_value=65, max_value=85, value=70)

# Dates
col_date1, col_date2 = st.columns(2)
with col_date1:
    start_date = st.date_input("Start Date", datetime.date(2020, 1, 1))
with col_date2:
    end_date = st.date_input("End Date", datetime.date.today())

if start_date >= end_date:
    st.error("Error: Start Date must be earlier than End Date.")
else:
    # Buffer calculation (Need extra days to calculate a clean 14-day RSI and SMA)
    buffer_days = datetime.timedelta(days=sma_window + 50)
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
            
            # --- MATHEMATICAL RSI CALCULATOR ---
            change = df['Close'].diff()
            gain = change.mask(change < 0, 0.0)
            loss = change.mask(change > 0, 0.0).abs()
            
            # Standard Exponential Moving Average for RSI
            avg_gain = gain.ewm(com=13, adjust=False).mean()
            avg_loss = loss.ewm(com=13, adjust=False).mean()
            
            # Avoid division by zero
            avg_loss = avg_loss.replace(0, 0.00001)
            
            rs = avg_gain / avg_loss
            df['RSI'] = 100 - (100 / (1 + rs))
            # -----------------------------------
            
            # Calculate Moving Average
            df['SMA'] = df['Close'].rolling(window=sma_window).mean()
            
            # Slice down to user's precise testing window
            df_test = df.loc[pd.to_datetime(start_date):pd.to_datetime(end_date)].copy()
            
            if df_test.empty:
                st.error("Insufficient market days found in this specific window.")
            else:
                # 3. Simulation Loop with Momentum Filtering
                starting_cash = 10000.0
                cash = starting_cash
                shares = 0
                holding = False
                portfolio_history = []
                trade_log = []
                
                for idx, row in df_test.iterrows():
                    price = row['Close']
                    sma = row['SMA']
                    rsi = row['RSI']
                    
                    if pd.isna(sma) or pd.isna(rsi):
                        portfolio_history.append(cash)
                        continue
                        
                    # UPGRADED BUY RULE: GPS says UP trend AND Speedometer is strong but not crashed
                    if price > sma and (rsi >= rsi_min) and (rsi <= rsi_max) and not holding:
                        shares = cash / price
                        cash = 0
                        holding = True
                        trade_log.append(f"🟢 BUY: Entered at ${price:.2f} (RSI was healthy at {rsi:.1f})")
                        
                    # SELL RULE: Price drops below Trend line OR momentum completely dies
                    elif (price < sma or rsi < 45) and holding:
                        cash = shares * price
                        shares = 0
                        holding = False
                        trade_log.append(f"🔴 SELL: Exited at ${price:.2f} (RSI: {rsi:.1f})")
                        
                    current_net_worth = (shares * price) if holding else cash
                    portfolio_history.append(current_net_worth)
                    
                df_test['Portfolio_Value'] = portfolio_history
                
                # 4. Results calculations
                final_portfolio_value = portfolio_history[-1]
                algo_pct_return = ((final_portfolio_value - starting_cash) / starting_cash) * 100
                
                initial_stock_price = df_test['Close'].iloc[0]
                final_stock_price = df_test['Close'].iloc[-1]
                bench_pct_return = ((final_stock_price - initial_stock_price) / initial_stock_price) * 100
                final_benchmark_value = starting_cash * (1 + (bench_pct_return / 100))
                
                # 5. Display Dashboard
                st.subheader("📊 Performance Scorecard")
                metric_col1, metric_col2 = st.columns(2)
                
                metric_col1.metric("Momentum Algo Value", f"${final_portfolio_value:,.2f}", f"{algo_pct_return:+.2f}%")
                metric_col2.metric("Standard Buy & Hold", f"${final_benchmark_value:,.2f}", f"{bench_pct_return:+.2f}%")
                
                alpha_score = algo_pct_return - bench_pct_return
                if alpha_score > 0:
                    st.success(f"🔥 Success! This momentum filter beat buy-and-hold by {alpha_score:.2f}%.")
                else:
                    st.warning(f"⚠️ Underperforming by {abs(alpha_score):.2f}%. Try adjusting the RSI boundaries on the left.")

                st.subheader("📈 Capital Growth Chart")
                st.line_chart(df_test['Portfolio_Value'])
                
                # Visualizing the Speedometer
                st.subheader("🧭 The RSI Speedometer Chart")
                df_test['Overbought_Line'] = rsi_max
                df_test['Momentum_Floor'] = rsi_min
                st.line_chart(df_test[['RSI', 'Overbought_Line', 'Momentum_Floor']])
                
                if trade_log:
                    with st.expander("📝 View Tactical Execution Log"):
                        for log in trade_log:
                            st.write(log)
                            
    except Exception as error_msg:
        st.error(f"System Error: {error_msg}")