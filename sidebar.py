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
            'months_code': ''.join(eval(row['contractMonthsList']))
        })
    return presets

def show_sidebar(commodity_categories):
    with st.sidebar:
        input_mode = st.radio("Choose Input Mode", ["Preset", "Manual"])
        presets = load_presets_from_csv()
        selected_preset = None

        if input_mode == "Preset":
            st.markdown("### 📚 Presets")
            groups = sorted(set(p['group'] for p in presets))
            selected_group = st.selectbox("Select Group", groups)
            filtered_by_group = [p for p in presets if p['group'] == selected_group]
            regions = sorted(set(p['region'] for p in filtered_by_group))
            selected_region = st.selectbox("Select Region", regions)
            filtered_by_region = [p for p in filtered_by_group if p['region'] == selected_region]
            month_codes = sorted(set(p['months_code'] for p in filtered_by_region))
            month_display = {code: f"Contract: {code}" for code in month_codes}
            selected_month_code = st.selectbox("Select Contract Month-Month", options=month_codes, format_func=lambda x: month_display[x])
            filtered_by_month = [p for p in filtered_by_region if p['months_code'] == selected_month_code]
            descriptions = [p['description'] for p in filtered_by_month]
            selected_desc = st.selectbox("Select Spread", descriptions)
            selected_preset = next((p['description'] for p in filtered_by_month if p['description'] == selected_desc), None)
            
            # Return preset data immediately without showing user inputs
            st.markdown("### 📅 Date Range")
            col1, col2 = st.columns(2)
            with col1:
                start_date_input = st.date_input("Start date", value=date(2020, 1, 1), key="start_date")
            with col2:
                end_date_input = st.date_input("End date", value=date(2025, 12, 31), key="end_date")

            start_date = datetime.combine(start_date_input, datetime.min.time())
            end_date = datetime.combine(end_date_input, datetime.min.time())

            if start_date > end_date:
                st.error("❌ Start date must be before end date.")
                st.stop()

            st.markdown("### ⚙️ Advanced Settings")
            rolling_window = st.slider("Rolling Window Size", min_value=5, max_value=100, value=20, step=1)
            var_confidence = st.slider("VaR Confidence Level (%)", min_value=90, max_value=99, value=95, step=1)

            # Return empty groups for preset mode
            return [], [], start_date, end_date, rolling_window, var_confidence, 500, selected_preset, presets

        else:  # Manual mode
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

            # ➕ New Manual Commodity Code Entry
            st.markdown("### ⌨️ Enter Commodity Codes Directly")
            st.info("Format: `Symbol Weight Conversion` per line. Example: `#ICEGCMMK25 1.0 1.0`")

            manual_group = st.radio("Apply manual entries to:", ["Group A", "Group B"], key="manual_group_choice")
            manual_input = st.text_area("Commodity Codes Input", height=150, key="manual_code_input")

            manual_lines = manual_input.strip().split('\n')
            for line in manual_lines:
                parts = line.strip().split()
                if len(parts) == 3:
                    symbol, weight_str, conv_str = parts
                    try:
                        weight = float(weight_str)
                        conversion = float(conv_str)
                        group = group_A if manual_group == "Group A" else group_B
                        group.append({
                            "label": f"[Manual] {symbol}",
                            "symbol": symbol,
                            "weight": weight,
                            "conversion": conversion
                        })
                    except ValueError:
                        st.warning(f"Invalid number format in line: `{line}`")
                elif line.strip():
                    st.warning(f"Invalid format in line: `{line}`")

            st.markdown("### 📅 Date Range")
            col1, col2 = st.columns(2)
            with col1:
                start_date_input = st.date_input("Start date", value=date(2020, 1, 1), key="start_date")
            with col2:
                end_date_input = st.date_input("End date", value=date(2025, 12, 31), key="end_date")

            start_date = datetime.combine(start_date_input, datetime.min.time())
            end_date = datetime.combine(end_date_input, datetime.min.time())

            if start_date > end_date:
                st.error("❌ Start date must be before end date.")
                st.stop()

            st.markdown("### ⚙️ Advanced Settings")
            rolling_window = st.slider("Rolling Window Size", min_value=5, max_value=100, value=20, step=1)
            var_confidence = st.slider("VaR Confidence Level (%)", min_value=90, max_value=99, value=95, step=1)

            return group_A, group_B, start_date, end_date, rolling_window, var_confidence, 500, selected_preset, presets

# Enhanced color palette
COLORS = {
    "commodity1": "#1f77b4",
    "commodity2": "#2ca02c",
    "spread": "#ff7f0e",
    "background": "#0e1117",
    "text": "#ffffff",
    "grid": "#2c2c2c",
    "highlight": "#e41a1c",
    "appended_data": "#9467bd",
    "latest_data": "#d62728",
    "historical_data": "#7f7f7f",
    "year_colors": {
        2020: "#17becf",
        2021: "#bcbd22",
        2022: "#8c564b",
        2023: "#e377c2",
        2024: "#aec7e8",
        2025: "#98df8a",
        2026: "#ffbb78",
        2027: "#f7b6d2",
        2028: "#c5b0d5",
        2029: "#c49c94",
        2030: "#dbdb8d",
    }
}