# 📦 Supply Chain Cost Optimization Engine (Dynamic Programming)

A Dynamic Programming (DP) based supply chain optimization system that computes the globally lowest-cost production, transportation, and inventory plan over a finite planning horizon. It has three parts: a modular Python optimization engine, a FastAPI backend, and an interactive Streamlit dashboard.

---

## 1. Project Overview

Supply chains must balance variable production costs, holding costs, and transportation expenses across multiple periods. Producing exactly to demand each period is rarely optimal because costs fluctuate from month to month.

This project uses a **Dynamic Programming** approach to evaluate every feasible state transition, find the best stockpiling strategy, and minimize total cumulative cost while respecting production and warehouse capacity limits.

---

## 2. Mathematical Model & DP Formulation

### Decision variables and parameters

| Symbol | Meaning |
| --- | --- |
| Pt | Production quantity in period t |
| It | Ending inventory after period t |
| Dt | Customer demand in period t |
| Kt | Maximum production capacity in period t |
| W | Maximum warehouse capacity |
| Cp(t) + Ctr(t) | Combined production and transportation cost per unit |
| Ch(t) | Inventory holding cost per unit in period t |

### Objective function

Minimize total cumulative cost:

```
min  Σ (t = 1..T)  [ (Cp(t) + Ctr(t)) · Pt  +  Ch(t) · It ]
```

### Constraints

- **Inventory balance:** `I_t = I_(t-1) + P_t − D_t`, so `P_t = D_t + I_t − I_(t-1)`
- **Production capacity:** `0 ≤ P_t ≤ K_t`
- **Warehouse capacity:** `0 ≤ I_t ≤ W`
- **Boundary conditions:** initial inventory `I_0 = 20`, required final inventory `I_T = 0`

### DP recurrence

```
DP[t][i] = min over 0 ≤ j ≤ W of
           DP[t-1][j] + (Cp(t) + Ctr(t)) · (D_t + i − j) + Ch(t) · i
```

Here `i` is the ending inventory of period `t`, `j` is the ending inventory of period `t−1`, and the transition is valid only when `0 ≤ D_t + i − j ≤ K_t`.

---

## 3. Sample Dataset & Baselines

The system ships with a 6-month planning horizon:

| Month | Demand (Dt) | Capacity (Kt) | Prod Cost (Cp) | Transport Cost (Ctr) | Holding Cost (Ch) |
| --- | --- | --- | --- | --- | --- |
| January | 80 | 120 | ₹10 | ₹2 | ₹1 |
| February | 100 | 120 | ₹11 | ₹2 | ₹1 |
| March | 130 | 120 | ₹9 | ₹3 | ₹1 |
| April | 90 | 120 | ₹13 | ₹2 | ₹2 |
| May | 140 | 150 | ₹10 | ₹2 | ₹2 |
| June | 100 | 150 | ₹14 | ₹3 | ₹2 |

### Strategy comparison

1. **Naive:** produces exactly what is needed each period after accounting for existing stock.
2. **Greedy:** prefers production in the locally cheapest periods.
3. **Dynamic Programming:** evaluates global state transitions to find the absolute minimum total cost.

---

## 4. System Architecture

- **Core engine:** Python with NumPy for the DP table and backtracking.
- **API layer:** FastAPI exposing a REST endpoint, `POST /api/v1/optimize`.
- **Presentation layer:** Streamlit dashboard for real-time parameter tuning, result tables, and charts.

---

## 5. Source Code

### 5.1 Backend optimization engine (`main.py`)

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import numpy as np

app = FastAPI(title="Supply Chain Cost Optimization API", version="1.0")

class SupplyChainInput(BaseModel):
    months: List[str]
    demands: List[float]
    prod_capacities: List[float]
    prod_costs: List[float]
    transport_costs: List[float]
    holding_costs: List[float]
    initial_inventory: int = 20
    warehouse_capacity: int = 100

