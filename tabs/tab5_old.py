import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from data_engineering_tab5 import generate_instrument_lists,concatenate_commodity_data_for_unique_instruments,check_instrument_expiry_dict

# Month character code mapping
month_code_map = {
    'F': 1,  'G': 2,  'H': 3,  'J': 4,  'K': 5,  'M': 6,
    'N': 7,  'Q': 8,  'U': 9,  'V': 10, 'X': 11, 'Z': 12
}

# Get current month (for expiry comparison)
current_month = datetime.now().month


# 🔄 Main seasonal plot function
def render_tab5(merged_data, instruments, meta_A_month_int, list_of_input_instruments):
    st.markdown('<div class="section-header">📈 Seasonal Pattern Analysis (252 Trading Days per Year)</div>', unsafe_allow_html=True)
    st.info("⏳ Aligns trading day number within each year for seasonal comparison. No averaging or aggregation applied.")

    # Step 1: Prepare instruments and data
    instrument_expiry_check = check_instrument_expiry_dict(list_of_input_instruments)
    expiry_status_dict = {inst: status for inst, status in instrument_expiry_check}

    new_instrument_lists, unique_instruments = generate_instrument_lists(instrument_expiry_check)

    df_final = concatenate_commodity_data_for_unique_instruments(unique_instruments, max_retries=5, retry_delay=5)
    if df_final is None or df_final.empty:
        st.error("❌ Failed to retrieve commodity data.")
        return

    df_final = df_final[['Instrument', 'Date', 'Close']]
    df_final['Date'] = pd.to_datetime(df_final['Date'], errors='coerce')
    df_final.dropna(subset=['Date'], inplace=True)
    df_final.sort_values(['Instrument', 'Date'], inplace=True)

    # User selection
    all_instruments = df_final['Instrument'].unique()
    selected_instruments = st.multiselect("Select Instrument(s):", all_instruments, default=all_instruments)
    df_filtered = df_final[df_final['Instrument'].isin(selected_instruments)]

    # Add Year and TradingDayOfYear
    df_filtered['Year'] = df_filtered['Instrument'].str[-2:].astype(int) + 2000
    df_filtered['TradingDayOfYear'] = (
        df_filtered
        .sort_values(['Instrument', 'Year', 'Date'])
        .groupby(['Instrument', 'Year'])
        .cumcount() + 1
    )

    # Add expiry status to each row
    df_filtered['ExpiryStatus'] = df_filtered['Instrument'].map(expiry_status_dict)

    # Apply different filters for non-expired and expired items
    #first logic for only expired things
    df_filtered_expired = df_filtered[df_filtered['ExpiryStatus'] == 'expired']
    df_filtered_valid = df_filtered[df_filtered['ExpiryStatus'] == 'valid']
    
    # Create Instrument-Year label
    df_filtered['Instrument_Year'] = df_filtered['Instrument'].astype(str) + " - " + df_filtered['Year'].astype(str)

    # Plotting
    fig = go.Figure()
    for label, group in df_filtered.groupby('Instrument_Year'):
        expiry_status = group['ExpiryStatus'].iloc[0]
        line_style = 'dash' if expiry_status == 'valid' else 'solid'

        fig.add_trace(go.Scatter(
            x=group['TradingDayOfYear'],
            y=group['Close'],
            mode='lines',
            name=label,
            line=dict(dash=line_style)
        ))

    fig.update_layout(
        title="Seasonality Chart by Trading Day (Aligned by Year)",
        xaxis_title="Trading Day of the Year",
        yaxis_title="Close Price",
        height=600
    )

    st.plotly_chart(fig, use_container_width=True)
