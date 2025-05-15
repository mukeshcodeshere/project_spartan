import win32com.client
import pythoncom
import pandas as pd
from datetime import datetime


def connect_to_mv_com_server(server: str = "GCC025", password: str = "c58zYaAS"):
    """Establish connection to MV COM server."""
    try:
        pythoncom.CoInitialize()
        con = win32com.client.Dispatch("Mv.Connectivity.ComClient.ServerConnection")
        con.Connect(server, password)
        return con
    except Exception as e:
        print(f"Error connecting to MV COM server: {e}")
        return None


def fetch_daily_data(con, symbol: str, start_date: datetime, end_date: datetime):
    """Fetch daily data for the given symbol and date range."""
    try:
        daily_data_raw = con.GetDailyRange(symbol=symbol, From=start_date, to=end_date)
        return list(daily_data_raw)
    except Exception as e:
        print(f"Error fetching daily data: {e}")
        return []


def inspect_com_object(obj):
    """Prints non-callable attributes of a COM object."""
    for attr in dir(obj):
        if not attr.startswith('_'):
            try:
                value = getattr(obj, attr)
                if not callable(value):
                    print(f"{attr}: {value}")
            except Exception as e:
                print(f"{attr}: Could not retrieve ({e})")


def daily_data_to_dataframe(daily_data):
    """Converts list of daily COM data objects to a pandas DataFrame."""
    data = []
    for day in daily_data:
        try:
            row = {
                "Date": pd.to_datetime(getattr(day, "StringDateTime", None)),
                "Open": getattr(day, "Open", None),
                "High": getattr(day, "High", None),
                "Low": getattr(day, "Low", None),
                "Close": getattr(day, "Close", None),
                "Volume": getattr(day, "Volume", None),
            }
            data.append(row)
        except Exception as e:
            print(f"Error processing record: {e}")
    return pd.DataFrame(data)


def get_mv_data(symbol: str, start_date: datetime, end_date: datetime, inspect_first: bool = False):
    """Safely retrieve and process MV daily data."""
    con = connect_to_mv_com_server()
    if con is None:
        raise RuntimeError("Failed to connect to MV COM server.")

    try:
        daily_data = fetch_daily_data(con, symbol, start_date, end_date)
    except Exception as e:
        raise RuntimeError(f"Failed to fetch data: {e}")

    if not daily_data:
        raise ValueError("No data returned. This could be due to an invalid symbol or temporary server issue.")

    if inspect_first:
        try:
            inspect_com_object(daily_data[0])
        except Exception:
            pass  # Skip inspection errors silently

    try:
        df = daily_data_to_dataframe(daily_data)
        return df
    except Exception as e:
        raise RuntimeError(f"Failed to convert daily data to DataFrame: {e}")
