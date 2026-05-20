import streamlit as st
import yfinance as yf
import pandas as pd
import datetime

# 1. Config and Interface
st.set_page_config(page_title="Algo Backtester", layout="centered")
st.title("⏳ Historical Backtest Engine")
st.write("Test your strategies against history to see how they perform before risking real capital.")

# 2. Interactive Inputs for your iPad
ticker = st.text_input("Stock Ticker:", "AAPL").upper()

col_date1, col_date2 = st.columns(2)
with col_date1:
    start_date = st.date_input("Start Date", datetime.date(2018, 1, 1))
with col_date2:
    end_date = st.date_input("End Date", datetime.date(2023, 1, 1))

# Safety Check: Ensure start date is before end date
if start_date >= end_date:
    st.error("Error: Start Date must be earlier than End Date.")
else:
    # 3. Secret Data Buffer Fix
    # We fetch data starting 100 days BEFORE the user's start date 
    # so the 50-day Moving Average line is already pre-calculated by Day 1.
    buffer_days = datetime.timedelta(days=100)
    fetch_start = start_date - buffer_days

    @st.cache_data(ttl=3600)
    def fetch_historical_data(symbol, start, end):
        return yf.Ticker(symbol).history(start=start, end=end)

    try:
        df = fetch_historical_data(ticker, fetch_start, end_date)
        
        if df.empty:
            st.error("No data found for this period. Try a different date or ticker.")
        else:
            # 4. Math Engine
            df['SMA_50'] = df['Close'].rolling(window=50).mean()
            
            # Slice the dataset down to the EXACT window requested by the user
            # This throws away the hidden 100-day buffer data now that math is done
            df_test = df.loc[pd.to_datetime(start_date):pd.to_datetime(end_date)].copy()
            
            if df_test.empty:
                st.error("Insufficient market days found in this specific window.")
            else:
                # 5. Core Simulation Loop
                starting_cash = 10000.0
                cash = starting_cash
                shares = 0
                holding = False
                portfolio_history = []
                
                for idx, row in df_test.iterrows():
                    price = row['Close']
                    sma = row['SMA_50']
                    
                    # Buy Logic
                    if price > sma and not holding and not pd.isna(sma):
                        shares = cash / price
                        cash = 0
                        holding = True
                    # Sell Logic
                    elif price < sma and holding:
                        cash = shares * price
                        shares = 0
                        holding = False
                        
                    # Calculate net worth at the end of the day
                    current_net_worth = (shares * price) if holding else cash
                    portfolio_history.append(current_net_worth)
                    
                df_test['Portfolio_Value'] = portfolio_history
                
                # 6. Scorecard Calculations
                final_portfolio_value = portfolio_history[-1]
                algo_pct_return = ((final_portfolio_value - starting_cash) / starting_cash) * 100
                
                initial_stock_price = df_test['Close'].iloc[0]
                final_stock_price = df_test['Close'].iloc[-1]
                bench_pct_return = ((final_stock_price - initial_stock_price) / initial_stock_price) * 100
                final_benchmark_value = starting_cash * (1 + (bench_pct_return / 100))
                
                # 7. Visual Results
                st.subheader("📊 Backtest Results Scorecard")
                metric_col1, metric_col2 = st.columns(2)
                
                metric_col1.metric(
                    label="Algorithm Final Value", 
                    value=f"${final_portfolio_value:,.2f}", 
                    delta=f"{algo_pct_return:+.2f}%"
                )
                metric_col2.metric(
                    label="Buy & Hold Benchmark", 
                    value=f"${final_benchmark_value:,.2f}", 
                    delta=f"{bench_pct_return:+.2f}%"
                )
                
                # Check for Outperformance
                alpha_score = algo_pct_return - bench_pct_return
                if alpha_score > 0:
                    st.success(f"🔥 Success! Your algorithm beat the market by {alpha_score:.2f}% during this timeframe.")
                else:
                    st.warning(f"⚠️ Market Underperformance. Your strategy lost to standard buy-and-hold by {abs(alpha_score):.2f}%.")

                st.subheader("📈 Strategy Growth Performance")
                st.line_chart(df_test['Portfolio_Value'])
                
                st.subheader("Price Movement Chart Context")
                st.line_chart(df_test[['Close', 'SMA_50']])
                
    except Exception as error_msg:
        st.error(f"System Error: {error_msg}")