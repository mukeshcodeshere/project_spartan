import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from data_engineering_tab5 import generate_instrument_lists,concatenate_commodity_data_for_unique_instruments,check_instrument_expiry_month_only,check_instrument_expiry_dict,plot_seasonality_chart_tab5

# Month character code mapping
month_code_map = {
    'F': 1,  'G': 2,  'H': 3,  'J': 4,  'K': 5,  'M': 6,
    'N': 7,  'Q': 8,  'U': 9,  'V': 10, 'X': 11, 'Z': 12
}

# Get current month (for expiry comparison)
current_month = datetime.now().month

def render_tab5(merged_data, instruments, meta_A_month_int, list_of_input_instruments):
    st.markdown('<div class="section-header"> Seasonal Pattern Analysis </div>', unsafe_allow_html=True)
    st.info("⏳ Please wait a few minutes while we load all the instruments.")

    # 1. Expiry status check
    instrument_expiry_check = check_instrument_expiry_month_only(list_of_input_instruments)
    expiry_status_dict = dict(instrument_expiry_check)

    # 2. Generate unique instruments and fetch data
    new_instrument_lists, unique_instruments = generate_instrument_lists(instrument_expiry_check)
    df_final = concatenate_commodity_data_for_unique_instruments(unique_instruments, max_retries=3, retry_delay=3)
    if df_final is None or df_final.empty:
        st.error("❌ Failed to retrieve commodity data.")
        return

    # 3. Clean and sort
    df_final = df_final[['Instrument', 'Date', 'Close']].dropna(subset=['Date'])
    df_final['Date'] = pd.to_datetime(df_final['Date'])
    df_final.sort_values(['Instrument', 'Date'], inplace=True)

    # 4. Add expiry status
    expiry_status_full = dict(check_instrument_expiry_dict(unique_instruments))
    df_final['ExpiryStatus'] = df_final['Instrument'].map(expiry_status_full)

    # 5. Instrument selection - PRIORITIZE valid ones
    valid_instruments = sorted(df_final[df_final['ExpiryStatus'] == 'valid']['Instrument'].unique())
    expired_instruments = sorted(df_final[df_final['ExpiryStatus'] == 'expired']['Instrument'].unique())

    st.subheader("🎯 Instrument Selection")
    with st.expander("📌 Active Instruments:", expanded=True):
        selected_valid = st.multiselect("Select Active Instruments:", valid_instruments, default=valid_instruments[:5])

    with st.expander("🗂️ Expired Instruments", expanded=True):
        selected_expired = st.multiselect("Select Expired Instruments:", expired_instruments, default=expired_instruments[:5])

    selected_all = selected_valid + selected_expired
    df_filtered = df_final[df_final['Instrument'].isin(selected_all)]

    if df_filtered.empty:
        st.warning("⚠️ No data available for the selected instruments.")
        return

    # 6. Add year and trading day
    df_filtered['Year'] = df_filtered['Instrument'].str[-2:].astype(int) + 2000
    df_filtered['TradingDayOfYear'] = (
        df_filtered.sort_values(['Instrument', 'Year', 'Date'])
        .groupby(['Instrument', 'Year'])
        .cumcount() + 1
    )

    # DataFrame preview
    with st.expander("📊 Preview Filtered Data"):
        st.dataframe(df_filtered)
    
    print(df_filtered.head())
    print(df_filtered.tail())

    # 7. Plotting (preserve existing logic but prioritize valid)
    plot_seasonality_chart_tab5(df_filtered, meta_A_month_int)
