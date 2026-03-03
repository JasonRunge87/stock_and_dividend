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
from io import BytesIO

st.set_page_config(page_title="Stock Long-Term Analysis", layout="wide")

st.title("📈 Stock Long-Term Analysis Tool")

# ==========================
# USER INPUTS
# ==========================

col1, col2, col3 = st.columns(3)

with col1:
    ticker_symbol = st.text_input("Ticker Symbol", "AAPL")

with col2:
    stock_growth = st.slider(
        "Expected Annual Stock Growth",
        min_value=0.0,
        max_value=0.20,
        value=0.05,
        step=0.005
    )

with col3:
    div_growth = st.slider(
        "Expected Annual Dividend Growth",
        min_value=0.0,
        max_value=0.20,
        value=0.03,
        step=0.005
    )

projection_years = st.slider("Projection Years", 5, 40, 20)

# ==========================
# DOWNLOAD DATA
# ==========================

if st.button("Run Analysis"):

    ticker = yf.Ticker(ticker_symbol)
    df = ticker.history(period="max", interval="1d")

    if df.empty:
        st.error("No data found. Check ticker symbol.")
        st.stop()

    st.success(f"Downloaded {len(df)} rows")

    # ==========================
    # HISTORICAL PLOT
    # ==========================

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df["Close"],
        mode="lines",
        name="Close Price"
    ))

    fig.update_layout(
        title=f"{ticker_symbol} Historical Price",
        xaxis_title="Date",
        yaxis_title="Price",
        template="plotly_white"
    )

    st.plotly_chart(fig, use_container_width=True)

    # ==========================
    # PROJECTION MODEL
    # ==========================

    last_price = df["Close"].iloc[-1]
    current_div = ticker.info.get("dividendRate", 0)

    years = np.arange(1, projection_years + 1)

    projected_prices = last_price * (1 + stock_growth) ** years
    projected_divs = current_div * (1 + div_growth) ** years

    projection_df = pd.DataFrame({
        "Year": years,
        "Projected Price": projected_prices,
        "Projected Dividend": projected_divs
    })

    st.subheader("Projection Table")
    st.dataframe(projection_df)

    # ==========================
    # PROJECTION PLOT
    # ==========================

    fig2 = go.Figure()

    fig2.add_trace(go.Scatter(
        x=projection_df["Year"],
        y=projection_df["Projected Price"],
        mode="lines",
        name="Projected Price"
    ))

    fig2.add_trace(go.Scatter(
        x=projection_df["Year"],
        y=projection_df["Projected Dividend"],
        mode="lines",
        name="Projected Dividend",
        yaxis="y2"
    ))

    fig2.update_layout(
        title="Projection Model",
        xaxis_title="Year",
        yaxis=dict(title="Projected Price"),
        yaxis2=dict(
            title="Projected Dividend",
            overlaying="y",
            side="right"
        ),
        template="plotly_white"
    )

    st.plotly_chart(fig2, use_container_width=True)

    # ==========================
    # EXCEL EXPORT
    # ==========================

    output = BytesIO()

    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name="Historical Data")
        projection_df.to_excel(writer, sheet_name="Projections", index=False)

    st.download_button(
        label="Download Excel Report",
        data=output.getvalue(),
        file_name=f"{ticker_symbol}_analysis.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )