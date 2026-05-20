import streamlit as st
import yfinance as yf
import pandas as pd
import datetime

# 1. Config and Interface
st.set_page_config(page_title="Algo Matrix", layout="wide") # 'wide' layout utilizes the full iPad screen
st.title("🖥️ Quantitative Strategy Performance Matrix")
st.write("Compare your rules across an entire watchlist simultaneously to find where the alpha hides.")

# ==========================================
# 2. CONTROL PANEL (SIDEBAR)
# ==========================================
st.sidebar.header("🎛️ Strategy Parameters")

# Let user input a comma-separated list of tickers
ticker_input = st.sidebar.text_area(
    "Enter Tickers (separated by commas):", 
    "AAPL, MSFT, TSLA, NVDA, AMD, SPY, QQQ"
)

st.sidebar.subheader("1. Trend Filter")
sma_window = st.sidebar.slider("Moving Average (Days)", min_value=20, max_value=200, value=50)

st.sidebar.subheader("2. Momentum Filter")
rsi_min = st.sidebar.slider("Minimum RSI to Buy", min_value=40, max_value=60, value=50)
rsi_max = st.sidebar.slider("Maximum RSI to Buy", min_value=65, max_value=85, value=70)

# Dates
col_date1, col_date2 = st.columns(2)
with col_date1:
    start_date = st.date_input("Start Date", datetime.date(2020, 1, 1))
with col_date2:
    end_date = st.date_input("End Date", datetime.date.today())

# Process the input string into a clean Python list
tickers = [t.strip().upper() for t in ticker_input.split(",") if t.strip()]

if start_date >= end_date:
    st.error("Error: Start Date must be earlier than End Date.")
elif not tickers:
    st.warning("Please enter at least one valid stock ticker.")
else:
    # Buffer calculation for indicators
    buffer_days = datetime.timedelta(days=sma_window + 50)
    fetch_start = start_date - buffer_days

    # Container to hold final metrics for the summary table
    matrix_results = []

    # Progress bar for visual feedback on iPad
    progress_bar = st.progress(0)
    
    # ==========================================
    # 3. CORE PROCESSING LOOP (THE SCANNER)
    # ==========================================
    for i, t in enumerate(tickers):
        # Update progress bar dynamically
        progress_bar.progress((i + 1) / len(tickers))
        
        try:
            # Fetch data for single ticker
            df = yf.Ticker(t).history(start=fetch_start, end=end_date)
            
            if df.empty:
                continue # Skip if no data found
                
            df.index = df.index.tz_localize(None)
            
            # Math: RSI
            change = df['Close'].diff()
            gain = change.mask(change < 0, 0.0)
            loss = change.mask(change > 0, 0.0).abs()
            avg_gain = gain.ewm(com=13, adjust=False).mean()
            avg_loss = loss.ewm(com=13, adjust=False).mean()
            avg_loss = avg_loss.replace(0, 0.00001)
            rs = avg_gain / avg_loss
            df['RSI'] = 100 - (100 / (1 + rs))
            
            # Math: SMA
            df['SMA'] = df['Close'].rolling(window=sma_window).mean()
            
            # Slice to window
            df_test = df.loc[pd.to_datetime(start_date):pd.to_datetime(end_date)].copy()
            
            if df_test.empty or len(df_test) < 2:
                continue
                
            # Simulation Loop
            starting_cash = 10000.0
            cash = starting_cash
            shares = 0
            holding = False
            portfolio_history = []
            
            for idx, row in df_test.iterrows():
                price = row['Close']
                sma = row['SMA']
                rsi = row['RSI']
                
                if pd.isna(sma) or pd.isna(rsi):
                    portfolio_history.append(cash)
                    continue
                    
                if price > sma and (rsi >= rsi_min) and (rsi <= rsi_max) and not holding:
                    shares = cash / price
                    cash = 0
                    holding = True
                elif (price < sma or rsi < 45) and holding:
                    cash = shares * price
                    shares = 0
                    holding = False
                    
                current_net_worth = (shares * price) if holding else cash
                portfolio_history.append(current_net_worth)
                
            final_portfolio_value = portfolio_history[-1]
            algo_pct_return = ((final_portfolio_value - starting_cash) / starting_cash) * 100
            
            initial_stock_price = df_test['Close'].iloc[0]
            final_stock_price = df_test['Close'].iloc[-1]
            bench_pct_return = ((final_stock_price - initial_stock_price) / initial_stock_price) * 100
            
            alpha = algo_pct_return - bench_pct_return
            status = "🟢 BEAT" if alpha > 0 else "🔴 LOST"
            
            # Append rows into a master database list
            matrix_results.append({
                "Ticker": t,
                "Algorithm Return": algo_pct_return,
                "Buy & Hold Return": bench_pct_return,
                "Alpha Generated": alpha,
                "Market Status": status
            })
            
        except Exception as e:
            # If an asset fails (like a typo), ignore it and move to next asset
            continue

    # Clean up progress bar when done
    progress_bar.empty()

    # ==========================================
    # 4. REPORTING LOGIC & AVERAGES
    # ==========================================
    if matrix_results:
        summary_df = pd.DataFrame(matrix_results)
        
        # Calculate cross-watchlist macro averages
        avg_algo = summary_df["Algorithm Return"].mean()
        avg_bench = summary_df["Buy & Hold Return"].mean()
        avg_alpha = summary_df["Alpha Generated"].mean()
        
        # Display Overview Row
        st.subheader("🏁 Global Watchlist Averages")
        m_col1, m_col2, m_col3 = st.columns(3)
        
        m_col1.metric("Average Algo Return", f"{avg_algo:.2f}%")
        m_col2.metric("Average Buy & Hold", f"{avg_bench:.2f}%")
        m_col3.metric(
            "Average Net Alpha", 
            f"{avg_alpha:+.2f}%", 
            delta=f"{avg_alpha:.2f}% Net Edge",
            delta_color="normal" if avg_alpha > 0 else "inverse"
        )
        
        st.markdown("---")
        st.subheader("📊 Individual Asset Breakdown")
        
        # Format columns for scannability
        styled_df = summary_df.copy()
        styled_df["Algorithm Return"] = styled_df["Algorithm Return"].map("{:.2f}%".format)
        styled_df["Buy & Hold Return"] = styled_df["Buy & Hold Return"].map("{:.2f}%".format)
        styled_df["Alpha Generated"] = styled_df["Alpha Generated"].map("{:+.2f}%".format)
        
        # Render interactive table on iPad
        st.dataframe(
            styled_df.sort_values(by="Alpha Generated", ascending=False), 
            use_container_width=True,
            hide_index=True
        )
        
    else:
        st.error("Could not compute matrix data. Ensure symbols are valid or adjust your date range parameters.")