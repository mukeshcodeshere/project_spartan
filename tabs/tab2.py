# tab2.py

import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

def render_tab2(tab2, merged_data, rolling_window, chart_height, COLORS, group_A_name, group_B_name):
    with tab2:
        st.markdown('<div class="section-header">🔄 Correlation Analysis</div>', unsafe_allow_html=True)

        # Ensure the necessary columns exist
        if group_A_name not in merged_data.columns or group_B_name not in merged_data.columns:
            st.warning("Selected commodities are not in the dataset.")
            return

        # Calculate rolling statistics
        merged_data['RollingMean_A'] = merged_data[group_A_name].rolling(window=rolling_window).mean()
        merged_data['RollingMean_B'] = merged_data[group_B_name].rolling(window=rolling_window).mean()
        merged_data['RollingStd_A'] = merged_data[group_A_name].rolling(window=rolling_window).std()
        merged_data['RollingStd_B'] = merged_data[group_B_name].rolling(window=rolling_window).std()
        merged_data['Rolling_Correlation'] = merged_data[group_A_name].rolling(window=rolling_window).corr(merged_data[group_B_name])

        # Drop NaNs created by rolling calculations
        rolling_data = merged_data.dropna(subset=[
            'RollingMean_A', 'RollingMean_B', 'Rolling_Correlation'
        ])

        col1, col2 = st.columns(2)

        # Rolling correlation plot
        with col1:
            st.markdown(f"### Rolling {rolling_window}-Day Correlation")
            fig, ax = plt.subplots(figsize=(10, chart_height / 100))
            ax.plot(rolling_data['Date'], rolling_data['Rolling_Correlation'], color='#ff7f0e', linewidth=2)
            ax.axhline(y=0, color='white', linestyle='--', alpha=0.5)
            ax.axhline(y=0.5, color='green', linestyle=':', alpha=0.5)
            ax.axhline(y=-0.5, color='red', linestyle=':', alpha=0.5)
            ax.set_xlabel('Date', fontsize=12)
            ax.set_ylabel('Correlation Coefficient', fontsize=12)
            ax.set_title('Rolling Correlation Between Assets', fontsize=14, pad=20)
            ax.set_ylim(-1, 1)
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
            plt.xticks(rotation=45)
            fig.tight_layout()
            st.pyplot(fig)

        # Rolling volatility plot
        with col2:
            st.markdown(f"### Rolling {rolling_window}-Day Volatility")
            fig, ax = plt.subplots(figsize=(10, chart_height / 100))
            ax.plot(rolling_data['Date'], rolling_data['RollingStd_A'], color=COLORS.get("commodity1", "#1f77b4"), linewidth=2, label=group_A_name)
            ax.plot(rolling_data['Date'], rolling_data['RollingStd_B'], color=COLORS.get("commodity2", "#ff7f0e"), linewidth=2, label=group_B_name)
            ax.set_xlabel('Date', fontsize=12)
            ax.set_ylabel('Standard Deviation', fontsize=12)
            ax.set_title('Volatility Comparison', fontsize=14, pad=20)
            ax.legend(loc='upper left', frameon=True)
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
            plt.xticks(rotation=45)
            fig.tight_layout()
            st.pyplot(fig)
