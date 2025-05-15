import pandas as pd
from datetime import datetime

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
        print(f"Processing instrument: {instrument}")  # Debugging: Show current instrument

        # Step 1: Check if the instrument code is long enough
        if len(instrument) < 4:
            print(f"Warning: Instrument code {instrument} is too short to process. Skipping...")
            continue
        
        # Step 2: Drop the last two characters (validate input length)
        shortened_instrument = instrument[:-2]
        print(f"Shortened instrument (last two characters removed): {shortened_instrument}")  # Debugging: Show shortened instrument

        # Step 3: Take the last character as the month character
        month_char = shortened_instrument[-1]
        print(f"Extracted month character: {month_char}")  # Debugging: Show extracted month character

        # Step 4: Get the corresponding month number from the month_code_map
        instrument_month = month_code_map.get(month_char, None)

        if instrument_month is None:
            print(f"Invalid month code: {month_char} in {instrument}. Skipping...")  # Debugging: Show invalid month code
            continue
        
        # Step 5: Compare the current month with the instrument's month
        print(f"Instrument month: {instrument_month}, Current month: {current_month}")  # Debugging: Show month comparison

        if current_month >= instrument_month:
            expired_instruments.append((instrument, "expired"))
        else:
            expired_instruments.append((instrument, "valid"))
    
    return expired_instruments