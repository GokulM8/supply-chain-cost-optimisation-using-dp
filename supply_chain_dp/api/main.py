"""
FastAPI application for supply chain cost optimization.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import sys
import os

# Add engine to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'engine'))

from dp import optimize_supply_chain
from baselines import naive_strategy, greedy_strategy

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


class StrategyResult(BaseModel):
    total_cost: float
    production_schedule: List[float]
    inventory_sequence: List[int]


class OptimizationResponse(BaseModel):
    status: str
    dp_result: StrategyResult
    naive_result: StrategyResult
    greedy_result: StrategyResult
    savings_vs_naive: float
    savings_vs_greedy: float


@app.post("/api/v1/optimize", response_model=OptimizationResponse)
def optimize_supply_chain_endpoint(data: SupplyChainInput):
    """
    Optimize supply chain costs using DP, naive, and greedy strategies.

    Returns costs and schedules for all three strategies plus savings percentages.
    """
    try:
        # Run Dynamic Programming optimization
        dp_cost, dp_production, dp_inventory = optimize_supply_chain(
            demands=data.demands,
            capacities=data.prod_capacities,
            prod_costs=data.prod_costs,
            transport_costs=data.transport_costs,
            holding_costs=data.holding_costs,
            initial_inventory=data.initial_inventory,
            warehouse_capacity=data.warehouse_capacity
        )

        # Run Naive baseline
        naive_cost, naive_production, naive_inventory = naive_strategy(
            demands=data.demands,
            capacities=data.prod_capacities,
            prod_costs=data.prod_costs,
            transport_costs=data.transport_costs,
            holding_costs=data.holding_costs,
            initial_inventory=data.initial_inventory,
            warehouse_capacity=data.warehouse_capacity
        )

        # Run Greedy baseline
        greedy_cost, greedy_production, greedy_inventory = greedy_strategy(
            demands=data.demands,
            capacities=data.prod_capacities,
            prod_costs=data.prod_costs,
            transport_costs=data.transport_costs,
            holding_costs=data.holding_costs,
            initial_inventory=data.initial_inventory,
            warehouse_capacity=data.warehouse_capacity
        )

        # Calculate savings percentages
        savings_vs_naive = ((naive_cost - dp_cost) / naive_cost * 100) if naive_cost > 0 else 0.0
        savings_vs_greedy = ((greedy_cost - dp_cost) / greedy_cost * 100) if greedy_cost > 0 else 0.0

        # Create schedule for response
        def create_schedule(months, demands, production, inventory):
            schedule = []
            for i, month in enumerate(months):
                schedule.append({
                    "month": month,
                    "demand": demands[i],
                    "optimal_production": production[i],
                    "ending_inventory": inventory[i]
                })
            return schedule

        return OptimizationResponse(
            status="success",
            dp_result=StrategyResult(
                total_cost=dp_cost,
                production_schedule=dp_production,
                inventory_sequence=dp_inventory
            ),
            naive_result=StrategyResult(
                total_cost=naive_cost,
                production_schedule=naive_production,
                inventory_sequence=naive_inventory
            ),
            greedy_result=StrategyResult(
                total_cost=greedy_cost,
                production_schedule=greedy_production,
                inventory_sequence=greedy_inventory
            ),
            savings_vs_naive=savings_vs_naive,
            savings_vs_greedy=savings_vs_greedy
        )

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")