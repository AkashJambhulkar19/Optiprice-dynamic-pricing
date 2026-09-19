-- =====================================================================
-- FACT TABLE: Competitor Stockout Arbitrage & Margin Opportunity Mart
-- Engine: DuckDB
-- Advanced SQL: Self-Joins, Conditional Volumetric Spreads, Impact Sizing
-- =====================================================================

CREATE OR REPLACE TABLE fct_stockout_opportunity AS
WITH baseline_sales AS (
    -- Normal day sales baseline (when competitors are in stock)
    SELECT
        sku,
        ROUND(AVG(total_units_sold), 1) AS baseline_daily_units,
        ROUND(AVG(our_gross_margin_pct), 2) AS baseline_margin_pct
    FROM fct_daily_pricing_performance
    WHERE competitor_stock_status = 'Full Competitor Availability'
    GROUP BY sku
),

stockout_events AS (
    -- Days where competitors experienced stockouts
    SELECT
        f.report_date,
        f.sku,
        f.product_name,
        f.category,
        f.our_effective_price,
        f.cost_price,
        f.total_units_sold,
        b.baseline_daily_units,
        -- Volume surge over baseline
        ROUND(f.total_units_sold - COALESCE(b.baseline_daily_units, f.total_units_sold), 0) AS incremental_units_captured,
        f.competitor_stock_status,
        f.competitors_stocked_out,
        f.total_revenue,
        f.total_gross_profit,
        -- Opportunity analysis: If we raised price by 5% during competitor stockouts, what would incremental profit be?
        ROUND(f.total_units_sold * (f.our_effective_price * 0.05), 2) AS uncaptured_pricing_power_dollar
    FROM fct_daily_pricing_performance f
    LEFT JOIN baseline_sales b ON f.sku = b.sku
    WHERE f.competitor_stock_status IN ('Monopoly Stock Window', 'Partial Competitor Stockout')
)

SELECT * FROM stockout_events;
