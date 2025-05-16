import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from data_engineering_tab5 import generate_instrument_lists,concatenate_commodity_data_for_unique_instruments,check_instrument_expiry_month_only,check_instrument_expiry_dict

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
    instrument_expiry_check = check_instrument_expiry_month_only(list_of_input_instruments)
    expiry_status_dict = {inst: status for inst, status in instrument_expiry_check}

    new_instrument_lists, unique_instruments = generate_instrument_lists(instrument_expiry_check)

    df_final = concatenate_commodity_data_for_unique_instruments(unique_instruments, max_retries=5, retry_delay=5)
    if df_final is None or df_final.empty:
        st.error("❌ Failed to retrieve commodity data.")
        return

    df_final = df_final[['Instrument', 'Date', 'Close']]
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
    instrument_expiry_check_full = check_instrument_expiry_dict(unique_instruments)
    expiry_status_dict = {inst: status for inst, status in instrument_expiry_check_full}
    # Add expiry status to each row
    df_filtered['ExpiryStatus'] = df_filtered['Instrument'].map(expiry_status_dict)

    # Handle the merged data
    if not df_filtered.empty:
        st.info("Filtered is available for analysis.")
        with st.expander("Click to view filtered data", expanded=False):
            st.dataframe(df_filtered)
    else:
        st.warning("No data available for the selected commodities.")

    import pandas as pd
    import plotly.graph_objects as go

    # Filter the data
    df_expired = df_filtered[df_filtered['ExpiryStatus'] == 'expired']
    df_valid = df_filtered[df_filtered['ExpiryStatus'] == 'valid']

    # Month names
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    # Define function to convert trading day index to shifted month (for expired instruments)
    def trading_day_to_month(day, total_days=252):
        month_fraction = day / total_days * 12
        shifted_month = (month_fraction + (meta_A_month_int - 1)) % 12
        return int(shifted_month)

    # Create figure
    fig = go.Figure()

    # ===============================
    # Process EXPIRED instruments
    # ===============================
    instrument_data_expired = {}
    for (instrument, year), group in df_expired.groupby(['Instrument', 'Year']):
        group = group.sort_values('TradingDayOfYear').tail(252)
        group = group.reset_index(drop=True)
        group['trading_day_index'] = range(len(group))
        instrument_data_expired[f"{instrument} - {year}"] = group

    for label, data in instrument_data_expired.items():
        fig.add_trace(go.Scatter(
            x=data['trading_day_index'],
            y=data['Close'],
            mode='lines',
            name=f"{label} (Expired)",
            line=dict(dash='solid')
        ))

    # ===============================
    # Process VALID instruments
    # ===============================
    # Ensure Date column is datetime
    # if not pd.api.types.is_datetime64_any_dtype(df_valid['Date']):
    #     df_valid['Date'] = pd.to_datetime(df_valid['Date'])

    current_year = df_valid['Date'].dt.year.max()
    start_date = pd.Timestamp(year=current_year, month=meta_A_month_int, day=1)
    df_valid_filtered = df_valid[df_valid['Date'] >= start_date]

    def date_to_trading_index(date, start_date):
        calendar_days = (date - start_date).days
        return calendar_days * 5/7  # Approximate trading days

    instrument_data_valid = {}
    for (instrument, year), group in df_valid_filtered.groupby(['Instrument', 'Year']):
        group = group.sort_values('Date').copy()
        group['trading_day_index'] = group['Date'].apply(lambda d: date_to_trading_index(d, start_date))
        instrument_data_valid[f"{instrument} - {year}"] = group

    for label, data in instrument_data_valid.items():
        fig.add_trace(go.Scatter(
            x=data['trading_day_index'],
            y=data['Close'],
            mode='lines',
            name=f"{label} (Valid)",
            line=dict(dash='dash')  # Dashed for valid
        ))

    # ===============================
    # X-axis month positions
    # ===============================
    month_positions = []
    month_labels = []

    for i in range(12):
        month_index = (meta_A_month_int - 1 + i) % 12
        position = i * 21  # Approx 21 trading days per month
        month_positions.append(position)
        month_labels.append(month_names[month_index])

    # ===============================
    # Final plot layout
    # ===============================
    fig.update_layout(
        title=f"Seasonality Chart for Expired and Valid Instruments (Starting from {month_names[meta_A_month_int - 1]})",
        xaxis=dict(
            title="Month",
            tickvals=month_positions,
            ticktext=month_labels
        ),
        yaxis_title="Close Price",
        height=600
    )

    # Display the chart
    st.plotly_chart(fig, use_container_width=True)


    # # Apply different filters for non-expired and expired items
    # #first logic for only expired things
    # df_filtered_expired = df_filtered[df_filtered['ExpiryStatus'] == 'expired']
    # df_filtered_valid = df_filtered[df_filtered['ExpiryStatus'] == 'valid']

    # ##########################################################
    # # THIS IS LOGIC For expired Instruments
    # # First, filter for expired instruments only
    # # df_expired = df_filtered[df_filtered['ExpiryStatus'] == 'expired']

    # # # Dictionary to hold the last 252 trading days for each expired instrument
    # # instrument_data = {}

    # # # Group by Instrument and Year
    # # for (instrument, year), group in df_expired.groupby(['Instrument', 'Year']):
    # #     # Sort by TradingDayOfYear to ensure chronological order
    # #     group = group.sort_values('TradingDayOfYear')
        
    # #     # Take only the last 252 trading days (or all if less than 252)
    # #     last_252_days = group.tail(252)
        
    # #     # Store in dictionary with proper identifier
    # #     key = f"{instrument} - {year}"
    # #     instrument_data[key] = last_252_days

    # # # Create a new figure
    # # fig = go.Figure()

    # # # Define month names for x-axis
    # # month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    # # # Get meta_A_month_int (assuming it's available in your environment)
    # # # Function to convert trading day to month label, starting from meta_A_month_int
    # # def trading_day_to_month(day, total_days=252):
    # #     # Calculate approximate month (0-11)
    # #     month_fraction = day / total_days * 12
    # #     # Shift by meta_A_month_int - 1 (0-indexed)
    # #     shifted_month = (month_fraction + (meta_A_month_int - 1)) % 12
    # #     return int(shifted_month)

    # # # Plot each instrument
    # # for label, data in instrument_data.items():
    # #     # Reset the x-axis to be 0-based index of trading days
    # #     data = data.reset_index(drop=True)
    # #     data['trading_day_index'] = range(len(data))
        
    # #     # Create month labels for the data
    # #     data['month'] = data['trading_day_index'].apply(lambda x: trading_day_to_month(x))
        
    # #     fig.add_trace(go.Scatter(
    # #         x=data['trading_day_index'],
    # #         y=data['Close'],
    # #         mode='lines',
    # #         name=label
    # #     ))

    # # # Create custom x-axis ticks at month boundaries
    # # month_positions = []
    # # month_labels = []

    # # for i in range(12):
    # #     # Calculate position for each month (assuming equal distribution)
    # #     position = i * (252 / 12)
    # #     month_index = (i + meta_A_month_int - 1) % 12
        
    # #     month_positions.append(position)
    # #     month_labels.append(month_names[month_index])

    # # # Update layout with custom x-axis ticks
    # # fig.update_layout(
    # #     title="Seasonality Chart for Expired Instruments (Last 252 Trading Days)",
    # #     xaxis=dict(
    # #         title="Month",
    # #         tickvals=month_positions,
    # #         ticktext=month_labels
    # #     ),
    # #     yaxis_title="Close Price",
    # #     height=600
    # # )

    # # st.plotly_chart(fig, use_container_width=True)
    # ##########################################################
    # # THIS IS LOGIC For valid Instruments
    # # Filter for valid instruments
    # df_valid = df_filtered[df_filtered['ExpiryStatus'] == 'valid']

    # # Assuming you have a Date column in your dataframe
    # # Convert it to datetime if it's not already
    # if not pd.api.types.is_datetime64_any_dtype(df_valid['Date']):
    #     df_valid['Date'] = pd.to_datetime(df_valid['Date'])

    # # Get meta_A_month_int (assuming it's available in your environment)
    # current_year = df_valid['Date'].dt.year.max()  # Use current/latest year in data

    # # Create the start date for filtering: 1st day of meta_A_month_int month in the current year
    # start_date = pd.Timestamp(year=current_year, month=meta_A_month_int, day=1)

    # # Filter data to only include dates on or after the start date
    # df_valid_filtered = df_valid[df_valid['Date'] >= start_date]

    # # Group by Instrument and Year
    # valid_instrument_data = {}
    # for (instrument, year), group in df_valid_filtered.groupby(['Instrument', 'Year']):
    #     # Sort by Date or TradingDayOfYear to ensure chronological order
    #     group = group.sort_values('Date')
        
    #     # Store in dictionary with proper identifier
    #     key = f"{instrument} - {year}"
    #     valid_instrument_data[key] = group

    # # Create a new figure
    # fig = go.Figure()

    # # Define month names for x-axis
    # month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    # # Function to convert date to normalized trading day index
    # # This will create a continuous x-axis starting from 0 at meta_A_month_int
    # def date_to_trading_index(date, start_date):
    #     # Calculate days since start date, then convert to trading days (approx)
    #     calendar_days = (date - start_date).days
    #     # Approximate trading days (excluding weekends)
    #     trading_days = calendar_days * 5/7  # 5 trading days per 7 calendar days
    #     return trading_days

    # # Plot each valid instrument
    # for label, data in valid_instrument_data.items():
    #     # Calculate trading day index for each date
    #     data['trading_day_index'] = data['Date'].apply(
    #         lambda date: date_to_trading_index(date, start_date)
    #     )
        
    #     # Calculate month for each trading day
    #     data['month'] = data['Date'].dt.month
        
    #     fig.add_trace(go.Scatter(
    #         x=data['trading_day_index'],
    #         y=data['Close'],
    #         mode='lines',
    #         name=label,
    #         line=dict(dash='dash')  # Use dashed line for valid instruments
    #     ))

    # # Calculate month positions for x-axis labels
    # # Assuming approximately 21 trading days per month
    # month_positions = []
    # month_labels = []

    # for i in range(12):
    #     # Starting from meta_A_month_int
    #     month_index = (meta_A_month_int - 1 + i) % 12
    #     # Position based on trading days (approx 21 per month)
    #     position = i * 21
        
    #     month_positions.append(position)
    #     month_labels.append(month_names[month_index])

    # # Update layout with custom x-axis ticks
    # fig.update_layout(
    #     title="Seasonality Chart for Valid Instruments (Starting from Month " + month_names[meta_A_month_int-1] + ")",
    #     xaxis=dict(
    #         title="Month",
    #         tickvals=month_positions,
    #         ticktext=month_labels
    #     ),
    #     yaxis_title="Close Price",
    #     height=600
    # )

    # st.plotly_chart(fig, use_container_width=True)


