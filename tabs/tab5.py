import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from scipy.stats import gaussian_kde
from data_engineering import load_commodity_data
import plotly.express as px
from data_engineering_tab5 import check_instrument_expiry, generate_instrument_lists, concatenate_commodity_data_for_unique_instruments

def render_tab5(merged_data, instruments, meta_A_month_int, list_of_input_instruments):
    st.markdown('<div class="section-header">📈 Trading Period Seasonal Analysis (Backward Fill)</div>', unsafe_allow_html=True)

    # Inform the user about potential rendering delay
    st.info("⏳ Please note: This tab may take a few minutes to load, as it processes a large number of instruments.")
    
    # Map month numbers to abbreviations
    month_int_to_abbr = {
        1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr",
        5: "May", 6: "Jun", 7: "Jul", 8: "Aug",
        9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"
    }
    
    # Define month ranges for 252 business days (approximately 21 trading days per month)
    trading_month_ranges = {
        "Jan": (1, 21), "Feb": (22, 42), "Mar": (43, 63), "Apr": (64, 84),
        "May": (85, 105), "Jun": (106, 126), "Jul": (127, 147), "Aug": (148, 168),
        "Sep": (169, 189), "Oct": (190, 210), "Nov": (211, 231), "Dec": (232, 252)
    }

    # Process the list and check expiry
    instrument_expiry_check = check_instrument_expiry(list_of_input_instruments)

    # Generate the new instrument lists based on expiry check
    new_instrument_lists, unique_instruments = generate_instrument_lists(instrument_expiry_check)
    df_final = concatenate_commodity_data_for_unique_instruments(unique_instruments, max_retries=5, retry_delay=5)
    
    if df_final is None or df_final.empty:
        st.error("Failed to retrieve commodity data. Please try again later.")
        return
    
    # Filter to required columns and sort
    df_final = df_final[['Instrument', 'Date', 'Close']]
    df_final['Date'] = pd.to_datetime(df_final['Date'], errors='coerce')
    df_final = df_final.dropna(subset=['Date'])
    df_final = df_final.sort_values(['Instrument', 'Date'])
    
    # Calculate trading day of year (1-252) for each instrument
    df_final['Year'] = df_final['Date'].dt.year
    
    # Process each instrument to map to trading days (1-252)
    instrument_dfs = []
    for instrument, group in df_final.groupby('Instrument'):
        # Keep last 252 trading days for each instrument
        last_252_days = group.sort_values('Date').tail(252).copy()
        
        if len(last_252_days) == 0:
            st.warning(f"No data available for {instrument}")
            continue
            
        # Create trading day number (1-252)
        last_252_days['TradingDayNum'] = range(1, len(last_252_days) + 1)
        
        # If we have less than 252 days, we'll still use what we have
        instrument_dfs.append(last_252_days)
    
    # Combine all processed instruments
    df_seasonal = pd.concat(instrument_dfs)
    print(df_seasonal.columns)
    print(df_seasonal)
    # View seasonality data
    if not df_seasonal.empty:
        with st.expander("Click to view data", expanded=False):
            st.dataframe(df_seasonal)
    else:
        st.warning("No seasonality data available.")

    # Generate the plot
    fig = px.line(
        df_seasonal,
        x='TradingDayNum',
        y='Close',
        color='Instrument',
        title='Seasonality Data by Instrument',
        labels={
            "TradingDayNum": "Trading Day Number",
            "Close": "Close Price",
            "Instrument": "Instrument"
        }
    )

    # Display it in Streamlit
    st.plotly_chart(fig, use_container_width=True)


