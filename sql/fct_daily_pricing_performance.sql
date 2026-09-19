-- =====================================================================
-- FACT TABLE: Daily Pricing Performance & Competitor Benchmark Mart
-- Engine: DuckDB
-- Advanced SQL: Common Table Expressions (CTEs), Window Functions,
--               Cross-Table Metric Aggregations, Partitioned Ranking
-- =====================================================================

CREATE OR REPLACE TABLE fct_daily_pricing_performance AS
WITH daily_internal_sales AS (
    -- Aggregate internal transaction performance by day and SKU
    SELECT
        transaction_date AS report_date,
        sku,
        SUM(units_sold) AS total_units_sold,
        ROUND(AVG(unit_selling_price), 2) AS our_effective_price,
        ROUND(SUM(gross_revenue), 2) AS total_revenue,
        ROUND(SUM(gross_profit), 2) AS total_gross_profit,
        ROUND(SUM(gross_profit) / NULLIF(SUM(gross_revenue), 0) * 100, 2) AS our_gross_margin_pct,
        MAX(is_promo_day) AS was_promo_day
    FROM stg_sales_transactions
    GROUP BY transaction_date, sku
),

competitor_daily_benchmarks AS (
    -- Aggregate competitor landscape: lowest price, average price, stockout count
    SELECT
        record_date AS report_date,
        sku,
        COUNT(DISTINCT competitor_name) AS active_competitors_tracked,
        ROUND(AVG(competitor_price), 2) AS avg_competitor_price,
        ROUND(MIN(competitor_price), 2) AS min_competitor_price,
        ROUND(MAX(competitor_price), 2) AS max_competitor_price,
        -- Window function: 7-day rolling average competitor price
        ROUND(AVG(AVG(competitor_price)) OVER (
            PARTITION BY sku 
            ORDER BY record_date 
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ), 2) AS rolling_7d_avg_competitor_price,
        SUM(CASE WHEN in_stock = TRUE THEN 1 ELSE 0 END) AS competitors_in_stock,
        SUM(CASE WHEN in_stock = FALSE THEN 1 ELSE 0 END) AS competitors_stocked_out
    FROM stg_competitor_prices
    GROUP BY record_date, sku
),

joined_pricing_mart AS (
    -- Join internal performance with external competitor telemetry
    SELECT
        s.report_date,
        p.category,
        s.sku,
        p.product_name,
        p.cost_price,
        s.our_effective_price,
        c.avg_competitor_price,
        c.min_competitor_price,
        c.rolling_7d_avg_competitor_price,
        c.active_competitors_tracked,
        c.competitors_in_stock,
        c.competitors_stocked_out,
        s.total_units_sold,
        s.total_revenue,
        s.total_gross_profit,
        s.our_gross_margin_pct,
        s.was_promo_day,
        
        -- Relative Price Index (RPI): > 100 means we are more expensive, < 100 means we are cheaper
        ROUND((s.our_effective_price / NULLIF(c.avg_competitor_price, 0)) * 100, 1) AS relative_price_index,
        
        -- Price difference against market minimum
        ROUND(s.our_effective_price - c.min_competitor_price, 2) AS spread_vs_market_min,
        
        -- Competitor undercutting classification
        CASE
            WHEN s.our_effective_price > c.min_competitor_price THEN 'Undercut by Market'
            WHEN s.our_effective_price = c.min_competitor_price THEN 'Price Matched'
            ELSE 'Price Leader (Cheapest)'
        END AS market_position_status,
        
        -- Stockout opportunity flag: all or majority competitors are out of stock
        CASE
            WHEN c.competitors_stocked_out > 0 AND c.competitors_in_stock = 0 THEN 'Monopoly Stock Window'
            WHEN c.competitors_stocked_out > 0 THEN 'Partial Competitor Stockout'
            ELSE 'Full Competitor Availability'
        END AS competitor_stock_status
    FROM daily_internal_sales s
    INNER JOIN dim_products p ON s.sku = p.sku
    LEFT JOIN competitor_daily_benchmarks c 
           ON s.report_date = c.report_date 
          AND s.sku = c.sku
)

SELECT * FROM joined_pricing_mart;
