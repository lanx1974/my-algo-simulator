import streamlit as st
import yfinance as yf
import pandas as pd
import datetime

# 1. Page Configuration
st.set_page_config(page_title="Volatility Harvester", layout="wide")
st.title("🏛️ Strategic Asset Allocation & Volatility Harvester")
st.write("This engine abandons market timing. It builds a diversified portfolio and uses quarterly rebalancing to mathematically harvest returns.")

# ==========================================
# 2. THE DIVERSIFIED PORTFOLIO CONFIGURATOR
# ==========================================
st.sidebar.header("🎛️ Asset Allocation Weights")
st.sidebar.write("Configure your permanent portfolio. Weights must add up to exactly 100%.")

# Standard Institutional "All-Weather-Lite" Asset Class Mix
w_spy = st.sidebar.slider("US Large-Cap Stocks (SPY) %", 0, 100, 50)
w_tlt = st.sidebar.slider("Long-Term US Bonds (TLT) %", 0, 100, 30)
w_gld = st.sidebar.slider("Gold Safe-Haven (GLD) %", 0, 100, 10)
w_vnq = st.sidebar.slider("Real Estate Trusts (VNQ) %", 0, 100, 10)

total_weight = w_spy + w_tlt + w_gld + w_vnq

# Map configuration into operational tracking dictionaries
allocation_dict = {"SPY": w_spy / 100, "TLT": w_tlt / 100, "GLD": w_gld / 100, "VNQ": w_vnq / 100}
tickers = list(allocation_dict.keys())

st.sidebar.markdown("---")
st.sidebar.header("💸 Transaction Costs")
fee_pct = st.sidebar.slider("Rebalancing Friction/Slippage (%)", min_value=0.0, max_value=0.5, value=0.10, step=0.05) / 100

# Testing Boundaries
col_date1, col_date2 = st.columns(2)
with col_date1:
    start_date = st.date_input("Start Date", datetime.date(2018, 1, 1))
with col_date2:
    end_date = st.date_input("End Date", datetime.date.today())

# Safety Check: Weights MUST sum to 100% to ensure mathematical validity
if total_weight != 100:
    st.sidebar.error(f"❌ Allocation Failure: Current total is {total_weight}%. Weights must add up to exactly 100%!")
elif start_date >= end_date:
    st.error("Error: Start Date must be earlier than End Date.")
