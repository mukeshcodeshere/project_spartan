# tab1.py

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns

def render_tab1(merged_data, group_A_name, group_B_name, chart_height, COLORS):
    st.markdown('<div class="section-header">🛢️ Price Overview</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Descriptive Statistics")
        group_A_stats = merged_data[group_A_name].describe().round(2)
        group_B_stats = merged_data[group_B_name].describe().round(2)
        spread_stats = merged_data['Spread'].describe().round(2)

        stats_df = pd.DataFrame({
            group_A_name: group_A_stats,
            group_B_name: group_B_stats,
            'Spread': spread_stats
        })

        st.dataframe(stats_df, height=300, use_container_width=True)

        latest_data = merged_data.iloc[-1]

        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric(
                label=group_A_name, 
                value=f"${latest_data[group_A_name]:.2f}",
                delta=f"{latest_data['Return_A']*100:.2f}%" if not pd.isna(latest_data['Return_A']) else None
            )
        with col_b:
            st.metric(
                label=group_B_name, 
                value=f"${latest_data[group_B_name]:.2f}",
                delta=f"{latest_data['Return_B']*100:.2f}%" if not pd.isna(latest_data['Return_B']) else None
            )
        with col_c:
            st.metric(
                label="Latest Spread", 
                value=f"${latest_data['Spread']:.2f}",
                delta=f"{latest_data['Return_Spread']*100:.2f}%" if not pd.isna(latest_data['Return_Spread']) else None
            )

    with col2:
        st.markdown("### Historical Price Comparison")
        fig, ax = plt.subplots(figsize=(10, chart_height/100))

        # Plot group totals
        ax.plot(merged_data['Date'], merged_data[group_A_name], 
                color=COLORS.get("commodity1", "#1f77b4"), linewidth=2, label=group_A_name)
        ax.plot(merged_data['Date'], merged_data[group_B_name], 
                color=COLORS.get("commodity2", "#ff7f0e"), linewidth=2, label=group_B_name)

        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel('Price ($)', fontsize=12)
        ax.set_title(f'{group_A_name} vs {group_B_name} Prices', fontsize=14, pad=20)
        ax.legend(loc='upper left', frameon=True)

        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
        plt.xticks(rotation=45)
        ax.grid(True, linestyle='--', alpha=0.7)

        # Add spread on secondary axis
        ax2 = ax.twinx()
        ax2.plot(merged_data['Date'], merged_data['Spread'], 
                color=COLORS.get("spread", "#2ca02c"), linewidth=1.5, linestyle='--', label='Spread')
        ax2.set_ylabel('Spread ($)', fontsize=12)
        ax2.tick_params(axis='y')

        lines1, labels1 = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax.legend(lines1 + lines2, labels1 + labels2, loc='upper left', frameon=True)

        fig.tight_layout()
        st.pyplot(fig)

    # Group constituents section - NEW SECTION
    st.markdown('<div class="section-header">🧩 Group Constituents</div>', unsafe_allow_html=True)
    
    # Get all columns that aren't utility columns (like Date, Spread, etc.)
    group_columns = [col for col in merged_data.columns 
                     if col not in ['Date', 'Year', 'Month', 'MonthName', 'DayOfWeek', 'DayName', 
                                   'Group A', 'Group B', 'Spread', 'Spread_Ratio'] 
                     and not col.startswith('Return_')]
    
    # Split into Group A and Group B assets
    a_assets = [col for col in group_columns if f"Return_{col}" in merged_data.columns 
                and col != group_A_name and col != group_B_name]
    
    if a_assets:
        st.markdown(f"### Constituent Assets")
        tabs = st.tabs([f"Asset Details", f"Performance Comparison"])
        
        with tabs[0]:
            # Display individual asset metrics
            metrics_cols = st.columns(min(4, len(a_assets)))
            for i, asset in enumerate(a_assets):
                with metrics_cols[i % len(metrics_cols)]:
                    latest_price = latest_data[asset]
                    latest_return = latest_data.get(f"Return_{asset}", None)
                    st.metric(
                        label=asset,
                        value=f"${latest_price:.2f}",
                        delta=f"{latest_return*100:.2f}%" if latest_return is not None and not pd.isna(latest_return) else None
                    )
        
        with tabs[1]:
            # Create line chart showing all assets
            fig, ax = plt.subplots(figsize=(10, chart_height/100))
            
            # Plot each asset with a different color
            for i, asset in enumerate(a_assets):
                color = plt.cm.tab10(i % 10)  # Cycle through 10 colors
                ax.plot(merged_data['Date'], merged_data[asset], linewidth=1.5, label=asset, alpha=0.8, color=color)
            
            ax.set_xlabel('Date', fontsize=12)
            ax.set_ylabel('Price ($)', fontsize=12)
            ax.set_title('Individual Asset Performance', fontsize=14, pad=20)
            ax.legend(loc='upper left', frameon=True, ncol=min(3, len(a_assets)))
            
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
            plt.xticks(rotation=45)
            ax.grid(True, linestyle='--', alpha=0.7)
            
            fig.tight_layout()
            st.pyplot(fig)

    st.markdown('<div class="section-header">📊 Price Distribution Analysis</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Price Distributions")
        fig, ax = plt.subplots(figsize=(10, chart_height/100))
        sns.kdeplot(data=merged_data, x=group_A_name, fill=True, color=COLORS.get("commodity1", "#1f77b4"), alpha=0.6, label=group_A_name)
        sns.kdeplot(data=merged_data, x=group_B_name, fill=True, color=COLORS.get("commodity2", "#ff7f0e"), alpha=0.6, label=group_B_name)
        ax.set_xlabel('Price ($)', fontsize=12)
        ax.set_ylabel('Density', fontsize=12)
        ax.set_title('Price Distribution Density', fontsize=14, pad=20)
        ax.legend(loc='upper right', frameon=True)
        fig.tight_layout()
        st.pyplot(fig)

    with col2:
        st.markdown("### Spread Distribution")
        fig, ax = plt.subplots(figsize=(10, chart_height/100))
        sns.histplot(data=merged_data, x='Spread', bins=30, kde=True, color=COLORS.get("spread", "#2ca02c"), alpha=0.7)
        plt.axvline(merged_data['Spread'].mean(), color='white', linestyle='dashed', linewidth=2, label=f'Mean: {merged_data["Spread"].mean():.2f}')
        plt.axvline(merged_data['Spread'].median(), color='red', linestyle='dotted', linewidth=2, label=f'Median: {merged_data["Spread"].median():.2f}')
        ax.set_xlabel('Spread ($)', fontsize=12)
        ax.set_ylabel('Frequency', fontsize=12)
        ax.set_title('Spread Distribution', fontsize=14, pad=20)
        ax.legend(loc='upper right', frameon=True)
        fig.tight_layout()
        st.pyplot(fig)

    # st.markdown('<div class="section-header">📏 Price Ratio Analysis</div>', unsafe_allow_html=True)
    # fig, ax = plt.subplots(figsize=(10, chart_height/100))
    # ax.plot(merged_data['Date'], merged_data['Spread_Ratio'], color=COLORS.get("spread", "#2ca02c"), linewidth=2)
    # ax.set_xlabel('Date', fontsize=12)
    # ax.set_ylabel(f'{group_B_name} / {group_A_name}', fontsize=12)
    # ax.set_title(f'{group_B_name} to {group_A_name} Ratio', fontsize=14, pad=20)
    # ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    # ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    # plt.xticks(rotation=45)
    # ax.axhline(y=1, color='red', linestyle='--', alpha=0.7)

    # # Add annotations for max and min ratio
    # if not merged_data.empty:
    #     max_ratio_idx = merged_data['Spread_Ratio'].idxmax()
    #     min_ratio_idx = merged_data['Spread_Ratio'].idxmin()
        
    #     ax.annotate(f'Max: {merged_data.loc[max_ratio_idx, "Spread_Ratio"]:.2f}',
    #                 xy=(merged_data.loc[max_ratio_idx, 'Date'], merged_data.loc[max_ratio_idx, 'Spread_Ratio']),
    #                 xytext=(0, 20), textcoords='offset points',
    #                 arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=.2', color='white'),
    #                 color='white')

    #     ax.annotate(f'Min: {merged_data.loc[min_ratio_idx, "Spread_Ratio"]:.2f}',
    #                 xy=(merged_data.loc[min_ratio_idx, 'Date'], merged_data.loc[min_ratio_idx, 'Spread_Ratio']),
    #                 xytext=(0, -20), textcoords='offset points',
    #                 arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=.2', color='white'),
    #                 color='white')

    fig.tight_layout()
    st.pyplot(fig)