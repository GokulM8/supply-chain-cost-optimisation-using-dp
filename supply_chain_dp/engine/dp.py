"""
Dynamic Programming engine for supply chain cost optimization.
"""

import numpy as np
from typing import List, Tuple


def optimize_supply_chain(
    demands: List[float],
    capacities: List[float],
    prod_costs: List[float],
    transport_costs: List[float],
    holding_costs: List[float],
    initial_inventory: int = 20,
    warehouse_capacity: int = 100
) -> Tuple[float, List[float], List[int]]:
    """
    Optimize supply chain costs using Dynamic Programming.

    Args:
        demands: Customer demand for each period
        capacities: Maximum production capacity for each period
        prod_costs: Production cost per unit for each period
        transport_costs: Transportation cost per unit for each period
        holding_costs: Inventory holding cost per unit for each period
        initial_inventory: Starting inventory (default: 20)
        warehouse_capacity: Maximum warehouse capacity (default: 100)

    Returns:
        Tuple of (total_minimum_cost, production_schedule, inventory_sequence)

    Raises:
        ValueError: If inputs are invalid or no feasible solution exists
    """
    # Validate integer inputs for inventory calculations
    _validate_integer_inputs(demands, capacities)

    # Input validation
    T = len(demands)
    if not all(len(arr) == T for arr in [capacities, prod_costs, transport_costs, holding_costs]):
        raise ValueError("All input arrays must have the same length")

    if any(x < 0 for x in demands):
        raise ValueError("Demands must be non-negative")
    if any(x < 0 for x in capacities):
        raise ValueError("Capacities must be non-negative")
    if any(x < 0 for x in prod_costs):
        raise ValueError("Production costs must be non-negative")
    if any(x < 0 for x in transport_costs):
        raise ValueError("Transport costs must be non-negative")
    if any(x < 0 for x in holding_costs):
        raise ValueError("Holding costs must be non-negative")

    if initial_inventory < 0:
        raise ValueError("Initial inventory must be non-negative")
    if warehouse_capacity <= 0:
        raise ValueError("Warehouse capacity must be positive")
    if initial_inventory > warehouse_capacity:
        raise ValueError("Initial inventory cannot exceed warehouse capacity")

    # Combine production and transportation costs
    total_prod_costs = [p + tr for p, tr in zip(prod_costs, transport_costs)]

    # Initialize DP table
    W = warehouse_capacity
    INF = float('inf')
    DP = np.full((T + 1, W + 1), INF)
    parent = np.full((T + 1, W + 1), -1, dtype=int)

    # Base case: period 0
    DP[0][initial_inventory] = 0

    # Fill DP table
    for t in range(1, T + 1):
        d = demands[t-1]
        k = capacities[t-1]
        h = holding_costs[t-1]
        c_prod = total_prod_costs[t-1]

        # Vectorized computation for current period
        for i in range(W + 1):  # ending inventory i
            # Calculate production needed: P_t = D_t + I_t - I_{t-1}
            # Rearranging: I_{t-1} = D_t + I_t - P_t
            # For each possible previous inventory j, production is P_t = d + i - j
            min_cost = INF
            best_prev_j = -1

            # Check all possible previous inventory states j
            for j in range(W + 1):
                p_t = d + i - j  # production needed
                # Check if production is feasible: 0 <= P_t <= K_t
                if 0 <= p_t <= k:
                    if DP[t-1][j] != INF:
                        cost = DP[t-1][j] + (c_prod * p_t) + (h * i)
                        if cost < min_cost:
                            min_cost = cost
                            best_prev_j = j

            DP[t][i] = min_cost
            parent[t][i] = best_prev_j

    # Check if solution exists
    min_total_cost = DP[T][0]
    if min_total_cost == INF:
        raise ValueError("No feasible plan under the given constraints.")

    # Backtrack to find optimal inventory sequence
    inventory_sequence = [0] * (T + 1)
    inventory_sequence[T] = 0  # Final inventory must be 0

    current_inv = 0
    for t in range(T, 0, -1):
        prev_inv = parent[t][current_inv]
        inventory_sequence[t-1] = prev_inv
        current_inv = prev_inv

    # Calculate optimal production schedule
    optimal_production = []
    for t in range(T):
        # P_t = D_t + I_{t+1} - I_t
        p_t = demands[t] + inventory_sequence[t+1] - inventory_sequence[t]
        optimal_production.append(p_t)

    return min_total_cost, optimal_production, inventory_sequence[1:]  # Exclude initial inventory from returned sequence


def _validate_integer_inputs(demands: List[float], capacities: List[float]) -> None:
    """
    Validate that demands and capacities are integers (or can be safely converted).
    This is important because inventory states are integer-valued.
    """
    for d in demands:
        if not float(d).is_integer():
            raise ValueError(f"Demand {d} must be an integer for inventory calculations")

    for k in capacities:
        if not float(k).is_integer():
            raise ValueError(f"Capacity {k} must be an integer for inventory calculations")