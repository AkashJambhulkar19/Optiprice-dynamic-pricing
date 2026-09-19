"""
=============================================================================
OPTIPRICE: MARKETPLACE DATA GENERATION ENGINE
Generates realistic multi-competitor pricing, stock status, and daily sales
logs with genuine econometric demand elasticity and competitor cross-elasticity.
=============================================================================
"""

import os
import random
import datetime
import numpy as np
import pandas as pd

# Set deterministic seed for reproducible analytical results
np.random.seed(42)
random.seed(42)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
os.makedirs(DATA_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# 1. Product Catalog Definition
# ---------------------------------------------------------------------------
PRODUCTS = [
    # Category: Electronics & Peripherals
    {"sku": "ELEC-101", "name": "ANC Wireless Earbuds Pro", "category": "Electronics", "cost": 32.0, "base_price": 59.99, "true_elasticity": -2.1, "cross_elasticity": 1.4},
    {"sku": "ELEC-102", "name": "65W GaN Fast Charger", "category": "Electronics", "cost": 12.5, "base_price": 24.99, "true_elasticity": -1.8, "cross_elasticity": 1.2},
    {"sku": "ELEC-103", "name": "RGB Mechanical Keyboard", "category": "Electronics", "cost": 45.0, "base_price": 79.99, "true_elasticity": -1.5, "cross_elasticity": 1.1},
    {"sku": "ELEC-104", "name": "4K Ultra-HD Webcam", "category": "Electronics", "cost": 28.0, "base_price": 49.99, "true_elasticity": -1.9, "cross_elasticity": 1.3},
    {"sku": "ELEC-105", "name": "10-in-1 USB-C Hub Adapter", "category": "Electronics", "cost": 18.0, "base_price": 34.99, "true_elasticity": -1.6, "cross_elasticity": 1.2},
    {"sku": "ELEC-106", "name": "Ergonomic Vertical Mouse", "category": "Electronics", "cost": 15.0, "base_price": 29.99, "true_elasticity": -1.4, "cross_elasticity": 0.9},

    # Category: FMCG & Specialty Grocery
    {"sku": "FMCG-201", "name": "Single-Origin Arabica Coffee (1kg)", "category": "Grocery", "cost": 11.0, "base_price": 18.99, "true_elasticity": -0.85, "cross_elasticity": 0.5},
    {"sku": "FMCG-202", "name": "Pure Whey Isolate Protein (2kg)", "category": "Grocery", "cost": 32.0, "base_price": 54.99, "true_elasticity": -1.2, "cross_elasticity": 1.1},
    {"sku": "FMCG-203", "name": "Cold-Pressed Extra Virgin Olive Oil", "category": "Grocery", "cost": 8.5, "base_price": 14.99, "true_elasticity": -0.75, "cross_elasticity": 0.4},
    {"sku": "FMCG-204", "name": "Raw Organic Almond Butter (500g)", "category": "Grocery", "cost": 6.0, "base_price": 11.99, "true_elasticity": -0.9, "cross_elasticity": 0.6},
    {"sku": "FMCG-205", "name": "Ceremonial Japanese Matcha Tea", "category": "Grocery", "cost": 14.0, "base_price": 26.99, "true_elasticity": -1.1, "cross_elasticity": 0.8},
    {"sku": "FMCG-206", "name": "Himalayan Pink Salt Grinder", "category": "Grocery", "cost": 2.2, "base_price": 5.99, "true_elasticity": -0.65, "cross_elasticity": 0.3},

    # Category: Personal Care & Beauty
    {"sku": "BEAU-301", "name": "Pure Vitamin C 20% Brightening Serum", "category": "Personal Care", "cost": 9.5, "base_price": 22.99, "true_elasticity": -2.3, "cross_elasticity": 1.6},
    {"sku": "BEAU-302", "name": "SPF 50+ Invisible Sunscreen Fluid", "category": "Personal Care", "cost": 7.0, "base_price": 16.99, "true_elasticity": -1.3, "cross_elasticity": 0.9},
    {"sku": "BEAU-303", "name": "Hyaluronic Acid Hydrating Gel", "category": "Personal Care", "cost": 8.0, "base_price": 19.99, "true_elasticity": -1.7, "cross_elasticity": 1.3},
    {"sku": "BEAU-304", "name": "Rosemary Scalp Revitalizing Oil", "category": "Personal Care", "cost": 5.5, "base_price": 13.99, "true_elasticity": -1.4, "cross_elasticity": 0.8},
    {"sku": "BEAU-305", "name": "Activated Charcoal Foaming Cleanser", "category": "Personal Care", "cost": 4.5, "base_price": 10.99, "true_elasticity": -1.1, "cross_elasticity": 0.7},

    # Category: Home & Living
    {"sku": "HOME-401", "name": "True HEPA Air Purifier Filter", "category": "Home Essentials", "cost": 16.0, "base_price": 29.99, "true_elasticity": -0.7, "cross_elasticity": 0.45},
    {"sku": "HOME-402", "name": "Double-Wall Insulated Steel Tumbler", "category": "Home Essentials", "cost": 8.5, "base_price": 19.99, "true_elasticity": -1.6, "cross_elasticity": 1.2},
    {"sku": "HOME-403", "name": "Microfiber Quick-Dry Bath Towel Set", "category": "Home Essentials", "cost": 11.0, "base_price": 24.99, "true_elasticity": -1.2, "cross_elasticity": 0.9},
    {"sku": "HOME-404", "name": "Dimmable LED Architectural Desk Lamp", "category": "Home Essentials", "cost": 19.0, "base_price": 39.99, "true_elasticity": -1.5, "cross_elasticity": 1.0},
    {"sku": "HOME-405", "name": "Organic Bamboo Cooking Utensils Set", "category": "Home Essentials", "cost": 6.0, "base_price": 14.99, "true_elasticity": -1.0, "cross_elasticity": 0.7},
]

COMPETITORS = ["MegaRetail_HQ", "SwiftBlink_Prime", "ApexMarket_Direct"]

def generate_catalog():
    """Builds and saves master catalog dataframe."""
    catalog = []
    for p in PRODUCTS:
        target_margin = round(((p["base_price"] - p["cost"]) / p["base_price"]) * 100, 2)
        catalog.append({
            "sku": p["sku"],
            "product_name": p["name"],
            "category": p["category"],
            "cost_price": p["cost"],
            "base_price": p["base_price"],
            "target_margin_pct": target_margin
        })
    df_cat = pd.DataFrame(catalog)
    output_path = os.path.join(DATA_DIR, "dim_products.csv")
    df_cat.to_csv(output_path, index=False)
    print(f" Saved catalog to {output_path} ({len(df_cat)} products)")
    return df_cat

def generate_market_data(days=90):
    """
    Simulates 90 days of daily competitor price scraping and internal transactions.
    Employs econometric demand simulation:
    Q_t = exp( alpha + beta * ln(P_our) + gamma * ln(P_comp_min) + weekend_boost + stockout_surge + noise )
    """
    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=days)
    dates = [start_date + datetime.timedelta(days=i) for i in range(days)]

    competitor_rows = []
    sales_rows = []
    tx_counter = 10001

    for prod in PRODUCTS:
        sku = prod["sku"]
        base_p = prod["base_price"]
        cost_p = prod["cost"]
        beta = prod["true_elasticity"]
        gamma = prod["cross_elasticity"]
        
        # Base daily volume calibrated to realistic e-comm velocity (25 - 90 units/day)
        base_daily_units = np.random.uniform(30, 80)
        alpha = np.log(base_daily_units) - beta * np.log(base_p) - gamma * np.log(base_p)

        # Baseline competitor price anchors
        comp_price_state = {c: base_p * np.random.uniform(0.96, 1.04) for c in COMPETITORS}

        for d in dates:
            d_str = d.strftime("%Y-%m-%d")
            is_weekend = d.weekday() >= 5
            is_promo_day = (d.day in [1, 15, 28]) or (is_weekend and random.random() < 0.2)

            # 1. Internal Store Pricing Decision
            # Store tests dynamic discount cycles
            price_variance = np.random.normal(0, 0.04)
            if is_promo_day:
                discount = np.random.uniform(0.08, 0.18)
                our_price = round(base_p * (1 - discount), 2)
            else:
                our_price = round(base_p * (1 + price_variance), 2)
            
            # Floor check: Never sell below cost + 5%
            our_price = max(round(cost_p * 1.05, 2), our_price)

            # 2. Competitor Behavior & Scraping Simulation
            daily_comp_prices = []
            competitors_stocked_out = 0

            for comp in COMPETITORS:
                # Random walk with mean reversion toward base price
                shock = np.random.normal(0, 0.03)
                reversion = 0.15 * (base_p - comp_price_state[comp])
                comp_price_state[comp] = round(comp_price_state[comp] + reversion + (base_p * shock), 2)
                
                # Competitors occasionally run aggressive flash sales (15% off)
                if random.random() < 0.08:
                    comp_price = round(comp_price_state[comp] * 0.85, 2)
                else:
                    comp_price = comp_price_state[comp]

                # Competitor Stockout simulation (~6% probability)
                in_stock = random.random() > 0.06
                if not in_stock:
                    competitors_stocked_out += 1

                shipping = 0.0 if comp_price > 35 else 3.99

                competitor_rows.append({
                    "record_date": d_str,
                    "sku": sku,
                    "competitor_name": comp,
                    "competitor_price": comp_price,
                    "in_stock": in_stock,
                    "shipping_fee": shipping
                })
                
                if in_stock:
                    daily_comp_prices.append(comp_price)

            # 3. Market Demand Determination (Econometric Model)
            min_comp_p = min(daily_comp_prices) if daily_comp_prices else our_price
            
            # Own-price and cross-price log-log equation
            ln_q = alpha + beta * np.log(our_price) + gamma * np.log(min_comp_p)
            
            # Demand modifiers
            if is_weekend:
                ln_q += 0.22  # ~25% traffic boost on weekends
            if is_promo_day:
                ln_q += 0.15  # Promotional halo effect
            if competitors_stocked_out >= 2:
                ln_q += 0.45  # Massive surge when competitors stock out (+55%)
            elif competitors_stocked_out == 1:
                ln_q += 0.20  # +22% surge

            # Add idiosyncratic market noise
            ln_q += np.random.normal(0, 0.08)
            
            units_sold = int(max(1, np.round(np.exp(ln_q))))
            gross_revenue = round(units_sold * our_price, 2)
            gross_cost = round(units_sold * cost_p, 2)
            gross_profit = round(gross_revenue - gross_cost, 2)

            sales_rows.append({
                "transaction_id": f"TXN-{tx_counter}",
                "transaction_date": d_str,
                "sku": sku,
                "units_sold": units_sold,
                "unit_selling_price": our_price,
                "is_promo_day": is_promo_day,
                "gross_revenue": gross_revenue,
                "gross_cost": gross_cost,
                "gross_profit": gross_profit
            })
            tx_counter += 1

    df_comp = pd.DataFrame(competitor_rows)
    df_sales = pd.DataFrame(sales_rows)

    comp_path = os.path.join(DATA_DIR, "raw_competitor_prices.csv")
    sales_path = os.path.join(DATA_DIR, "raw_sales_transactions.csv")

    df_comp.to_csv(comp_path, index=False)
    df_sales.to_csv(sales_path, index=False)

    print(f" Generated {len(df_comp)} competitor price records -> {comp_path}")
    print(f" Generated {len(df_sales)} daily transaction records -> {sales_path}")

if __name__ == "__main__":
    generate_catalog()
    generate_market_data(days=90)
