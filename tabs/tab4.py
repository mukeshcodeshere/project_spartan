import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

def render_tab4(merged_data, group_A_name, group_B_name, var_confidence, COLORS):
    st.markdown('<div class="section-header">⚠️ Risk Analysis</div>', unsafe_allow_html=True)

    st.write(merged_data)
    # Correct dynamic column references based on input names
    return_col_A = "Return_A"  # Group A's returns column
    return_col_B = "Return_B"  # Group B's returns column
    return_col_spread = "Return_Spread"  # Spread returns column


    required_columns = [return_col_A, return_col_B, return_col_spread]
    for col in required_columns:
        if col not in merged_data.columns:
            st.error(f"Missing required column: {col}. Please check your data.")
            return

    # Drop rows where necessary returns are NaN
    returns_data = merged_data.dropna(subset=[return_col_A, return_col_B, return_col_spread])

    if returns_data.empty:
        st.error("No valid data for the risk analysis.")
        return

    # Calculate Value at Risk (VaR)
    var_pct = (100 - var_confidence) / 100
    var_a = np.percentile(returns_data[return_col_A], var_pct * 100) * 100
    var_b = np.percentile(returns_data[return_col_B], var_pct * 100) * 100
    var_spread = np.percentile(returns_data[return_col_spread], var_pct * 100) * 100

    # Display Value at Risk (VaR)
    st.markdown("### Value at Risk (VaR)")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(f"{group_A_name} VaR ({var_confidence}%)", f"{var_a:.2f}%", delta_color="inverse")
    with col2:
        st.metric(f"{group_B_name} VaR ({var_confidence}%)", f"{var_b:.2f}%", delta_color="inverse")
    with col3:
        st.metric(f"Spread VaR ({var_confidence}%)", f"{var_spread:.2f}%", delta_color="inverse")

    # Plot return distributions with VaR
    st.markdown("### Return Distributions with VaR")
    col1, col2, col3 = st.columns(3)

    def plot_return_distribution(ax, data, title, color, var_value):
        sns.histplot(data * 100, kde=True, color=color, bins=50, ax=ax)
        ax.axvline(var_value, color='red', linestyle='--', linewidth=2, label=f'VaR ({var_confidence}%): {var_value:.2f}%')
        ax.set_xlabel('Daily Return (%)')
        ax.set_ylabel('Frequency')
        ax.set_title(title)
        ax.legend()

    with col1:
        fig, ax = plt.subplots(figsize=(8, 4))
        plot_return_distribution(ax, returns_data[return_col_A], f'{group_A_name} Returns', COLORS["commodity1"], var_a)
        st.pyplot(fig)

    with col2:
        fig, ax = plt.subplots(figsize=(8, 4))
        plot_return_distribution(ax, returns_data[return_col_B], f'{group_B_name} Returns', COLORS["commodity2"], var_b)
        st.pyplot(fig)

    with col3:
        fig, ax = plt.subplots(figsize=(8, 4))
        plot_return_distribution(ax, returns_data[return_col_spread], 'Spread Returns', COLORS["spread"], var_spread)
        st.pyplot(fig)

    # Annualized volatility
    volatility_a = returns_data[return_col_A].std() * np.sqrt(252) * 100
    volatility_b = returns_data[return_col_B].std() * np.sqrt(252) * 100
    volatility_spread = returns_data[return_col_spread].std() * np.sqrt(252) * 100

    # Display volatility
    st.markdown("### Volatility (Annualized)")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(f"{group_A_name} Volatility", f"{volatility_a:.2f}%")
    with col2:
        st.metric(f"{group_B_name} Volatility", f"{volatility_b:.2f}%")
    with col3:
        st.metric("Spread Volatility", f"{volatility_spread:.2f}%")

    # Maximum drawdown calculation
    def calculate_max_drawdown(returns):
        cumulative = (1 + returns).cumprod()
        peak = cumulative.expanding(min_periods=1).max()
        drawdown = (cumulative - peak) / peak
        return drawdown.min() * 100

    max_dd_a = calculate_max_drawdown(returns_data[return_col_A])
    max_dd_b = calculate_max_drawdown(returns_data[return_col_B])
    max_dd_spread = calculate_max_drawdown(returns_data[return_col_spread])

    # Display max drawdown
    st.markdown("### Maximum Drawdown")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(f"{group_A_name} Max Drawdown", f"{max_dd_a:.2f}%")
    with col2:
        st.metric(f"{group_B_name} Max Drawdown", f"{max_dd_b:.2f}%")
    with col3:
        st.metric("Spread Max Drawdown", f"{max_dd_spread:.2f}%")

