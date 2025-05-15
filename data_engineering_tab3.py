##################

###############

def check_expiry_month(month_code: str) -> bool:
    """Returns True if the contract is expired compared to current date."""
    month_code_map = {
        'F': 1,  # Jan
        'G': 2,
        'H': 3,
        'J': 4,
        'K': 5,
        'M': 6,
        'N': 7,
        'Q': 8,
        'U': 9,
        'V': 10,
        'X': 11,
        'Z': 12  # Dec
    }

    contract_month = month_code_map.get(month_code.upper())
    if contract_month is None:
        raise ValueError(f"Invalid month code: {month_code}")

    now = pd.Timestamp.now()
    current_month = now.month

    # Expired if contract is this year and month has already passed or is current
    return (contract_month <= current_month)


def load_commodity_data_py(symbol, start_date, end_date):
    print(f"Loading data for {symbol} from {start_date} to {end_date}")
    try:
        df = get_mv_data(symbol=symbol, start_date=start_date, end_date=end_date)
        print(f"Data shape for {symbol}: {df.shape}")
        if df.empty:
            print(f"[WARN] No data returned for {symbol}.")
        return df
    except Exception as e:
        print(f"[ERROR] Error loading {symbol}: {type(e).__name__} - {e}")
        return pd.DataFrame()

def build_rolling_contract_data(symbol_input, start_date, end_date):
    print(f"\n==> Starting build_rolling_contract_data with input: {symbol_input}")
    try:
        # Extract contract parts
        year_suffix = symbol_input[-2:]          # '25'
        month_code = symbol_input[-3:-2]         # 'F'
        root_symbol = symbol_input[:-3]          # '/HO'

        base_year = int("20" + year_suffix)
        print(f"Parsed root_symbol: {root_symbol}, month_code: {month_code}, base_year: {base_year}")

        # Initial 11-year contract list
        years = list(range(base_year - 10, base_year + 1))
        contracts = [f"{root_symbol}{month_code}{str(y)[-2:]}" for y in years]
        print(f"Initial contract list: {contracts}")

        # Check latest contract expiry
        latest_symbol = contracts[-1]
        latest_data = load_commodity_data_py(latest_symbol, start_date, end_date)

        if not latest_data.empty:
            contract_year_full = str(years[-1])
            checked_data = check_expiry(latest_data, month_code, contract_year_full, latest_symbol)

            if not checked_data.empty and 'expired' in checked_data.columns:
                unique_vals = checked_data['expired'].unique()
                print(f"Expiry column unique values for {latest_symbol}: {unique_vals}")
                if (unique_vals == 1).all():
                    print(f"{latest_symbol} is expired. Shifting contract years.")
                    years = list(range(base_year - 9, base_year + 2))
                    contracts = [f"{root_symbol}{month_code}{str(y)[-2:]}" for y in years]
        else:
            print(f"[WARN] No data to check expiry for {latest_symbol}.")

        print(f"Final contract list for download: {contracts}")

        # Download and compile all contract data
        full_df = pd.DataFrame()
        for symbol in contracts:
            print(f"Fetching data for: {symbol}")
            df = load_commodity_data_py(symbol, start_date, end_date)
            if df.empty:
                print(f"[INFO] Skipping {symbol} due to empty data.")
                continue

            if "Date" not in df.columns or "Close" not in df.columns:
                print(f"[ERROR] Required columns missing in {symbol}. Columns: {df.columns.tolist()}")
                continue

            df = df[["Date", "Close"]].copy()
            df["Symbol"] = symbol
            df["Date"] = pd.to_datetime(df["Date"])
            df.sort_values("Date", inplace=True)
            df = df.tail(252)
            full_df = pd.concat([full_df, df], ignore_index=True)
            print(f"[INFO] Added {symbol}: {df.shape[0]} rows")

        print(f"[SUCCESS] Total combined rows: {full_df.shape[0]}")
        return full_df
    except Exception as e:
        print(f"[CRITICAL] Failed to build rolling data: {type(e).__name__} - {e}")
        return pd.DataFrame()

def main():
    symbol_input = "/HOF25"
    start_date = pd.to_datetime("2010-01-01").tz_localize("UTC")
    end_date = pd.to_datetime("2025-12-31").tz_localize("UTC")

    print("=== Starting main ===")
    df = build_rolling_contract_data(symbol_input, start_date, end_date)

    if not df.empty:
        print("✅ Data loaded successfully!")
        df.to_csv("test.csv", index=False)
        print("✅ Saved to test.csv")
    else:
        print("❌ No data returned. Please check the symbol or date range.")

if __name__ == "__main__":
    main()
