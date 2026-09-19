-- =====================================================================
-- SCHEMA INITIALIZATION FOR OPTIPRICE ANALYTICS REPOSITORY
-- Database Engine: DuckDB / Analytical SQL
-- =====================================================================

-- 1. Product Dimension: Master Catalog with unit economics
CREATE TABLE IF NOT EXISTS dim_products (
    sku VARCHAR PRIMARY KEY,
    product_name VARCHAR NOT NULL,
    category VARCHAR NOT NULL,
    cost_price DOUBLE NOT NULL,
    base_price DOUBLE NOT NULL,
    target_margin_pct DOUBLE NOT NULL
);

-- 2. Competitor Pricing Telemetry: Scraped competitor price & stock data
CREATE TABLE IF NOT EXISTS stg_competitor_prices (
    record_date DATE NOT NULL,
    sku VARCHAR NOT NULL,
    competitor_name VARCHAR NOT NULL,
    competitor_price DOUBLE NOT NULL,
    in_stock BOOLEAN NOT NULL,
    shipping_fee DOUBLE DEFAULT 0.0,
    PRIMARY KEY (record_date, sku, competitor_name)
);

-- 3. Sales Transactions: Daily store-level checkout logs
CREATE TABLE IF NOT EXISTS stg_sales_transactions (
    transaction_id VARCHAR PRIMARY KEY,
    transaction_date DATE NOT NULL,
    sku VARCHAR NOT NULL,
    units_sold INTEGER NOT NULL,
    unit_selling_price DOUBLE NOT NULL,
    is_promo_day BOOLEAN DEFAULT FALSE,
    gross_revenue DOUBLE NOT NULL,
    gross_cost DOUBLE NOT NULL,
    gross_profit DOUBLE NOT NULL
);
