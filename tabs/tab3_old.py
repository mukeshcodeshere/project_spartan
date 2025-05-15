import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from scipy.stats import gaussian_kde

def render_tab3(merged_data, instruments, meta_A_month_int,list_of_input_instruments):
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
        pivot = pivot.bfill()

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

        # Shift day indices based on selected starting month
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

        # Create Plotly Line Chart
        fig = go.Figure()
        for col in shifted_df.columns:
            fig.add_trace(go.Scatter(
                x=shifted_df.index,
                y=shifted_df[col],
                mode='lines',
                name=str(col),
                hovertemplate=f"Year: {col}<br>Day: %{{x}}<br>Value: %{{y:.2f}}<extra></extra>"
            ))

        # Set x-axis labels to months
        months = list(month_ranges.keys())
        start_month_idx = months.index(starting_month)
        shifted_month_order = months[start_month_idx:] + months[:start_month_idx]

        xticks = []
        xlabels = []
        current_month_abbr = month_int_to_abbr.get(datetime.now().month, None)

        for month in shifted_month_order:
            original_start = month_ranges[month][0]
            if original_start >= start_day:
                sx = original_start - start_day + 1
            else:
                sx = (366 - start_day + 1) + original_start
            xticks.append(sx)
            xlabels.append(f"<b>{month}</b>" if month == current_month_abbr else month)

        fig.update_layout(
            title=title,
            xaxis=dict(
                tickmode='array',
                tickvals=xticks,
                ticktext=xlabels,
                title='Month'
            ),
            yaxis_title='Value',
            legend_title='Year',
            height=400,
            margin=dict(t=40, b=40),
        )

        st.plotly_chart(fig, use_container_width=True)

        # Distribution (KDE) plot using Plotly
        values = shifted_df.dropna().values.flatten()
        values = values[~np.isnan(values)]

        if len(values) > 1:
            st.subheader("📈 Probability Density (KDE)")

            kde = gaussian_kde(values)
            x_vals = np.linspace(min(values), max(values), 500)
            y_vals = kde(x_vals)

            fig_kde = go.Figure()
            fig_kde.add_trace(go.Scatter(
                x=x_vals,
                y=y_vals,
                mode='lines',
                fill='tozeroy',
                line=dict(color='#F95D6A'),
                hovertemplate="Value: %{x:.2f}<br>Density: %{y:.5f}<extra></extra>"
            ))

            fig_kde.update_layout(
                title=f"{title} - Probability Density",
                xaxis_title="Value",
                yaxis_title="Density",
                height=300,
                margin=dict(t=40, b=40),
            )

            st.plotly_chart(fig_kde, use_container_width=True)

    # Make 'Spread' the first tab, followed by all instruments
    all_tabs = ['Spread'] + instruments
    tabs = st.tabs(all_tabs)

    # First tab: Spread
    with tabs[0]:
        st.subheader("Spread Seasonality")
        if 'Spread' not in merged_data.columns:
            st.warning("No 'Spread' column found in data.")
            return
        pivot = prepare_seasonal_pivot(merged_data, 'Spread')
        filtered = filter_pivot(pivot)
        create_seasonal_plot(filtered, "Spread Daily Seasonality")

    # Other tabs: instruments
    for i, name in enumerate(instruments):
        with tabs[i + 1]:  # offset by 1 because Spread is now first
            st.subheader(f"{name} Seasonality")
            pivot = prepare_seasonal_pivot(merged_data, name)
            filtered = filter_pivot(pivot)
            create_seasonal_plot(filtered, f"{name} Daily Seasonality")

