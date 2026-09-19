"""
=============================================================================
OPTIPRICE: ECONOMETRIC ELASTICITY & PRICE OPTIMIZATION ENGINE
Performs OLS log-log regression to estimate Own-Price and Cross-Price Elasticity
of demand. Computes microeconomic optimal prices to maximize gross profit.
=============================================================================
"""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import numpy as np
import pandas as pd
import statsmodels.api as sm
from src.db_manager import query_warehouse, get_connection


def calculate_sku_elasticity(df_sku):
    """
    Fits Log-Log Demand Model for a single SKU:
    ln(Units) = alpha + beta_own * ln(Our_Price) + beta_cross * ln(Comp_Price) + e
    Returns elasticity coefficients, R-squared, and p-values.
    """
    # Filter valid rows
    valid = df_sku[(df_sku["total_units_sold"] > 0) & 
                   (df_sku["our_effective_price"] > 0) & 
                   (df_sku["min_competitor_price"] > 0)].copy()

    if len(valid) < 15:
        return None

    y = np.log(valid["total_units_sold"])
    X = pd.DataFrame({
        "ln_our_price": np.log(valid["our_effective_price"]),
        "ln_comp_price": np.log(valid["min_competitor_price"]),
        "is_weekend": (pd.to_datetime(valid["report_date"]).dt.weekday >= 5).astype(int)
    })
    X = sm.add_constant(X)

    try:
        model = sm.OLS(y, X).fit()
        beta_own = float(model.params.get("ln_our_price", -1.0))
        beta_cross = float(model.params.get("ln_comp_price", 0.5))
        p_val_own = float(model.pvalues.get("ln_our_price", 1.0))
        r2 = float(model.rsquared)

        return {
            "own_price_elasticity": round(beta_own, 3),
            "cross_price_elasticity": round(beta_cross, 3),
            "r_squared": round(r2, 3),
            "p_value_own": round(p_val_own, 4)
        }
    except Exception as e:
        return None

def compute_optimal_price(cost_price, current_price, elasticity, min_comp_price, avg_daily_units):
    """
    Finds the profit-maximizing price using the exact log-log demand function:
    Q(P) = Q_0 * (P / P_0)^beta
    Profit(P) = Q(P) * (P - cost)
    Searches candidate price adjustments from -20% to +20% with operational guardrails.
    Guarantees that recommended price maximizes profit without unconstrained extrapolation.
    """
    beta = elasticity
    current_profit = avg_daily_units * (current_price - cost_price)
    
    # Candidate multipliers from 0.82 to 1.20 in 0.5% increments
    candidate_multipliers = np.linspace(0.82, 1.20, 77)
    best_price = current_price
    best_profit = current_profit

    for mult in candidate_multipliers:
        cand_p = round(current_price * mult, 2)
        # Margin floor constraint: Must have at least 12% gross margin
        if cand_p < cost_price * 1.12:
            continue
        
        # Exact econometric log-log demand projection
        ratio = cand_p / current_price
        cand_units = avg_daily_units * (ratio ** beta)
        cand_profit = cand_units * (cand_p - cost_price)
        
        if cand_profit > best_profit:
            best_profit = cand_profit
            best_price = cand_p

    return best_price

def run_pricing_optimization():
    """
    Runs full elasticity pipeline across all SKUs and builds dim_pricing_recommendations table.
    """
    query = """
    SELECT 
        sku,
        product_name,
        category,
        cost_price,
        report_date,
        our_effective_price,
        min_competitor_price,
        avg_competitor_price,
        total_units_sold,
        total_revenue,
        total_gross_profit,
        market_position_status,
        competitor_stock_status
    FROM fct_daily_pricing_performance
    """
    df = query_warehouse(query)
    
    skus = df["sku"].unique()
    recommendations = []

    for sku in skus:
        df_sku = df[df["sku"] == sku]
        meta = df_sku.iloc[0]
        cost_p = meta["cost_price"]
        current_avg_p = round(df_sku["our_effective_price"].mean(), 2)
        comp_min_p = round(df_sku["min_competitor_price"].mean(), 2)
        avg_daily_units = round(df_sku["total_units_sold"].mean(), 1)
        total_monthly_rev = round(df_sku["total_revenue"].sum() / (len(df_sku) / 30), 2)
        total_monthly_profit = round(df_sku["total_gross_profit"].sum() / (len(df_sku) / 30), 2)

        metrics = calculate_sku_elasticity(df_sku)
        if not metrics:
            continue

        ped = metrics["own_price_elasticity"]
        xed = metrics["cross_price_elasticity"]

        rec_price = compute_optimal_price(cost_p, current_avg_p, ped, comp_min_p, avg_daily_units)
        price_change_pct = round(((rec_price - current_avg_p) / current_avg_p) * 100, 1)

        # Classification & Strategy
        if ped > -1.0:
            elasticity_class = "Inelastic (Pricing Power)"
            strategy = "Margin Expansion: Inelastic demand allows price increase without volume loss"
        elif ped < -1.7:
            elasticity_class = "Highly Elastic (Price Sensitive)"
            strategy = "Volume Capture: High elasticity indicates discounting or matching expands margin"
        else:
            elasticity_class = "Moderate Elasticity"
            strategy = "Parity & Selective Promotion: Calibrate price to maintain optimal velocity"

        # Exact log-log demand projection
        ratio = rec_price / current_avg_p
        forecasted_daily_units = max(1.0, avg_daily_units * (ratio ** ped))
        
        forecasted_monthly_rev = round(forecasted_daily_units * rec_price * 30, 2)
        forecasted_monthly_profit = round(forecasted_daily_units * (rec_price - cost_p) * 30, 2)
        profit_delta_monthly = max(0.0, round(forecasted_monthly_profit - total_monthly_profit, 2))

        recommendations.append({
            "sku": sku,
            "product_name": meta["product_name"],
            "category": meta["category"],
            "cost_price": cost_p,
            "current_price": current_avg_p,
            "competitor_min_price": comp_min_p,
            "own_price_elasticity": ped,
            "cross_price_elasticity": xed,
            "r_squared": metrics["r_squared"],
            "elasticity_class": elasticity_class,
            "recommended_price": rec_price,
            "price_change_pct": price_change_pct,
            "current_monthly_profit": total_monthly_profit,
            "forecasted_monthly_profit": forecasted_monthly_profit,
            "monthly_profit_uplift": profit_delta_monthly,
            "strategic_action": strategy
        })

    df_rec = pd.DataFrame(recommendations)

    # Save to DuckDB table dim_pricing_recommendations
    con = get_connection()
    con.execute("CREATE OR REPLACE TABLE dim_pricing_recommendations AS SELECT * FROM df_rec")
    con.close()

    print(f" Elasticity and Price Optimization Engine completed for {len(df_rec)} SKUs.")
    total_uplift = df_rec["monthly_profit_uplift"].sum()
    print(f" Total Identified Monthly Profit Uplift across catalog: ${total_uplift:,.2f} (${total_uplift * 12:,.2f} annualized)")

    return df_rec

if __name__ == "__main__":
    run_pricing_optimization()
