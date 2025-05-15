import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

def render_tab3(merged_data, instruments, meta_A_month_int):
    st.markdown('<div class="section-header">📈 Trading Period Seasonal Analysis (Backward Fill)</div>', unsafe_allow_html=True)

    merged_data['Date'] = pd.to_datetime(merged_data['Date'], errors='coerce')
    merged_data = merged_data.dropna(subset=['Date'])
    merged_data['DayOfYear'] = merged_data['Date'].dt.dayofyear
    merged_data['Year'] = merged_data['Date'].dt.year

    month_ranges = {
        "Jan": (1, 31), "Feb": (32, 59), "Mar": (60, 90), "Apr": (91, 120),
        "May": (121, 151), "Jun": (152, 181), "Jul": (182, 212), "Aug": (213, 243),
        "Sep": (244, 273), "Oct": (274, 304), "Nov": (305, 334), "Dec": (335, 366)
    }

    month_int_to_abbr = {
        1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr",
        5: "May", 6: "Jun", 7: "Jul", 8: "Aug",
        9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"
    }

    starting_month = month_int_to_abbr.get(meta_A_month_int, None)
    if starting_month is None:
        st.error(f"Invalid month integer: {meta_A_month_int}")
        return

    with st.sidebar.expander("Seasonal Analysis Settings", expanded=False):
        all_years = sorted(set(merged_data['Year']))
        selected_years = st.multiselect("Select years to display:", all_years, default=all_years)
        exclude_months = st.multiselect("Exclude months:", list(month_ranges.keys()), default=[])

    excluded_days = set()
    for month in exclude_months:
        start, end = month_ranges[month]
        excluded_days.update(range(start, end + 1))

    def prepare_seasonal_pivot(df, value_column):
        df = df[['DayOfYear', 'Year', value_column]].dropna()
        if df.empty:
            return None

        pivot = df.pivot_table(index='DayOfYear', columns='Year', values=value_column, aggfunc='mean')
        pivot = pivot.sort_index(axis=1)

        full_index = pd.Index(range(1, 367), name='DayOfYear')
        pivot = pivot.reindex(full_index)

        # Backward fill missing data
        pivot = pivot.fillna(method='bfill')

        return pivot

    def filter_pivot(pivot):
        if pivot is None or pivot.empty:
            return None
        pivot = pivot.loc[~pivot.index.isin(excluded_days)]
        pivot = pivot[selected_years] if selected_years else pivot
        return pivot

    def create_seasonal_plot(df, title):
        if df is None or df.empty:
            st.warning(f"No data available for {title}")
            return

        start_day = month_ranges[starting_month][0]

        shifted_x = []
        for day in df.index:
            if day >= start_day:
                sx = day - start_day + 1
            else:
                sx = (366 - start_day + 1) + day
            shifted_x.append(sx)

        shifted_df = df.copy()
        shifted_df['shifted_x'] = shifted_x
        shifted_df = shifted_df.set_index('shifted_x')
        shifted_df = shifted_df.sort_index()

        fig1, ax1 = plt.subplots(figsize=(7, 4))
        for col in shifted_df.columns:
            ax1.plot(shifted_df.index, shifted_df[col], label=str(col))

        months = list(month_ranges.keys())
        start_month_idx = months.index(starting_month)
        shifted_month_order = months[start_month_idx:] + months[:start_month_idx]

        xticks = []
        xlabels = []
        bold_labels = []
        current_month_abbr = month_int_to_abbr.get(datetime.now().month, None)

        for month in shifted_month_order:
            original_start = month_ranges[month][0]
            if original_start >= start_day:
                sx = original_start - start_day + 1
            else:
                sx = (366 - start_day + 1) + original_start

            if sx in shifted_df.index:
                xticks.append(sx)
                xlabels.append(month)
                bold_labels.append(month == current_month_abbr)

        ax1.set_xticks(xticks)
        ax1.set_xticklabels(xlabels)

        for label, bold in zip(ax1.get_xticklabels(), bold_labels):
            if bold:
                label.set_fontweight('bold')

        ax1.set_title(title)
        ax1.set_xlabel("Month")
        ax1.set_ylabel("Value")
        ax1.legend(title="Year")
        ax1.grid(True)
        st.pyplot(fig1)

        values = shifted_df.values.flatten()
        values = values[~np.isnan(values)]

        if len(values) > 0:
            st.subheader("📊 Value Distribution")
            fig2, ax2 = plt.subplots(figsize=(7, 4))
            sns.histplot(values, kde=True, bins=30, ax=ax2, color='#F95D6A', edgecolor='white')
            ax2.set_title(f"{title} - Value Distribution")
            ax2.set_xlabel("Value")
            ax2.set_ylabel("Frequency")
            ax2.grid(True)
            st.pyplot(fig2)

    all_tabs = instruments + ['Spread']
    tabs = st.tabs(all_tabs)

    for i, name in enumerate(instruments):
        with tabs[i]:
            st.subheader(f"{name} Seasonality")
            pivot = prepare_seasonal_pivot(merged_data, name)
            filtered = filter_pivot(pivot)
            create_seasonal_plot(filtered, f"{name} Daily Seasonality")

    with tabs[-1]:
        st.subheader("Spread Seasonality")
        if 'Spread' not in merged_data.columns:
            st.warning("No 'Spread' column found in data.")
            return
        pivot = prepare_seasonal_pivot(merged_data, 'Spread')
        filtered = filter_pivot(pivot)
        create_seasonal_plot(filtered, "Spread Daily Seasonality")
