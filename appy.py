import streamlit as st
import yfinance as yf
import pandas as pd

# 1. App Layout and Title
st.set_page_config(page_title="Algo Simulator", layout="centered")
st.title("📈 6-Month Algo Simulation Engine")
st.write("This tool simulates investing $10,000 using a 50-day moving average strategy.")

# 2. User Input on your Phone/iPad
ticker = st.text_input("Enter a Stock Ticker (e.g., AAPL, TSLA, MSFT):", "AAPL").upper()

# 3. Fetch Stock Data from Yahoo Finance
@st.cache_data(ttl=3600)  # Caches data for 1 hour so the app runs lightning-fast
def get_stock_data(symbol):
    # Fetch 1 year of data so we can calculate a clean 50-day average
    return yf.Ticker(symbol).history(period="1y")

try:
    df = get_stock_data(ticker)
    
    if df.empty:
        st.error("No data found. Please check the stock ticker symbol.")
    else:
        # 4. Calculate the 50-Day Simple Moving Average (SMA)
        df['SMA_50'] = df['Close'].rolling(window=50).mean()
        
        # Crop data to just the last 126 trading days (exactly 6 calendar months)
        df_sim = df.iloc[-126:].copy()
        
        # 5. Run the Simulation Loop
        starting_cash = 10000.0
        cash = starting_cash
        shares = 0
        holding = False
        portfolio_values = []
        
        for index, row in df_sim.iterrows():
            price = row['Close']
            sma = row['SMA_50']
            
            # STRATEGY RULES:
            # Rule A: If price goes ABOVE the average line and we have cash -> BUY
            if price > sma and not holding:
                shares = cash / price
                cash = 0
                holding = True
            
            # Rule B: If price falls BELOW the average line and we hold shares -> SELL
            elif price < sma and holding:
                cash = shares * price
                shares = 0
                holding = False
            
            # Record what our total portfolio is worth at the end of this trading day
            day_value = (shares * price) if holding else cash
            portfolio_values.append(day_value)
            
        # Add the simulation history into our data table
        df_sim['Portfolio_Value'] = portfolio_values
        
        # 6. Calculate performance metrics
        final_val = portfolio_values[-1]
        algo_return = ((final_val - starting_cash) / starting_cash) * 100
        
        # Calculate benchmark (What if you just bought and held the stock normally?)
        bench_return = ((df_sim['Close'].iloc[-1] - df_sim['Close'].iloc[0]) / df_sim['Close'].iloc[0]) * 100
        bench_final = starting_cash * (1 + (bench_return / 100))

        # 7. Display Results visually on iPad
        st.subheader("📊 Performance vs. The Market")
        col1, col2 = st.columns(2)
        col1.metric("Your Algorithm Value", f"${final_val:,.2f}", f"{algo_return:+.2f}%")
        col2.metric("Buy & Hold Benchmark", f"${bench_final:,.2f}", f"{bench_return:+.2f}%")
        
        st.subheader("📉 Your Simulated Account Growth")
        st.line_chart(df_sim['Portfolio_Value'])
        
        st.subheader("Stock Price vs. 50-Day Moving Average Line")
        st.line_chart(df_sim[['Close', 'SMA_50']])

except Exception as e:
    st.error(f"An unexpected error occurred: {e}")