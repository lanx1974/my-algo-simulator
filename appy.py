import streamlit as st
import yfinance as yf
import pandas as pd
import datetime

# 1. Config and Interface
st.set_page_config(page_title="Mean Reversion Matrix", layout="wide")
st.title("🛡️ Mean Reversion Volatility Matrix")
st.write("This engine stops chasing trends. Instead, it buys extreme market panics and sells the rebounds.")

# ==========================================
# 2. CONTROL PANEL (SIDEBAR)
# ==========================================
st.sidebar.header("🎛️ Volatility Parameters")

ticker_input = st.sidebar.text_area(
    "Enter Tickers (separated by commas):", 
    "AAPL, MSFT, TSLA, NVDA, AMD, SPY, QQQ, AMZN, META, GOOGL"
)

# Bollinger Band inputs
bb_window = st.sidebar.slider("Base Moving Average (Days)", min_value=10, max_value=50, value=20)
num_std = st.sidebar.slider("Standard Deviation width (Rubber Band Stretch)", min_value=1.5, max_value=3.0, value=2.0, step=0.1)

# Dates
col_date1, col_date2 = st.columns(2)
with col_date1:
    start_date = st.date_input("Start Date", datetime.date(2021, 1, 1))
with col_date2:
    end_date = st.date_input("End Date", datetime.date.today())

tickers = [t.strip().upper() for t in ticker_input.split(",") if t.strip()]

if start_date >= end_date:
    st.error("Error: Start Date must be earlier than End Date.")
elif not tickers:
    st.warning("Please enter at least one valid stock ticker.")
else:
    buffer_days = datetime.timedelta(days=bb_window + 50)
    fetch_start = start_date - buffer_days
    matrix_results = []
    progress_bar = st.progress(0)
    
    # ==========================================
    # 3. CORE PROCESSING LOOP (COUNTER-TREND)
    # ==========================================
    for i, t in enumerate(tickers):
        progress_bar.progress((i + 1) / len(tickers))
        
        try:
            df = yf.Ticker(t).history(start=fetch_start, end=end_date)
            if df.empty:
                continue
                
            df.index = df.index.tz_localize(None)
            
            # --- BOLLINGER BAND MATHEMATICS ---
            df['Middle_Band'] = df['Close'].rolling(window=bb_window).mean()
            df['Std_Dev'] = df['Close'].rolling(window=bb_window).std()
            
            # Upper and Lower boundaries of normal asset volatility
            df['Upper_Band'] = df['Middle_Band'] + (num_std * df['Std_Dev'])
            df['Lower_Band'] = df['Middle_Band'] - (num_std * df['Std_Dev'])
            # ----------------------------------
            
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
                lower_b = row['Lower_Band']
                upper_b = row['Upper_Band']
                mid_b = row['Middle_Band']
                
                if pd.isna(lower_b) or pd.isna(upper_b):
                    portfolio_history.append(cash)
                    continue
                    
                # BUY RULE: Price drops BELOW the extreme lower boundary (Panic Buy)
                if price < lower_b and not holding:
                    shares = cash / price
                    cash = 0
                    holding = True
                    
                # SELL RULE: Price snaps back up to the historical middle average (Take Profit)
                elif price >= mid_b and holding:
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
            
            matrix_results.append({
                "Ticker": t,
                "Algorithm Return": algo_pct_return,
                "Buy & Hold Return": bench_pct_return,
                "Alpha Generated": alpha,
                "Market Status": status
            })
            
        except Exception:
            continue

    progress_bar.empty()

    # ==========================================
    # 4. DISP_REPORT
    # ==========================================
    if matrix_results:
        summary_df = pd.DataFrame(matrix_results)
        
        avg_algo = summary_df["Algorithm Return"].mean()
        avg_bench = summary_df["Buy & Hold Return"].mean()
        avg_alpha = summary_df["Alpha Generated"].mean()
        
        st.subheader("🏁 Mean Reversion Portfolio Averages")
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
        
        styled_df = summary_df.copy()
        styled_df["Algorithm Return"] = styled_df["Algorithm Return"].map("{:.2f}%".format)
        styled_df["Buy & Hold Return"] = styled_df["Buy & Hold Return"].map("{:.2f}%".format)
        styled_df["Alpha Generated"] = styled_df["Alpha Generated"].map("{:+.2f}%".format)
        
        st.dataframe(
            styled_df.sort_values(by="Alpha Generated", ascending=False), 
            use_container_width=True,
            hide_index=True
        )
    else:
        st.error("No data could be processed. Adjust parameters.")