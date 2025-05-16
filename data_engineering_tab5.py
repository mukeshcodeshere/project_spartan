import pandas as pd
from datetime import datetime
from gcc_sparta_lib import get_mv_data
from datetime import datetime, timedelta
import streamlit as st
import time
# Today's date
end_date = datetime.today()

# Approximate 15 years ago (15 * 365.25 to account for leap years)
start_date = end_date - timedelta(days=15*365.25)

# Month code mapping
month_code_map = {
    'F': 1,  # Jan
    'G': 2,  # Feb
    'H': 3,  # Mar
    'J': 4,  # Apr
    'K': 5,  # May
    'M': 6,  # Jun
    'N': 7,  # Jul
    'Q': 8,  # Aug
    'U': 9,  # Sep
    'V': 10, # Oct
    'X': 11, # Nov
    'Z': 12  # Dec
}

# Get the current month
current_month = datetime.now().month
current_year = datetime.now().year

# Function to check if an instrument has expired
def check_instrument_expiry_month_only(instruments):
    expired_instruments = []

    for instrument in instruments:
        #print(f"Processing instrument: {instrument}")  # Debugging: Show current instrument

        # Step 1: Check if the instrument code is long enough
        if len(instrument) < 4:
            #print(f"Warning: Instrument code {instrument} is too short to process. Skipping...")
            continue
        
        # Step 2: Drop the last two characters (validate input length)
        shortened_instrument = instrument[:-2]
        #print(f"Shortened instrument (last two characters removed): {shortened_instrument}")  # Debugging: Show shortened instrument

        # Step 3: Take the last character as the month character
        month_char = shortened_instrument[-1]
        #print(f"Extracted month character: {month_char}")  # Debugging: Show extracted month character

        # Step 4: Get the corresponding month number from the month_code_map
        instrument_month = month_code_map.get(month_char, None)

        if instrument_month is None:
            #print(f"Invalid month code: {month_char} in {instrument}. Skipping...")  # Debugging: Show invalid month code
            continue
        
        # Step 5: Compare the current month with the instrument's month
       # print(f"Instrument month: {instrument_month}, Current month: {current_month}")  # Debugging: Show month comparison

        if current_month >= instrument_month:
            expired_instruments.append((instrument, "expired"))
        else:
            expired_instruments.append((instrument, "valid"))
    
    return expired_instruments

def generate_instrument_lists(instrument_expiry_check):
    """
    Generate a new list of instruments based on expiry status and years.
    """
    # Get current year and calculate start_year and end_year
    current_year = datetime.now().year
    start_year = current_year - 10

    # List to store the new instrument lists
    new_instrument_lists = []

    # Process each instrument and create the desired lists
    for instrument, status in instrument_expiry_check:
        # Calculate end_year based on expiration status
        end_year = current_year + 1 if status == "expired" else current_year

        # Generate the list of years
        year_range = [str(year)[2:] for year in range(start_year, end_year + 1)]

        # Remove the last 2 characters from the instrument and concatenate with the years
        instrument_base = instrument[:-2]  # Drop last 2 characters
        new_instrument_list = [instrument_base + year for year in year_range]

        # Add the new instrument list to the result
        new_instrument_lists.append(new_instrument_list)

    # Concatenate all the lists together and remove duplicates
    all_instruments = [instrument for sublist in new_instrument_lists for instrument in sublist]
    unique_instruments = list(set(all_instruments))

    # Sort the unique instruments (optional, but keeps the order consistent)
    unique_instruments.sort()

    return new_instrument_lists,unique_instruments

@st.cache_data
def concatenate_commodity_data_for_unique_instruments(unique_instruments, max_retries=5, retry_delay=5):
    fetched_data = []
    failed_instruments = []

    progress_bar = st.progress(0)
    status_text = st.empty()

    total_instruments = len(unique_instruments)

    for idx, instrument in enumerate(unique_instruments, start=1):
        success = False
        for attempt in range(1, max_retries + 1):
            try:
                with st.spinner(f"Attempt {attempt}/{max_retries} - Fetching data for {instrument}..."):
                    df_commodity_data = get_mv_data(instrument, start_date, end_date, False)

                if df_commodity_data is not None and not df_commodity_data.empty:
                    df_commodity_data['Instrument'] = instrument
                    fetched_data.append(df_commodity_data)
                    success = True
                    break
                else:
                    print(f" No data returned for {instrument} on attempt {attempt}. Retrying...")
            except Exception as e:
                print(f" Error on attempt {attempt} for {instrument}: {e}")
            
            time.sleep(retry_delay)

        if not success:
            failed_instruments.append(instrument)

        # Update progress bar
        progress = idx / total_instruments
        progress_bar.progress(progress)
        status_text.text(f"Processed {idx}/{total_instruments} instruments")

    if failed_instruments:
        st.error(f"❌ Failed to fetch data for the following instruments after {max_retries} attempts: {', '.join(failed_instruments)}")
    else:
        st.success("✅ All instruments fetched successfully.")

    df_final = pd.concat(fetched_data, ignore_index=True) if fetched_data else pd.DataFrame()
    return df_final

