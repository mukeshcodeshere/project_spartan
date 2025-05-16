import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from scipy.stats import gaussian_kde
from data_engineering import load_commodity_data
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
    
    st.write("=======================================")

    # Process the list and check expiry
    instrument_expiry_check = check_instrument_expiry(list_of_input_instruments)

    # Generate the new instrument lists based on expiry check
    new_instrument_lists, unique_instruments = generate_instrument_lists(instrument_expiry_check)
    df_final = concatenate_commodity_data_for_unique_instruments(unique_instruments, max_retries=5, retry_delay=5)
    
    if df_final is None or df_final.empty:
        st.error("Failed to retrieve commodity data. Please try again later.")
        return
        
    st.write("Data retrieved successfully:")
    st.write(df_final.head())
    
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
    
    st.write("=======================================")
    st.write(f"Processed data with {len(df_seasonal)} rows")
    
    # Create sidebar for settings
    with st.sidebar.expander("Seasonal Analysis Settings", expanded=False):
        all_years = sorted(set(df_seasonal['Year']))
        selected_years = st.multiselect(
            "Select years to display:", 
            all_years, 
            default=all_years[-3:] if len(all_years) > 3 else all_years,
            key="tab5_years_select"  # Added unique key
        )
        exclude_months = st.multiselect(
            "Exclude months:", 
            list(trading_month_ranges.keys()), 
            default=[],
            key="tab5_months_select"  # Added unique key
        )
    
    # Collect days to exclude based on selected months
    excluded_days = set()
    for month in exclude_months:
        start, end = trading_month_ranges[month]
        excluded_days.update(range(start, end + 1))
    
    # Determine starting month from meta_A_month_int
    starting_month = month_int_to_abbr.get(meta_A_month_int, "Jan")  # Default to Jan if invalid
    
    # Create plot function to visualize data starting from the specified month
    def create_seasonal_plot(data, title):
        if data is None or data.empty:
            st.warning(f"No data available for {title}")
            return
        
        fig = go.Figure()
        
        # Get start trading day based on starting month
        start_day = trading_month_ranges[starting_month][0]
        
        # Process each instrument to create a line on the plot
        for instrument, group in data.groupby('Instrument'):
            # Map trading day to shifted trading day based on starting month
            group = group.copy()
            group['ShiftedTradingDay'] = group['TradingDayNum'].apply(
                lambda day: day - start_day + 1 if day >= start_day else 252 - start_day + 1 + day
            )
            
            # Sort by shifted trading day
            group = group.sort_values('ShiftedTradingDay')
            
            # Normalize close prices to start at 100 for better comparison
            first_close = group['Close'].iloc[0]
            group['NormalizedClose'] = group['Close'] / first_close * 100
            
            # Add trace for this instrument
            fig.add_trace(go.Scatter(
                x=group['ShiftedTradingDay'],
                y=group['NormalizedClose'],
                mode='lines',
                name=instrument,
                hovertemplate=f"Instrument: {instrument}<br>Trading Day: %{{x}}<br>Value: %{{y:.2f}}<extra></extra>"
            ))
        
        # Set x-axis ticks to display months
        xticks = []
        xlabels = []
        
        # Get the correct order of months starting from the selected starting month
        months = list(trading_month_ranges.keys())
        start_month_idx = months.index(starting_month)
        shifted_month_order = months[start_month_idx:] + months[:start_month_idx]
        
        for month in shifted_month_order:
            original_start = trading_month_ranges[month][0]
            if original_start >= start_day:
                sx = original_start - start_day + 1
            else:
                sx = (252 - start_day + 1) + original_start
            xticks.append(sx)
            xlabels.append(month)
        
        fig.update_layout(
            title=title,
            xaxis=dict(
                tickmode='array',
                tickvals=xticks,
                ticktext=xlabels,
                title='Month'
            ),
            yaxis_title='Normalized Value (Starting at 100)',
            legend_title='Instrument',
            height=600,
            margin=dict(t=40, b=40),
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Create the main visualization
    st.subheader("📊 Instrument Seasonal Comparison")
    st.write(f"Seasonal analysis starting from {starting_month} (using last 252 trading days for each instrument)")
    
    # Filter data for plotting
    # 1. Only include selected years if specified
    if selected_years:
        plot_data = df_seasonal[df_seasonal['Year'].isin(selected_years)].copy()
    else:
        plot_data = df_seasonal.copy()
    
    # 2. Exclude days from excluded months
    if excluded_days:
        plot_data = plot_data[~plot_data['TradingDayNum'].isin(excluded_days)]
    
    # Create the plot
    create_seasonal_plot(plot_data, "Instrument Performance Over Trading Year")