else:
    # Fetch historical data for all core assets simultaneously
    @st.cache_data(ttl=3600)
    def fetch_matrix_data(symbols, start, end):
        data = yf.download(symbols, start=start, end=end)['Close']
        return data

    try:
        df_raw = fetch_matrix_data(tickers, start_date, end_date)
        
        if df_raw.empty:
            st.error("Error pulling historical asset array.")
        else:
            # Clean up timeline indices
            df = df_raw.ffill().dropna()
            df.index = df.index.tz_localize(None)
            
            # --- ARCHITECTURAL UPGRADE: THE QUARTERLY REBALANCE CLOCK ---
            # Group by year-quarter entries to find the absolute last trading day of each quarter
            quarter_end_dates = df.groupby(df.index.to_period('Q')).apply(lambda x: x.index[-1]).values
            
            # 3. Allocation Simulation Engine
            starting_capital = 10000.0
            portfolio_history = []
            rebalance_log = []
            
            # Tracker dictionaries to maintain state across the historical loop
            shares_held = {t: 0.0 for t in tickers}
            is_initialized = False
            total_fees_accumulated = 0.0
            
            for idx, row in df.iterrows():
                # On Day 1: Deploy total starting cash across assets based on target allocation percentages
                if not is_initialized:
                    for t in tickers:
                        target_cash_allocation = starting_capital * allocation_dict[t]
                        shares_held[t] = target_cash_allocation / row[t]
                    is_initialized = True
                
                # Compute current valuation of all assets combined at today's specific price points
                current_portfolio_value = sum(shares_held[t] * row[t] for t in tickers)
                
                # CHECK THE REBALANCE CLOCK: Is today the last trading day of a quarter?
                if idx in quarter_end_dates:
                    quarter_fees = 0.0
                    
                    # Calculate what the ideal asset balance SHOULD look like right now
                    ideal_allocations = {t: current_portfolio_value * allocation_dict[t] for t in tickers}
                    
                    # Execute adjustments asset by asset
                    for t in tickers:
                        actual_current_value = shares_held[t] * row[t]
                        ideal_target_value = ideal_allocations[t]
                        
                        # Calculate trade volume required to get back to target allocation
                        trade_volume = abs(ideal_target_value - actual_current_value)
                        
                        # Deduct trading friction based on trade volume size
                        trade_fee = trade_volume * fee_pct
                        quarter_fees += trade_fee
                        total_fees_accumulated += trade_fee
                        
                        # Apply the adjustment: re-calculate exact shares held
                        shares_held[t] = (ideal_target_value - trade_fee) / row[t]
                        
                    # Recalculate portfolio value after rebalancing friction is subtracted
                    current_portfolio_value = sum(shares_held[t] * row[t] for t in tickers)
                    
                    rebalance_log.append(
                        f"🔄 Rebalanced on {idx.strftime('%Y-%m-%d')} | "
                        f"Portfolio Value: ${current_portfolio_value:,.2f} | "
                        f"Friction Costs Paid: ${quarter_fees:.2f}"
                    )
                    
                portfolio_history.append(current_portfolio_value)
                
            df['Strategic_Portfolio'] = portfolio_history
            
            # 4. Performance Metrics vs. Standard Equity Benchmark (SPY)
            final_strategy_value = portfolio_history[-1]
            strategy_pct_return = ((final_strategy_value - starting_capital) / starting_capital) * 100
            
            spy_initial = df['SPY'].iloc[0]
            spy_final = df['SPY'].iloc[-1]
            spy_benchmark_return = ((spy_final - spy_initial) / spy_initial) * 100
            final_spy_value = starting_capital * (1 + (spy_benchmark_return / 100))
            
            # Max Drawdown Calculation (Measures structural risk/portfolio pain)
            def compute_max_drawdown(series):
                rolling_max = series.cummax()
                drawdowns = (series - rolling_max) / rolling_max
                return drawdowns.min() * 100
                
            strat_drawdown = compute_max_drawdown(df['Strategic_Portfolio'])
            spy_drawdown = compute_max_drawdown(df['SPY'])
            
            # 5. Render Institutional Dashboard Panel
            st.subheader("🏁 Diversified Strategy Performance Scorecard")
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            
            col_m1.metric("Diversified Portfolio Value", f"${final_strategy_value:,.2f}", f"{strategy_pct_return:+.2f}%")
            col_m2.metric("Pure US Stock Value (SPY)", f"${final_spy_value:,.2f}", f"{spy_benchmark_return:+.2f}%")
            col_m3.metric("Portfolio Max Peak-to-Trough Loss", f"{strat_drawdown:.2f}%", help="Maximum downside drop from historical peaks.")
            col_m4.metric("Pure Equity (SPY) Max Loss", f"{spy_drawdown:.2f}%", delta="Benchmark Risk Volatility", delta_color="inverse")
            
            st.markdown("---")
            st.subheader("📈 Total Capital Growth Trackers")
            
            # Normalize display values to visualize side-by-side growth trajectory clearly
            chart_df = pd.DataFrame(index=df.index)
            chart_df['Strategic Diversified Portfolio'] = df['Strategic_Portfolio']
            chart_df['Pure US Equity Index (SPY)'] = (df['SPY'] / df['SPY'].iloc[0]) * starting_capital
            st.line_chart(chart_df)
            
            # Display execution context
            col_l1, col_l2 = st.columns([2, 1])
            with col_l1:
                if rebalance_log:
                    with st.expander("📝 System Rebalancing Logs"):
                        for event in rebalance_log:
                            st.write(event)
            with col_l2:
                with st.expander("💸 Overhead Audit"):
                    st.write(f"Total Portfolio Trades Executed: {len(rebalance_log) * 4}")
                    st.write(f"Total Lifetime Rebalance Costs: ${total_fees_accumulated:.2f}")
                    
    except Exception as error_msg:
        st.error(f"Execution Error: {error_msg}")