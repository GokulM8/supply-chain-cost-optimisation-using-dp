"""
Tests for the supply chain DP engine.
"""

import pytest
import numpy as np
from engine.dp import optimize_supply_chain
from engine.baselines import naive_strategy, greedy_strategy


def test_sample_dataset():
    """Test with the sample dataset from README."""
    demands = [80, 100, 130, 90, 140, 100]
    capacities = [120, 120, 120, 120, 150, 150]
    prod_costs = [10, 11, 9, 13, 10, 14]
    transport_costs = [2, 2, 3, 2, 2, 3]
    holding_costs = [1, 1, 1, 2, 2, 2]
    initial_inventory = 20
    warehouse_capacity = 100

    # Run DP optimization
    dp_cost, dp_production, dp_inventory = optimize_supply_chain(
        demands, capacities, prod_costs, transport_costs, holding_costs,
        initial_inventory, warehouse_capacity
    )

    # Run baselines
    naive_cost, naive_production, naive_inventory = naive_strategy(
        demands, capacities, prod_costs, transport_costs, holding_costs,
        initial_inventory, warehouse_capacity
    )

    greedy_cost, greedy_production, greedy_inventory = greedy_strategy(
        demands, capacities, prod_costs, transport_costs, holding_costs,
        initial_inventory, warehouse_capacity
    )

    # Verify DP cost is less than or equal to baselines
    assert dp_cost <= naive_cost + 1e-10  # Small tolerance for floating point
    assert dp_cost <= greedy_cost + 1e-10

    # Verify basic properties
    assert dp_cost >= 0
    assert len(dp_production) == len(demands)
    assert len(dp_inventory) == len(demands)

    # Verify inventory constraints
    assert dp_inventory[0] == initial_inventory  # Starting inventory
    # Note: The returned inventory sequence excludes the initial value, so we need to reconstruct
    full_inventory = [initial_inventory] + dp_inventory
    assert full_inventory[-1] == 0  # Ending inventory should be 0

    for i, inv in enumerate(full_inventory):
        assert 0 <= inv <= warehouse_capacity

    # Verify production constraints
    for i, prod in enumerate(dp_production):
        assert 0 <= prod <= capacities[i]


def test_infeasible_input():
    """Test that infeasible inputs raise appropriate error."""
    # Demand exceeds capacity and no way to build inventory due to limits
    demands = [150]  # Higher than capacity
    capacities = [100]
    prod_costs = [10]
    transport_costs = [2]
    holding_costs = [1]
    initial_inventory = 0
    warehouse_capacity = 50  # Too small to build enough inventory

    with pytest.raises(ValueError, match="No feasible plan"):
        optimize_supply_chain(
            demands, capacities, prod_costs, transport_costs, holding_costs,
            initial_inventory, warehouse_capacity
        )


def test_input_validation():
    """Test input validation."""
    demands = [80, 100]
    capacities = [120]  # Wrong length
    prod_costs = [10, 11]
    transport_costs = [2, 2]
    holding_costs = [1, 1]

    with pytest.raises(ValueError, match="All input arrays must have the same length"):
        optimize_supply_chain(
            demands, capacities, prod_costs, transport_costs, holding_costs
        )

    # Test negative values
    demands = [80, -10]  # Negative demand
    capacities = [120, 120]

    with pytest.raises(ValueError, match="Demands must be non-negative"):
        optimize_supply_chain(
            demands, capacities, prod_costs, transport_costs, holding_costs
        )

    # Test non-integer demands/capacities
    demands = [80.5, 100]  # Non-integer demand
    capacities = [120, 120]

    with pytest.raises(ValueError, match="must be an integer"):
        optimize_supply_chain(
            demands, capacities, prod_costs, transport_costs, holding_costs
        )


def test_inventory_balance():
    """Test that inventory balance constraint is satisfied."""
    demands = [80, 100, 130]
    capacities = [120, 120, 120]
    prod_costs = [10, 11, 9]
    transport_costs = [2, 2, 3]
    holding_costs = [1, 1, 1]
    initial_inventory = 20
    warehouse_capacity = 100

    dp_cost, dp_production, dp_inventory = optimize_supply_chain(
        demands, capacities, prod_costs, transport_costs, holding_costs,
        initial_inventory, warehouse_capacity
    )

    # Reconstruct full inventory sequence
    full_inventory = [initial_inventory] + dp_inventory

    # Check inventory balance: I_t = I_{t-1} + P_t - D_t
    for t in range(len(demands)):
        expected_inventory = full_inventory[t] + dp_production[t] - demands[t]
        assert abs(full_inventory[t+1] - expected_inventory) < 1e-10


if __name__ == "__main__":
    pytest.main([__file__])