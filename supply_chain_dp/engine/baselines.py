"""
Baseline strategies for supply chain cost optimization.
"""

import numpy as np
from typing import List, Tuple


def naive_strategy(
    demands: List[float],
    capacities: List[float],
    prod_costs: List[float],
    transport_costs: List[float],
    holding_costs: List[float],
    initial_inventory: int = 20,
    warehouse_capacity: int = 100
) -> Tuple[float, List[float], List[int]]:
    """
    Naive strategy: produce exactly what is needed each period after accounting for existing stock.

    This strategy maintains inventory as low as possible while meeting demand,
    producing only what's needed to meet demand plus any necessary adjustments
    to stay within warehouse capacity bounds.

    Args:
        Same as optimize_supply_chain

    Returns:
        Tuple of (total_cost, production_schedule, inventory_sequence)
    """
    T = len(demands)

    # Combine production and transportation costs
    total_prod_costs = [p + tr for p, tr in zip(prod_costs, transport_costs)]

    # Initialize arrays
    production = [0.0] * T
    inventory = [0.0] * (T + 1)
    inventory[0] = float(initial_inventory)

    # For each period, produce to meet demand, adjusting for inventory constraints
    for t in range(T):
        d = demands[t]
        # Start with producing exactly to meet demand
        desired_production = d

        # Calculate what inventory would be if we produced desired amount
        projected_inventory = inventory[t] + desired_production - d

        # Clamp inventory to warehouse bounds [0, warehouse_capacity]
        if projected_inventory < 0:
            # Need to produce more to avoid negative inventory
            production[t] = d - inventory[t]
            inventory[t+1] = 0
        elif projected_inventory > warehouse_capacity:
            # Produce less to avoid exceeding capacity
            production[t] = warehouse_capacity - inventory[t] + d
            inventory[t+1] = warehouse_capacity
        else:
            # Produce exactly to meet demand
            production[t] = desired_production
            inventory[t+1] = projected_inventory

        # Ensure production doesn't exceed capacity
        if production[t] > capacities[t]:
            production[t] = capacities[t]
            inventory[t+1] = inventory[t] + production[t] - d
            # Clamp again after capacity adjustment
            if inventory[t+1] < 0:
                inventory[t+1] = 0
            elif inventory[t+1] > warehouse_capacity:
                inventory[t+1] = warehouse_capacity

    # Ensure final inventory is 0 (adjust last period if needed)
    if inventory[T] != 0:
        # Adjust production in last period to meet final inventory constraint
        adjustment = inventory[T]
        production[T-1] -= adjustment
        inventory[T] = 0
        # Ensure production doesn't go negative
        if production[T-1] < 0:
            production[T-1] = 0
            # Recalculate inventory (this might not be perfectly accurate but handles edge case)
            inventory[T] = inventory[T-1] + production[T-1] - demands[T-1]

    # Calculate total cost
    total_cost = 0.0
    for t in range(T):
        total_cost += total_prod_costs[t] * production[t] + holding_costs[t] * inventory[t+1]

    return total_cost, production, [int(x) for x in inventory[1:]]  # Exclude initial inventory and convert to int


def greedy_strategy(
    demands: List[float],
    capacities: List[float],
    prod_costs: List[float],
    transport_costs: List[float],
    holding_costs: List[float],
    initial_inventory: int = 20,
    warehouse_capacity: int = 100
) -> Tuple[float, List[float], List[int]]:
    """
    Greedy strategy: prefer production in locally cheapest periods.

    This strategy produces more in periods with lower production costs
    to build inventory for future use, and less in expensive periods.

    Args:
        Same as optimize_supply_chain

    Returns:
        Tuple of (total_cost, production_schedule, inventory_sequence)
    """
    T = len(demands)

    # Combine production and transportation costs
    total_prod_costs = [p + tr for p, tr in zip(prod_costs, transport_costs)]

    # Calculate average cost to determine "cheap" vs "expensive" periods
    avg_cost = np.mean(total_prod_costs) if T > 0 else 0

    # Initialize arrays
    production = [0.0] * T
    inventory = [0.0] * (T + 1)
    inventory[0] = float(initial_inventory)

    # For each period, make greedy decision based on cost
    for t in range(T):
        d = demands[t]
        k = capacities[t]
        c = total_prod_costs[t]
        h = holding_costs[t]  # Used in cost calculation later

        # If current period cost is below average, produce up to capacity to build inventory
        if c <= avg_cost:
            # Produce as much as possible (up to capacity) to build cheap inventory
            max_producible = min(k, d + warehouse_capacity - inventory[t])
            production[t] = max_producible
        else:
            # Expensive period: produce only what's needed to meet demand
            production[t] = max(0, d - inventory[t])

        # Ensure production doesn't exceed capacity
        production[t] = min(production[t], k)

        # Calculate resulting inventory
        inventory[t+1] = inventory[t] + production[t] - d

        # Clamp inventory to warehouse bounds
        if inventory[t+1] < 0:
            inventory[t+1] = 0
            # If we went negative, we needed to produce more
            production[t] = d - inventory[t]
            inventory[t+1] = 0
        elif inventory[t+1] > warehouse_capacity:
            inventory[t+1] = warehouse_capacity
            # If we exceeded capacity, we needed to produce less
            production[t] = warehouse_capacity - inventory[t] + d
            # Re-clamp to capacity
            production[t] = min(production[t], k)
            inventory[t+1] = inventory[t] + production[t] - d

    # Ensure final inventory is 0
    if inventory[T] != 0:
        adjustment = inventory[T]
        if T > 0:
            # Try to adjust last period production
            if adjustment > 0:  # Have excess inventory, reduce last period production
                reduction = min(adjustment, production[T-1])
                production[T-1] -= reduction
            else:  # Need more inventory, increase last period production (if possible)
                increase = min(-adjustment, capacities[T-1] - production[T-1])
                production[T-1] += increase
            inventory[T] = inventory[T-1] + production[T-1] - demands[T-1]

    # Calculate total cost
    total_cost = 0.0
    for t in range(T):
        total_cost += total_prod_costs[t] * production[t] + holding_costs[t] * inventory[t+1]

    return total_cost, production, [int(x) for x in inventory[1:]]  # Exclude initial inventory and convert to int