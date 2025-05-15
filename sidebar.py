import streamlit as st
from datetime import datetime, date
import pandas as pd

def load_presets_from_csv():
    df = pd.read_csv("PriceAnalyzerIn.csv")
    presets = []
    for _, row in df.iterrows():
        presets.append({
            'name': row['Name'],
            'tickers': eval(row['tickerList']),
            'months': eval(row['contractMonthsList']),
            'weights': eval(row['weightsList']),
            'conversions': eval(row['convList']),
            'description': row['desc'],
            'group': row['group'],
            'region': row['region'],
            'months_code': ''.join(eval(row['contractMonthsList']))  # Join month codes
        })
    return presets

def show_sidebar(commodity_categories):
    with st.sidebar:
        # New selection to toggle between presets and manual input
        input_mode = st.radio("Choose Input Mode", ["Preset", "Manual"])

        presets = load_presets_from_csv()  # Load presets regardless of mode
        selected_preset = None

        if input_mode == "Preset":
            # Hierarchical preset selection
            st.markdown("### 📚 Presets")
            
            # Extract unique groups, regions, and month combinations
            groups = sorted(set(p['group'] for p in presets))
            
            # First level: Group selection
            selected_group = st.selectbox("Select Group", groups)
            
            # Filter by selected group
            filtered_by_group = [p for p in presets if p['group'] == selected_group]
            regions = sorted(set(p['region'] for p in filtered_by_group))
            
            # Second level: Region selection
            selected_region = st.selectbox("Select Region", regions)
            
            # Filter by selected region
            filtered_by_region = [p for p in filtered_by_group if p['region'] == selected_region]
            month_codes = sorted(set(p['months_code'] for p in filtered_by_region))
            
            # Third level: Month combination selection
            month_display = {code: f"Contract: {code}" for code in month_codes}
            selected_month_code = st.selectbox("Select Contract Month-Month", options=month_codes, format_func=lambda x: month_display[x])
            
            # Filter by selected month code
            filtered_by_month = [p for p in filtered_by_region if p['months_code'] == selected_month_code]
            descriptions = [p['description'] for p in filtered_by_month]
            
            # Final level: Description selection
            selected_desc = st.selectbox("Select Spread", descriptions)
            
            # Get the fully selected preset
            selected_preset = next((p['description'] for p in filtered_by_month if p['description'] == selected_desc), None)
        else:
            # Manual input, so no preset is selected
            selected_preset = None

        st.markdown("### 🔍 User Inputs")

        def select_multiple_commodities(group_name):
            with st.expander(f"⚙️ Configure {group_name}", expanded=True):
                category = st.selectbox(
                    f"{group_name}: Exchange / Group",
                    sorted(commodity_categories.keys()),
                    key=f"{group_name}_category"
                )

                filtered_items = sorted(commodity_categories[category], key=lambda x: x[1])
                symbol_options = [f"{desc} ({symbol})" for symbol, desc in filtered_items]

                selected_labels = st.multiselect(
                    f"{group_name}: Select Instruments",
                    symbol_options,
                    key=f"{group_name}_symbols"
                )

                group = []
                if selected_labels:
                    st.markdown("##### ⚖️ Weights & ⚙️ Conversions")
                for label in selected_labels:
                    for symbol, desc in filtered_items:
                        if f"{desc} ({symbol})" == label:
                            full_label = f"[{category}] {desc} ({symbol})"
                            cols = st.columns([2, 1, 1])
                            with cols[0]:
                                st.markdown(f"**{desc} ({symbol})**")
                            with cols[1]:
                                weight = st.number_input(
                                    "Weight", min_value=-10.0, value=1.0, step=0.1,
                                    key=f"{group_name}_{symbol}_weight"
                                )
                            with cols[2]:
                                conversion = st.number_input(
                                    "Conversion", min_value=-10.0, value=1.0, step=0.1,
                                    key=f"{group_name}_{symbol}_conversion"
                                )
                            group.append({
                                "label": full_label,
                                "symbol": symbol,
                                "weight": weight,
                                "conversion": conversion
                            })
                return group

        group_A = select_multiple_commodities("Group A")
        group_B = select_multiple_commodities("Group B")

        st.markdown("### 📅 Date Range")
        col1, col2 = st.columns(2)
        with col1:
            start_date_input = st.date_input("Start date", value=date(2020, 1, 1), key="start_date")
        with col2:
            end_date_input = st.date_input("End date", value=date(2025, 12, 31), key="end_date")

        # Convert to datetime.datetime
        start_date = datetime.combine(start_date_input, datetime.min.time())
        end_date = datetime.combine(end_date_input, datetime.min.time())

        if start_date > end_date:
            st.error("❌ Start date must be before end date.")
            st.stop()

        # Other parameters
        st.markdown("### ⚙️ Advanced Settings")
        rolling_window = st.slider("Rolling Window Size", min_value=5, max_value=100, value=20, step=1)
        var_confidence = st.slider("VaR Confidence Level (%)", min_value=90, max_value=99, value=95, step=1)

        return group_A, group_B, start_date, end_date, rolling_window, var_confidence, 500, selected_preset, presets



# Enhanced color palette with distinct colors for different years
COLORS = {
    "commodity1": "#1f77b4",  # Blue
    "commodity2": "#2ca02c",  # Green
    "spread": "#ff7f0e",  # Orange
    "background": "#0e1117",
    "text": "#ffffff",
    "grid": "#2c2c2c",
    "highlight": "#e41a1c",  # Red
    "appended_data": "#9467bd",  # Purple
    "latest_data": "#d62728",  # Dark Red
    "historical_data": "#7f7f7f",  # Gray
    "year_colors": {
        2020: "#17becf",  # Cyan
        2021: "#bcbd22",  # Olive
        2022: "#8c564b",  # Brown
        2023: "#e377c2",  # Pink
        2024: "#aec7e8",  # Light Blue
        2025: "#98df8a",  # Light Green
        2026: "#ffbb78",  # Light Orange
        2027: "#f7b6d2",  # Light Pink
        2028: "#c5b0d5",  # Light Purple
        2029: "#c49c94",  # Light Brown
        2030: "#dbdb8d",  # Light Olive
    }
}