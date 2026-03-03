# -*- coding: utf-8 -*-
"""
Created on Tue Mar  3 16:46:17 2026

@author: JasonRunge
"""
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="Stock Long-Term Analysis", layout="wide")
st.title("📈 Stock Long-Term Analysis Tool")

# -------------------------
# STOCK INPUT
# -------------------------
col1, col2, col3 = st.columns(3)
with col1:
    ticker_symbol = st.text_input("Ticker Symbol", "AAPL")

# -------------------------
# DOWNLOAD DATA BUTTON
# -------------------------
if st.button("Get Data"):
    ticker = yf.Ticker(ticker_symbol)
    df = ticker.history(period="max", interval="1d")

    if df.empty:
        st.error("No data found. Check ticker symbol.")
        st.stop()

    st.success(f"Downloaded {len(df)} rows")
    Data_0_Import = df.copy()

    # --- Stock Table ---
    close = Data_0_Import["Close"].copy()
    year_end_close = close.resample("YE").last()
    year_end_close.index = year_end_close.index.year
    yoy_growth = year_end_close.pct_change() * 100
    stock_table = pd.DataFrame({"Year_End_Close": year_end_close, "YoY_Growth_%": yoy_growth})

    # --- Dividend Table ---
    div = Data_0_Import["Dividends"].copy()
    div.index = pd.to_datetime(div.index)
    div = div[div != 0]
    div_yearly = div.groupby(div.index.year).sum()
    if len(div_yearly) > 1:
        div_yearly = div_yearly.iloc[1:]
    current_year = pd.Timestamp.today().year
    if len(div_yearly) > 0 and div_yearly.index[-1] == current_year:
        div_yearly = div_yearly.iloc[:-1]
    div_table = pd.DataFrame({"Total_Dividends_Per_Year": div_yearly})
    div_table["Dividend_YoY_Growth_%"] = div_table["Total_Dividends_Per_Year"].pct_change() * 100

    # Store in session_state
    st.session_state['stock_table'] = stock_table
    st.session_state['div_table'] = div_table

# -------------------------
# CHECK IF DATA EXISTS
# -------------------------
if 'stock_table' in st.session_state and 'div_table' in st.session_state:
    stock_table = st.session_state['stock_table']
    div_table = st.session_state['div_table']

    # Show stock and dividend tables
    st.subheader("📊 Stock Historical Values")
    st.dataframe(stock_table, width=800, height=300)
    st.subheader("💰 Dividend Historical Values")
    st.dataframe(div_table, width=800, height=300)

    # -------------------------
    # PORTFOLIO INPUTS
    # -------------------------
    st.subheader("💡 Portfolio Projection Inputs")
    initial_cash = st.number_input("Initial Investment Amount ($)", min_value=0.0, value=10000.0, step=1000.0, key="init_cash")
    annual_contribution = st.number_input("Annual Contribution ($)", min_value=0.0, value=5000.0, step=500.0, key="annual_contrib")
    n_years = st.number_input("Projection Horizon (Years)", min_value=1, max_value=100, value=10, step=1, key="proj_years")
    stock_growth = st.number_input("Expected Annual Stock Growth (0.05 = 5%)", value=0.07, step=0.01, format="%.4f", key="stock_growth")
    div_growth = st.number_input("Expected Annual Dividend Growth (0.03 = 3%)", value=0.03, step=0.01, format="%.4f", key="div_growth")

    if st.button("Run Portfolio Projection"):
        last_stock_price = stock_table["Year_End_Close"].iloc[-1]
        last_dividend_per_share = div_table["Total_Dividends_Per_Year"].iloc[-1] if not div_table.empty else 0

        shares_owned = []
        stock_prices = []
        dividend_per_share = []
        portfolio_values = []

        # Initial purchase
        initial_shares = initial_cash / last_stock_price
        shares_owned.append(initial_shares)
        stock_prices.append(last_stock_price)
        dividend_per_share.append(last_dividend_per_share)
        portfolio_values.append(initial_shares * last_stock_price)

        for year in range(1, int(n_years)):
            next_price = stock_prices[-1] * (1 + stock_growth)
            stock_prices.append(next_price)
            next_div_ps = dividend_per_share[-1] * (1 + div_growth)
            dividend_per_share.append(next_div_ps)
            dividend_received = shares_owned[-1] * next_div_ps
            total_new_cash = annual_contribution + dividend_received
            new_shares = total_new_cash / next_price
            total_shares = shares_owned[-1] + new_shares
            shares_owned.append(total_shares)
            portfolio_value = total_shares * next_price
            portfolio_values.append(portfolio_value)

        projection_table = pd.DataFrame({
            "Year": range(1, int(n_years)+1),
            "Stock_Price": stock_prices,
            "Shares_Owned": shares_owned,
            "Dividend_per_Share": dividend_per_share,
            "Portfolio_Value": portfolio_values
        })

        st.subheader("📈 Portfolio Projection Table")
        st.dataframe(projection_table, width=800, height=400)

        total_cash_contributed = initial_cash + annual_contribution * n_years
        estimated_portfolio_worth = projection_table["Portfolio_Value"].iloc[-1]
        total_gain = estimated_portfolio_worth - total_cash_contributed
        total_gain_pct = (estimated_portfolio_worth / total_cash_contributed - 1) * 100

        st.subheader("💰 Portfolio Summary")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Cash Contributed", f"${total_cash_contributed:,.2f}")
        col2.metric(f"Portfolio Worth after {int(n_years)} yrs", f"${estimated_portfolio_worth:,.2f}")
        col3.metric("Total Gain ($)", f"${total_gain:,.2f}")
        col4.metric("Total Gain (%)", f"{total_gain_pct:.2f}%")
else:
    st.info("Please click 'Get Data' to download stock and dividend data before running projections.")