def check_instrument_expiry_dict(instruments):
    instrument_status = []
    
    # Get the current year and month for comparison
    current_date = datetime.now()
    current_year = current_date.year
    current_month = current_date.month

    for instrument in instruments:
        if len(instrument) < 4:
            instrument_status.append((instrument, "invalid"))  # Short instruments are invalid
            continue
        
        # Extract the last two digits of the year and convert them to a full year
        instrument_year = 2000 + int(instrument[-2:])
        
        # Extract the month character and map it to a month number
        month_char = instrument[-3]
        instrument_month = month_code_map.get(month_char, None)

        if instrument_month is None:
            instrument_status.append((instrument, "invalid month"))
            continue
        
        # Determine if the instrument is expired or valid
        if (instrument_year < current_year) or (instrument_year == current_year and instrument_month < current_month):
            instrument_status.append((instrument, "expired"))
        else:
            instrument_status.append((instrument, "valid"))
    
    return instrument_status

def plot_seasonality_chart_tab5(df_filtered, meta_A_month_int):
    import plotly.graph_objects as go
    import pandas as pd
    import streamlit as st
    import itertools

    df_expired = df_filtered[df_filtered['ExpiryStatus'] == 'expired']
    df_valid = df_filtered[df_filtered['ExpiryStatus'] == 'valid']

    fig = go.Figure()
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    # Generate unique colors for each instrument
    color_palette = itertools.cycle([
        "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728",
        "#9467bd", "#8c564b", "#e377c2", "#7f7f7f",
        "#bcbd22", "#17becf"
    ])
    instrument_colors = {instrument: next(color_palette) for instrument in df_filtered['Instrument'].unique()}

    # === Plot expired instruments ===
    for (instrument, year), group in df_expired.groupby(['Instrument', 'Year']):
        group = group.sort_values('TradingDayOfYear').tail(252).reset_index(drop=True)
        group = group.copy()
        group.loc[:, 'trading_day_index'] = range(len(group))
        fig.add_trace(go.Scatter(
            x=group['trading_day_index'],
            y=group['Close'],
            mode='lines',
            name=f"{instrument} - {year} (Expired)",
            line=dict(dash='dash', width=2, color=instrument_colors[instrument]),
            opacity=0.7
        ))

    # === Plot valid instruments ===
    if df_valid.empty:
        st.write("No valid instruments found.")
        return

    max_valid_date = df_valid['Date'].max()
    start_year = max_valid_date.year
    start_date = pd.Timestamp(year=start_year, month=meta_A_month_int, day=1)

    def date_to_trading_index(date, start):
        days_diff = (date - start).days
        trading_index = days_diff * 5 / 7
        return trading_index

    valid_data = df_valid[df_valid['Date'] >= start_date].copy()
    if valid_data.empty:
        st.write("No valid data after adjusted start date.")
    else:
        for (instrument, year), group in valid_data.groupby(['Instrument', 'Year']):
            group = group.sort_values('Date').copy()
            group.loc[:, 'trading_day_index'] = group['Date'].apply(lambda d: date_to_trading_index(d, start_date))
            fig.add_trace(go.Scatter(
                x=group['trading_day_index'],
                y=group['Close'],
                mode='lines',
                name=f"{instrument} - {year} (Valid)",
                line=dict(dash='solid', width=3, color=instrument_colors[instrument]),
                opacity=1
            ))

    # Month ticks
    month_positions = [i * 21 for i in range(12)]
    month_labels = [month_names[(meta_A_month_int - 1 + i) % 12] for i in range(12)]

    fig.update_layout(
        title=f"📅 Seasonality Chart (Starting from {month_names[meta_A_month_int - 1]})",
        xaxis=dict(title="Month", tickvals=month_positions, ticktext=month_labels),
        yaxis_title="Close Price",
        height=600,
        template="plotly_white",
        showlegend=True
    )

    st.plotly_chart(fig, use_container_width=True)
