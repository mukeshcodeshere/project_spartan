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
print(f"Current month: {current_month}")  # Debugging: Show the current month

# Function to check if an instrument has expired
def check_instrument_expiry(instruments):
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

    for instrument in unique_instruments:
        success = False
        for attempt in range(1, max_retries + 1):
            try:
                with st.spinner(f"Attempt {attempt}/{max_retries} - Fetching data for {instrument}..."):
                    df_commodity_data = get_mv_data(instrument, start_date, end_date, False)

                if df_commodity_data is not None and not df_commodity_data.empty:
                    df_commodity_data['Instrument'] = instrument
                    fetched_data.append(df_commodity_data)
                    success = True
                    break  # Exit retry loop on success
                else:
                    st.warning(f"⚠️ No data returned for {instrument} on attempt {attempt}. Retrying...")
            except Exception as e:
                st.error(f"❌ Error on attempt {attempt} for {instrument}: {e}")
            
            time.sleep(retry_delay)  # Delay before next attempt

        if not success:
            failed_instruments.append(instrument)

    if failed_instruments:
        st.error(f"❌ Failed to fetch data for the following instruments after {max_retries} attempts: {', '.join(failed_instruments)}")
    else:
        st.success("✅ All instruments fetched successfully.")

    df_final = pd.concat(fetched_data, ignore_index=True) if fetched_data else pd.DataFrame()
    return df_final
