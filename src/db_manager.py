"""
=============================================================================
OPTIPRICE: DUCKDB ANALYTICAL PIPELINE & DATABASE MANAGER
Automates schema creation, staging data ingestion, and transformation mart
execution using modern in-process analytical SQL (DuckDB).
=============================================================================
"""

import os
import duckdb
import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
SQL_DIR = os.path.join(PROJECT_ROOT, "sql")
DB_PATH = os.path.join(PROJECT_ROOT, "optiprice.duckdb")

def get_connection(db_path=DB_PATH):
    """Establishes connection to DuckDB."""
    return duckdb.connect(database=db_path, read_only=False)

def execute_sql_file(con, file_path):
    """Reads and executes a SQL script against DuckDB."""
    with open(file_path, "r", encoding="utf-8") as f:
        sql_content = f.read()
    # DuckDB can execute multi-statement SQL strings
    con.execute(sql_content)
    print(f" Executed SQL script: {os.path.basename(file_path)}")

def build_data_warehouse():
    """Initializes schema, loads CSVs, and runs analytical transformation models."""
    con = get_connection()
    print(" DuckDB connected. Building analytical data warehouse...")

    # 1. Initialize schema
    schema_file = os.path.join(SQL_DIR, "schema_init.sql")
    execute_sql_file(con, schema_file)

    # 2. Ingest CSV data into staging tables using DuckDB's vectorized CSV reader
    cat_csv = os.path.join(DATA_DIR, "dim_products.csv").replace("\\", "/")
    comp_csv = os.path.join(DATA_DIR, "raw_competitor_prices.csv").replace("\\", "/")
    sales_csv = os.path.join(DATA_DIR, "raw_sales_transactions.csv").replace("\\", "/")

    con.execute(f"INSERT OR REPLACE INTO dim_products SELECT * FROM read_csv_auto('{cat_csv}')")
    con.execute(f"INSERT OR REPLACE INTO stg_competitor_prices SELECT * FROM read_csv_auto('{comp_csv}')")
    con.execute(f"INSERT OR REPLACE INTO stg_sales_transactions SELECT * FROM read_csv_auto('{sales_csv}')")
    print(f" Ingested raw source data into staging tables.")

    # 3. Execute Analytical Marts (Fact Tables)
    fct_pricing = os.path.join(SQL_DIR, "fct_daily_pricing_performance.sql")
    execute_sql_file(con, fct_pricing)

    fct_stockout = os.path.join(SQL_DIR, "fct_stockout_opportunity.sql")
    execute_sql_file(con, fct_stockout)

    # Validate row counts
    count_pricing = con.execute("SELECT COUNT(*) FROM fct_daily_pricing_performance").fetchone()[0]
    count_stockout = con.execute("SELECT COUNT(*) FROM fct_stockout_opportunity").fetchone()[0]
    print(f" Warehouse built successfully!")
    print(f"   -> fct_daily_pricing_performance: {count_pricing} rows")
    print(f"   -> fct_stockout_opportunity: {count_stockout} rows")

    con.close()

def query_warehouse(query_str, db_path=DB_PATH):
    """Utility function to execute a query and return a pandas DataFrame."""
    con = duckdb.connect(database=db_path, read_only=True)
    df = con.execute(query_str).fetchdf()
    con.close()
    return df

if __name__ == "__main__":
    build_data_warehouse()
