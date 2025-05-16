import streamlit as st
import pandas as pd
from datetime import datetime
from data_engineering_tab5 import generate_instrument_lists, concatenate_commodity_data_for_unique_instruments, check_instrument_expiry_month_only, check_instrument_expiry_dict, plot_seasonality_chart_tab6, check_month_status

# Month character code mapping
month_code_map = {
    'F': 1, 'G': 2, 'H': 3, 'J': 4, 'K': 5, 'M': 6,
    'N': 7, 'Q': 8, 'U': 9, 'V': 10, 'X': 11, 'Z': 12
}

# Get current year and month (for expiry comparison)
current_year = datetime.now().year
current_month = datetime.now().month

def render_tab6(instruments, meta_A_month_int, list_of_input_instruments):
    st.markdown("## 📈 Spread Analysis [Spread = Compared Instrument - Base Instrument]")

    # 1. Expiry status check
    month_status_dict = check_month_status(month_code_map)
    
    # 2. Generate unique instruments and root symbols
    instrument_expiry_check = check_instrument_expiry_month_only(list_of_input_instruments)
    _, unique_instruments = generate_instrument_lists(instrument_expiry_check)
    root_symbols = sorted(set(inst[:-3] for inst in unique_instruments))

    # UI Section: Selection for Root Symbol and Months
    st.markdown("---")
    st.subheader("🔍 Select Instrument and Months")

    # Use expanders to organize sections and reduce clutter
    with st.expander("Select Root Symbol", expanded=True):
        selected_root = st.selectbox("Choose Root Symbol:", root_symbols, key="root_symbol")
    
    with st.expander("Select Months for Comparison", expanded=True):
        selected_base_month = st.selectbox("Select Base Month Code:", list(month_code_map.keys()), key="base_month")
        selected_comparison_month = st.selectbox("Select Comparison Month Code:", list(month_code_map.keys()), key="comparison_month")
        
        # Adding expiry status for each month from month_status_dict
        base_expiry_status = month_status_dict.get(selected_base_month, "Unknown")        
        # Determine the base year
        if base_expiry_status == "expired_month":
            base_year = current_year + 1  # If expired, base year is next year
        else:
            base_year = current_year  # If not expired, base year is the current year
        
        # Subtract 2000 from both base and comparison years
        base_year_minus_2k = base_year - 2000
        comparison_year_minus_2k = current_year - 2000  # Comparison year is always the current year - 2000
    
    # Display selected base and comparison months with their expiry status
    if selected_root and selected_base_month and selected_comparison_month:
        # Ensure base month and comparison month are different
        if selected_base_month != selected_comparison_month:
            base_instr = f"{selected_root}{selected_base_month}{base_year_minus_2k}"  # Replace with calculated base year
            comp_instr = f"{selected_root}{selected_comparison_month}{comparison_year_minus_2k}"
            # Initialize lists to store instruments
            base_instr_list = []
            comp_instr_list = []

            # Generate the instruments for the base month and comparison month
            for year_offset in range(-10, 1):  # Range from base_year_minus_2k - 10 to base_year_minus_2k
                base_year = base_year_minus_2k + year_offset
                comparison_year = base_year_minus_2k + year_offset

                # Generate the base_instr and comp_instr for each year offset
                base_instr = f"{selected_root}{selected_base_month}{base_year}"
                comp_instr = f"{selected_root}{selected_comparison_month}{comparison_year}"

                # Append to respective lists
                base_instr_list.append(base_instr)
                comp_instr_list.append(comp_instr)

            st.write(base_instr_list)
            st.write(comp_instr_list)







        else:
            st.warning("Base Month and Comparison Month should be different. Please select different months.")

    else:
        st.warning("Please select both the Base and Comparison months.")



    # Final Data Concatenation and Error Handling
    df_final = concatenate_commodity_data_for_unique_instruments(unique_instruments, max_retries=5, retry_delay=5)
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
    with st.expander("📌 Live Instruments:", expanded=True):
        selected_valid = st.multiselect("Select Live Instruments:", valid_instruments, default=valid_instruments[:5])

    with st.expander("🗂️ Dead Instruments", expanded=True):
        selected_expired = st.multiselect("Select Dead Instruments:", expired_instruments, default=expired_instruments[:5])

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
    plot_seasonality_chart_tab6(df_filtered, meta_A_month_int)
