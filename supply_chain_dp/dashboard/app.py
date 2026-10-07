"""
Streamlit dashboard for supply chain cost optimization.
"""

import streamlit as st
import requests
import pandas as pd
import os
from typing import Dict, Any

# Configure page
st.set_page_config(
    page_title="Supply Chain Optimizer",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Get API URL from environment variable with default
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

st.title("📦 Supply Chain Cost Optimization Engine")
st.markdown("Optimize production, inventory, and transportation costs using **Dynamic Programming**.")

# Sidebar for parameters
with st.sidebar:
    st.header("Simulation Parameters")
    initial_inv = st.number_input("Initial Inventory", value=20, min_value=0)
    warehouse_cap = st.number_input("Warehouse Capacity", value=100, min_value=1)

    # Default data from README
    default_data = pd.DataFrame({
        "Month": ["January", "February", "March", "April", "May", "June"],
        "Demand": [80, 100, 130, 90, 140, 100],
        "Capacity": [120, 120, 120, 120, 150, 150],
        "Prod Cost": [10, 11, 9, 13, 10, 14],
        "Transport Cost": [2, 2, 3, 2, 2, 3],
        "Holding Cost": [1, 1, 1, 2, 2, 2]
    })

    st.subheader("Monthly Planning Data")
    edited_df = st.data_editor(
        default_data,
        num_rows="fixed",
        use_container_width=True
    )

# Main content area
col1, col2 = st.columns([1, 1])

with col1:
    st.header("Optimization Results")
    if st.button("Run Optimization", type="primary", use_container_width=True):
        payload = {
            "months": edited_df["Month"].tolist(),
            "demands": edited_df["Demand"].tolist(),
            "prod_capacities": edited_df["Capacity"].tolist(),
            "prod_costs": edited_df["Prod Cost"].tolist(),
            "transport_costs": edited_df["Transport Cost"].tolist(),
            "holding_costs": edited_df["Holding Cost"].tolist(),
            "initial_inventory": int(initial_inv),
            "warehouse_capacity": int(warehouse_cap)
        }

        try:
            with st.spinner("Running optimization..."):
                res = requests.post(f"{API_URL}/api/v1/optimize", json=payload)

            if res.status_code == 200:
                data = res.json()

                if data["status"] == "success":
                    # Display costs in metrics
                    st.subheader("Cost Comparison")
                    cost_col1, cost_col2, cost_col3 = st.columns(3)

                    with cost_col1:
                        st.metric(
                            label="DP Optimal Cost",
                            value=f"₹{data['dp_result']['total_cost']:.2f}"
                        )

                    with cost_col2:
                        st.metric(
                            label="Naive Cost",
                            value=f"₹{data['naive_result']['total_cost']:.2f}",
                            delta=f"-{data['savings_vs_naive']:.1f}%" if data['savings_vs_naive'] > 0 else f"+{abs(data['savings_vs_naive']):.1f}%"
                        )

                    with cost_col3:
                        st.metric(
                            label="Greedy Cost",
                            value=f"₹{data['greedy_result']['total_cost']:.2f}",
                            delta=f"-{data['savings_vs_greedy']:.1f}%" if data['savings_vs_greedy'] > 0 else f"+{abs(data['savings_vs_greedy']):.1f}%"
                        )

                    # Display DP schedule
                    st.subheader("Optimal Production Schedule (DP)")
                    result_df = pd.DataFrame(data["dp_result"]["schedule"])
                    st.dataframe(result_df, use_container_width=True, hide_index=True)

                    # Charts
                    st.subheader("Production vs Demand vs Inventory")
                    chart_data = result_df.set_index("month")[["demand", "optimal_production", "ending_inventory"]]
                    st.line_chart(chart_data)

                    # Strategy comparison chart
                    st.subheader("Strategy Cost Comparison")
                    strategy_data = pd.DataFrame({
                        "Strategy": ["Dynamic Programming", "Naive", "Greedy"],
                        "Total Cost": [
                            data["dp_result"]["total_cost"],
                            data["naive_result"]["total_cost"],
                            data["greedy_result"]["total_cost"]
                        ]
                    })
                    st.bar_chart(strategy_data.set_index("Strategy"))

                    # Download CSV
                    csv = result_df.to_csv(index=False)
                    st.download_button(
                        label="Download Schedule as CSV",
                        data=csv,
                        file_name="supply_chain_schedule.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                else:
                    st.error(f"Unexpected response: {data}")
            else:
                st.error(f"Backend error: {res.status_code} - {res.text}")

        except requests.exceptions.ConnectionError:
            st.error(f"Connection failed: Unable to connect to {API_URL}. Make sure the FastAPI backend is running.")
        except Exception as e:
            st.error(f"An error occurred: {e}")

with col2:
    st.header("Instructions")
    st.markdown("""
    1. **Adjust parameters** in the sidebar:
       - Initial Inventory: Starting stock levels
       - Warehouse Capacity: Maximum storage capability
       - Monthly Data: Demand, capacity, and cost parameters for each month

    2. **Click "Run Optimization"** to compute:
       - Dynamic Programming (DP) solution: Globally optimal
       - Naive baseline: Produce exactly to meet demand each period
       - Greedy baseline: Produce more in low-cost periods

    3. **View results**:
       - Cost comparison metrics showing savings percentages
       - Detailed production schedule table
       - Charts comparing production, demand, and inventory levels
       - Strategy cost comparison bar chart

    4. **Download results** as CSV for further analysis

    **Note**: All costs are in Indian Rupees (₹) as per the sample data.
    """)

    st.header("About")
    st.info("""
    This application implements a Dynamic Programming approach to supply chain optimization.
    The DP algorithm evaluates all feasible inventory states to find the globally optimal
    production plan that minimizes total costs while respecting capacity constraints.
    """)

# Footer
st.divider()
st.caption("Supply Chain Cost Optimization Engine • Built with Streamlit and FastAPI")