@app.post("/api/v1/optimize")
def optimize_supply_chain(data: SupplyChainInput):
    T = len(data.demands)
    W = data.warehouse_capacity
    INF = float('inf')

    total_prod_costs = [p + tr for p, tr in zip(data.prod_costs, data.transport_costs)]

    DP = np.full((T + 1, W + 1), INF)
    parent = np.full((T + 1, W + 1), -1, dtype=int)

    DP[0][data.initial_inventory] = 0

    for t in range(1, T + 1):
        d = data.demands[t-1]
        k = data.prod_capacities[t-1]
        h = data.holding_costs[t-1]
        c_prod = total_prod_costs[t-1]

        for i in range(W + 1):
            min_cost = INF
            best_prev_j = -1
            for j in range(W + 1):
                p_t = d + i - j
                if 0 <= p_t <= k:
                    if DP[t-1][j] != INF:
                        cost = DP[t-1][j] + (c_prod * p_t) + (h * i)
                        if cost < min_cost:
                            min_cost = cost
                            best_prev_j = j
            DP[t][i] = min_cost
            parent[t][i] = best_prev_j

    min_total_cost = DP[T][0]
    if min_total_cost == INF:
        raise HTTPException(status_code=422, detail="No feasible plan under the given constraints.")

    # Backtracking reconstruction
    current_inv = 0
    inventory_sequence = [0] * (T + 1)
    inventory_sequence[T] = 0

    for t in range(T, 0, -1):
        prev_inv = parent[t][current_inv]
        inventory_sequence[t-1] = prev_inv
        current_inv = prev_inv

    optimal_production = []
    for t in range(T):
        p_t = data.demands[t] + inventory_sequence[t+1] - inventory_sequence[t]
        optimal_production.append(p_t)

    schedule = []
    for idx, m in enumerate(data.months):
        schedule.append({
            "month": m,
            "demand": data.demands[idx],
            "optimal_production": optimal_production[idx],
            "ending_inventory": inventory_sequence[idx+1]
        })

    return {
        "status": "success",
        "total_minimum_cost": min_total_cost,
        "schedule": schedule
    }
```

### 5.2 Frontend dashboard (`app.py`)

```python
import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Supply Chain Optimizer", layout="wide")

st.title("📦 Supply Chain Cost Optimization Engine")
st.markdown("Optimize production, inventory, and transportation costs using **Dynamic Programming**.")

col1, col2 = st.columns([1, 2])

with col1:
    st.header("Simulation Parameters")
    initial_inv = st.number_input("Initial Inventory", value=20)
    warehouse_cap = st.number_input("Warehouse Capacity", value=100)

    default_data = pd.DataFrame({
        "Month": ["January", "February", "March", "April", "May", "June"],
        "Demand": [80, 100, 130, 90, 140, 100],
        "Capacity": [120, 120, 120, 120, 150, 150],
        "Prod Cost": [10, 11, 9, 13, 10, 14],
        "Transport Cost": [2, 2, 3, 2, 2, 3],
        "Holding Cost": [1, 1, 1, 2, 2, 2]
    })

    st.subheader("Monthly Planning Data")
    edited_df = st.data_editor(default_data, num_rows="fixed")

with col2:
    st.header("Optimization Results")
    if st.button("Run DP Optimization", type="primary"):
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
            res = requests.post("http://127.0.0.1:8000/api/v1/optimize", json=payload)
            if res.status_code == 200:
                data = res.json()
                st.success(f"Optimization Successful! Minimum Total Cost: **₹{data['total_minimum_cost']:.2f}**")

                result_df = pd.DataFrame(data["schedule"])
                st.dataframe(result_df, use_container_width=True)

                st.subheader("Production vs Demand Trend")
                chart_data = result_df.set_index("month")[["demand", "optimal_production", "ending_inventory"]]
                st.line_chart(chart_data)
            else:
                st.error(f"Backend error: {res.text}")
        except Exception as e:
            st.error(f"Connection failed: {e}. Make sure FastAPI is running.")
```

---

## 6. Installation & Execution Guide

1. **Set up the project folder** and place `main.py` and `app.py` inside it.
2. **Install dependencies:**

   ```bash
   pip install fastapi uvicorn streamlit pandas numpy requests
   ```
3. **Start the FastAPI backend:**

   ```bash
   uvicorn main:app --reload
   ```
4. **In a separate terminal, launch the Streamlit dashboard:**

   ```bash
   streamlit run app.py
   ```
