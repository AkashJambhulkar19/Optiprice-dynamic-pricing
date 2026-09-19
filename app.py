"""
=============================================================================
OPTIPRICE: ENTERPRISE PRICING INTELLIGENCE & DEMAND ELASTICITY PLATFORM
C-Suite Executive Analytics Dashboard & Dynamic Repricing Cockpit
=============================================================================
"""

import os
import duckdb
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Configure page metadata
st.set_page_config(
    page_title="OptiPrice | Executive Pricing Intelligence",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply sleek executive CSS
st.markdown("""
<style>
    /* Metric Card Styling */
    .metric-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 16px 20px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.2);
    }
    .metric-title {
        color: #94a3b8;
        font-size: 13px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 4px;
    }
    .metric-value {
        color: #f8fafc;
        font-size: 26px;
        font-weight: 700;
        margin-bottom: 2px;
    }
    .metric-delta-pos {
        color: #10b981;
        font-size: 12px;
        font-weight: 600;
    }
    .metric-delta-neg {
        color: #ef4444;
        font-size: 12px;
        font-weight: 600;
    }
    /* Section headers */
    .section-header {
        font-size: 20px;
        font-weight: 700;
        color: #f1f5f9;
        margin-top: 10px;
        margin-bottom: 12px;
    }
    /* Badges */
    .badge-inelastic {
        background-color: #064e3b;
        color: #34d399;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: 600;
    }
    .badge-elastic {
        background-color: #7f1d1d;
        color: #f87171;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(PROJECT_ROOT, "optiprice.duckdb")

@st.cache_data(ttl=600)
def load_data():
    """Fetches core analytics tables from DuckDB."""
    if not os.path.exists(DB_PATH):
        st.warning(" DuckDB database not initialized yet. Run database initialization pipeline first.")
        return None, None, None, None

    con = duckdb.connect(database=DB_PATH, read_only=True)
    df_pricing = con.execute("SELECT * FROM fct_daily_pricing_performance").fetchdf()
    df_stockout = con.execute("SELECT * FROM fct_stockout_opportunity").fetchdf()
    df_rec = con.execute("SELECT * FROM dim_pricing_recommendations").fetchdf()
    df_raw_comp = con.execute("SELECT * FROM stg_competitor_prices").fetchdf()
    con.close()

    df_pricing["report_date"] = pd.to_datetime(df_pricing["report_date"])
    df_stockout["report_date"] = pd.to_datetime(df_stockout["report_date"])
    df_raw_comp["record_date"] = pd.to_datetime(df_raw_comp["record_date"])
    return df_pricing, df_stockout, df_rec, df_raw_comp

# ---------------------------------------------------------------------------
# Sidebar Controls & Global Filters
# ---------------------------------------------------------------------------
st.sidebar.image("https://img.icons8.com/fluency/96/bullish.png", width=64)
st.sidebar.title("OptiPrice Engine")
st.sidebar.caption("Enterprise Pricing Intelligence & Demand Analytics")

df_pricing, df_stockout, df_rec, df_raw_comp = load_data()

if df_pricing is None:
    st.info("Please initialize the pipeline using the buttons below.")
    if st.button(" Run Pipeline Initialization"):
        from src.data_generator import generate_catalog, generate_market_data
        from src.db_manager import build_data_warehouse
        from src.elasticity_engine import run_pricing_optimization
        with st.spinner("Generating market simulation data..."):
            generate_catalog()
            generate_market_data(90)
        with st.spinner("Executing DuckDB SQL Marts..."):
            build_data_warehouse()
        with st.spinner("Fitting Econometric Elasticity Models..."):
            run_pricing_optimization()
        st.success(" Pipeline initialized successfully! Reloading...")
        st.rerun()
    st.stop()

# Sidebar Category Multi-select
categories = sorted(df_pricing["category"].unique().tolist())
selected_categories = st.sidebar.multiselect(
    "Filter Categories:",
    options=categories,
    default=categories
)

# Date Filter
min_date = df_pricing["report_date"].min().date()
max_date = df_pricing["report_date"].max().date()
date_range = st.sidebar.date_input("Date Range:", [min_date, max_date])

# Filter datasets
if len(date_range) == 2:
    start_d, end_d = date_range
    filtered_pricing = df_pricing[(df_pricing["category"].isin(selected_categories)) & 
                                  (df_pricing["report_date"].dt.date >= start_d) & 
                                  (df_pricing["report_date"].dt.date <= end_d)]
else:
    filtered_pricing = df_pricing[df_pricing["category"].isin(selected_categories)]

filtered_rec = df_rec[df_rec["category"].isin(selected_categories)]

st.sidebar.markdown("---")
st.sidebar.markdown("###  Quick Summary")
total_catalog_skus = len(df_rec)
inelastic_skus = len(df_rec[df_rec["own_price_elasticity"] > -1.0])
elastic_skus = len(df_rec[df_rec["own_price_elasticity"] < -1.7])
st.sidebar.metric("Tracked SKUs", f"{total_catalog_skus}")
st.sidebar.metric("Inelastic SKUs (Pricing Power)", f"{inelastic_skus}")
st.sidebar.metric("Elastic SKUs (Price Sensitive)", f"{elastic_skus}")

# ---------------------------------------------------------------------------
# Navigation Tabs
# ---------------------------------------------------------------------------
tab_overview, tab_benchmarks, tab_elasticity, tab_reprice, tab_sql = st.tabs([
    " Executive KPI Cockpit",
    " Competitor Benchmarking",
    " Elasticity & What-If Simulator",
    " Dynamic Repricing Action Center",
    " SQL Warehouse & Queries"
])

# ---------------------------------------------------------------------------
# TAB 1: EXECUTIVE KPI COCKPIT
# ---------------------------------------------------------------------------
with tab_overview:
    st.markdown('<div class="section-header">Executive Revenue Health & Competitor Pressure</div>', unsafe_allow_html=True)

    # Top KPI Metrics Calculation
    total_rev = filtered_pricing["total_revenue"].sum()
    total_profit = filtered_pricing["total_gross_profit"].sum()
    overall_margin = (total_profit / total_rev) * 100 if total_rev > 0 else 0
    
    undercut_records = filtered_pricing[filtered_pricing["market_position_status"] == "Undercut by Market"]
    undercut_rate = (len(undercut_records) / len(filtered_pricing)) * 100 if len(filtered_pricing) > 0 else 0
    
    # Value at Risk: Total revenue earned on days when undercut vs if matched
    value_at_risk = undercut_records["total_revenue"].sum() * 0.12  # Estimated 12% revenue drag
    
    # Stockout Opportunity captured
    stockout_arbitrage_total = df_stockout["uncaptured_pricing_power_dollar"].sum()

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Gross Revenue</div>
            <div class="metric-value">${total_rev:,.0f}</div>
            <div class="metric-delta-pos"> 90-Day Trailing</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Gross Margin</div>
            <div class="metric-value">{overall_margin:.1f}%</div>
            <div class="metric-delta-pos"> Target: 42.0%</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Competitor Undercut Rate</div>
            <div class="metric-value">{undercut_rate:.1f}%</div>
            <div class="metric-delta-neg"> of sales under pressure</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Revenue at Risk</div>
            <div class="metric-value">${value_at_risk:,.0f}</div>
            <div class="metric-delta-neg"> Margin erosion risk</div>
        </div>
        """, unsafe_allow_html=True)

    with col5:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Stockout Arbitrage</div>
            <div class="metric-value">${stockout_arbitrage_total:,.0f}</div>
            <div class="metric-delta-pos"> Pricing power window</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Chart 1: Daily Revenue Trend vs Undercut Percentage
    daily_summary = filtered_pricing.groupby("report_date").agg({
        "total_revenue": "sum",
        "total_gross_profit": "sum",
        "market_position_status": lambda x: (x == "Undercut by Market").mean() * 100
    }).reset_index().rename(columns={"market_position_status": "undercut_pct"})

    col_chart_left, col_chart_right = st.columns([7, 5])

    with col_chart_left:
        fig_timeline = go.Figure()
        fig_timeline.add_trace(go.Scatter(
            x=daily_summary["report_date"],
            y=daily_summary["total_revenue"],
            name="Daily Revenue ($)",
            mode="lines",
            line=dict(color="#3b82f6", width=2.5)
        ))
        fig_timeline.add_trace(go.Scatter(
            x=daily_summary["report_date"],
            y=daily_summary["total_gross_profit"],
            name="Gross Profit ($)",
            mode="lines",
            line=dict(color="#10b981", width=2, dash="dot")
        ))
        fig_timeline.update_layout(
            title="<b>Daily Revenue & Gross Profit Trajectory</b>",
            template="plotly_dark",
            height=360,
            margin=dict(l=20, r=20, t=40, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_timeline, use_container_width=True)

    with col_chart_right:
        # Category breakdown
        cat_perf = filtered_pricing.groupby("category").agg({
            "total_revenue": "sum",
            "total_gross_profit": "sum"
        }).reset_index()
        cat_perf["margin_pct"] = (cat_perf["total_gross_profit"] / cat_perf["total_revenue"]) * 100

        fig_cat = px.bar(
            cat_perf,
            x="category",
            y="margin_pct",
            color="category",
            text=cat_perf["margin_pct"].apply(lambda x: f"{x:.1f}%"),
            title="<b>Gross Margin % by Product Category</b>",
            template="plotly_dark",
            color_discrete_sequence=px.colors.qualitative.Prism
        )
        fig_cat.update_layout(
            height=360,
            showlegend=False,
            yaxis_title="Gross Margin %",
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig_cat, use_container_width=True)

# ---------------------------------------------------------------------------
# TAB 2: COMPETITOR BENCHMARKING
# ---------------------------------------------------------------------------
with tab_benchmarks:
    st.markdown('<div class="section-header">Competitor Price Distribution & Gap Analysis</div>', unsafe_allow_html=True)
    
    col_bench1, col_bench2 = st.columns([6, 6])
    
    with col_bench1:
        # Relative Price Index Distribution
        fig_rpi = px.histogram(
            filtered_pricing,
            x="relative_price_index",
            nbins=40,
            title="<b>Relative Price Index (RPI) Distribution vs Market Average</b>",
            template="plotly_dark",
            color_discrete_sequence=["#6366f1"]
        )
        fig_rpi.add_vline(x=100, line_dash="dash", line_color="#ef4444", annotation_text="Market Parity (100)")
        fig_rpi.update_layout(
            xaxis_title="Relative Price Index (100 = Market Parity)",
            yaxis_title="Observation Count",
            height=340,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig_rpi, use_container_width=True)

    with col_bench2:
        # Competitor Market Share of Lowest Price
        market_pos_counts = filtered_pricing["market_position_status"].value_counts().reset_index()
        market_pos_counts.columns = ["Position", "Count"]

        fig_pos = px.pie(
            market_pos_counts,
            values="Count",
            names="Position",
            title="<b>Market Price Positioning Breakdown</b>",
            template="plotly_dark",
            hole=0.45,
            color_discrete_map={
                "Price Leader (Cheapest)": "#10b981",
                "Price Matched": "#3b82f6",
                "Undercut by Market": "#ef4444"
            }
        )
        fig_pos.update_layout(height=340, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_pos, use_container_width=True)

    st.markdown("####  Live Competitor Price Matrix & Spread (Latest Snapshot)")
    
    latest_date = df_pricing["report_date"].max()
    latest_snapshot = df_pricing[df_pricing["report_date"] == latest_date][
        ["sku", "product_name", "category", "our_effective_price", "min_competitor_price", 
         "avg_competitor_price", "spread_vs_market_min", "relative_price_index", "market_position_status"]
    ].sort_values("spread_vs_market_min", ascending=False)

    st.dataframe(
        latest_snapshot.style.format({
            "our_effective_price": "${:.2f}",
            "min_competitor_price": "${:.2f}",
            "avg_competitor_price": "${:.2f}",
            "spread_vs_market_min": "${:+.2f}",
            "relative_price_index": "{:.1f}"
        }),
        use_container_width=True,
        height=320
    )

# ---------------------------------------------------------------------------
# TAB 3: DEMAND ELASTICITY & WHAT-IF SIMULATOR
# ---------------------------------------------------------------------------
with tab_elasticity:
    st.markdown('<div class="section-header">Econometric Demand Elasticity & Interactive Scenario Simulator</div>', unsafe_allow_html=True)
    
    col_elas_left, col_elas_right = st.columns([6, 6])
    
    with col_elas_left:
        # Scatter: Elasticity vs Margin
        fig_scatter = px.scatter(
            filtered_rec,
            x="own_price_elasticity",
            y="price_change_pct",
            size="current_monthly_profit",
            color="elasticity_class",
            hover_name="product_name",
            title="<b>Own-Price Elasticity vs Recommended Price Adjustment</b>",
            template="plotly_dark",
            labels={
                "own_price_elasticity": "Own-Price Elasticity (β)",
                "price_change_pct": "Recommended Price Shift %"
            }
        )
        fig_scatter.add_vline(x=-1.0, line_dash="dash", line_color="#34d399", annotation_text="Unitary Elasticity (β = -1.0)")
        fig_scatter.update_layout(height=380, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_scatter, use_container_width=True)

    with col_elas_right:
        # Cross price elasticity bar
        cross_df = filtered_rec.sort_values("cross_price_elasticity", ascending=True)
        fig_cross = px.bar(
            cross_df,
            x="cross_price_elasticity",
            y="product_name",
            orientation="h",
            color="cross_price_elasticity",
            title="<b>Cross-Price Elasticity (Competitor Substitution Vulnerability)</b>",
            template="plotly_dark",
            color_continuous_scale="Reds"
        )
        fig_cross.update_layout(
            height=380, 
            margin=dict(l=20, r=20, t=40, b=20),
            xaxis_title="Cross-Price Elasticity (Higher = Easier for Competitors to Steal Volume)"
        )
        st.plotly_chart(fig_cross, use_container_width=True)

    st.markdown("---")
    st.markdown("###  Interactive Executive Pricing Simulator")
    st.caption("Adjust pricing sliders below to run real-time microeconomic simulations using estimated elasticity coefficients.")

    sim_col1, sim_col2 = st.columns([4, 8])

    with sim_col1:
        selected_sku = st.selectbox(
            "Select SKU to Simulate:",
            options=filtered_rec["sku"].tolist(),
            format_func=lambda s: f"{s} - {filtered_rec[filtered_rec['sku']==s]['product_name'].values[0]}"
        )
        sku_meta = filtered_rec[filtered_rec["sku"] == selected_sku].iloc[0]

        st.markdown(f"""
        **Category**: `{sku_meta['category']}`  
        **Unit Cost**: `${sku_meta['cost_price']:.2f}`  
        **Current Price**: `${sku_meta['current_price']:.2f}`  
        **Min Competitor Price**: `${sku_meta['competitor_min_price']:.2f}`  
        **Own Elasticity (β)**: `{sku_meta['own_price_elasticity']:.2f}`  
        **Cross Elasticity (γ)**: `{sku_meta['cross_price_elasticity']:.2f}`  
        """)

        sim_price_delta_pct = st.slider(
            "Simulated Our Price Adjustment (%):",
            min_value=-25,
            max_value=25,
            value=int(sku_meta["price_change_pct"]),
            step=1
        )
        sim_comp_reaction_pct = st.slider(
            "Simulated Competitor Reaction (%):",
            min_value=-20,
            max_value=15,
            value=0,
            step=1
        )

    with sim_col2:
        # Simulation math
        base_price = sku_meta["current_price"]
        cost = sku_meta["cost_price"]
        beta = sku_meta["own_price_elasticity"]
        gamma = sku_meta["cross_price_elasticity"]

        simulated_price = base_price * (1.0 + (sim_price_delta_pct / 100.0))
        comp_price = sku_meta["competitor_min_price"] * (1.0 + (sim_comp_reaction_pct / 100.0))

        # Demand change % = beta * (% change our price) + gamma * (% change comp price)
        demand_shift_pct = (beta * (sim_price_delta_pct / 100.0)) + (gamma * (sim_comp_reaction_pct / 100.0))
        
        # Monthly base volume derived from profit
        current_monthly_units = sku_meta["current_monthly_profit"] / max(0.1, (base_price - cost))
        simulated_monthly_units = max(1.0, current_monthly_units * (1.0 + demand_shift_pct))

        simulated_monthly_rev = simulated_monthly_units * simulated_price
        simulated_monthly_profit = simulated_monthly_units * (simulated_price - cost)
        simulated_margin_pct = (simulated_monthly_profit / simulated_monthly_rev) * 100

        current_monthly_rev = current_monthly_units * base_price
        current_monthly_profit = sku_meta["current_monthly_profit"]
        profit_delta = simulated_monthly_profit - current_monthly_profit

        # Display simulation KPIs
        kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
        with kpi_col1:
            st.metric("New Price", f"${simulated_price:.2f}", delta=f"{sim_price_delta_pct}%")
        with kpi_col2:
            st.metric("Forecasted Monthly Units", f"{simulated_monthly_units:,.0f}", delta=f"{demand_shift_pct*100:.1f}%")
        with kpi_col3:
            st.metric("Projected Monthly Revenue", f"${simulated_monthly_rev:,.0f}", delta=f"${simulated_monthly_rev - current_monthly_rev:+,.0f}")
        with kpi_col4:
            st.metric("Projected Monthly Profit", f"${simulated_monthly_profit:,.0f}", delta=f"${profit_delta:+,.0f}", delta_color="normal" if profit_delta >= 0 else "inverse")

        # Demand Curve Visualizer
        price_range = np.linspace(base_price * 0.75, base_price * 1.30, 50)
        units_curve = [max(1, current_monthly_units * (1.0 + beta * ((p - base_price) / base_price))) for p in price_range]
        profit_curve = [u * (p - cost) for u, p in zip(units_curve, price_range)]

        fig_sim = go.Figure()
        fig_sim.add_trace(go.Scatter(
            x=price_range, y=profit_curve,
            name="Monthly Gross Profit ($)",
            line=dict(color="#10b981", width=3)
        ))
        fig_sim.add_vline(x=base_price, line_dash="dash", line_color="#94a3b8", annotation_text="Current Price")
        fig_sim.add_vline(x=simulated_price, line_color="#3b82f6", annotation_text=f"Simulated (${simulated_price:.2f})")
        fig_sim.update_layout(
            title="<b>Profit Optimization Curve Across Simulated Price Points</b>",
            template="plotly_dark",
            xaxis_title="Price ($)",
            yaxis_title="Monthly Profit ($)",
            height=300,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig_sim, use_container_width=True)

# ---------------------------------------------------------------------------
# TAB 4: DYNAMIC REPRICING ACTION CENTER
# ---------------------------------------------------------------------------
with tab_reprice:
    st.markdown('<div class="section-header">Automated Dynamic Repricing Feed & Prescriptions</div>', unsafe_allow_html=True)
    
    total_pipeline_uplift = filtered_rec["monthly_profit_uplift"].sum()
    annualized_uplift = total_pipeline_uplift * 12

    st.info(f"""
     **Optimization Value Unlocked**: Implementing these mathematically optimal prices generates an estimated **${total_pipeline_uplift:,.2f}/month** in incremental gross profit (**${annualized_uplift:,.2f} annualized EBITDA expansion**).
    """)

    # Repricing Table
    repricing_view = filtered_rec[[
        "sku", "product_name", "category", "cost_price", "current_price", 
        "recommended_price", "price_change_pct", "elasticity_class", 
        "monthly_profit_uplift", "strategic_action"
    ]].sort_values("monthly_profit_uplift", ascending=False)

    st.dataframe(
        repricing_view.style.format({
            "cost_price": "${:.2f}",
            "current_price": "${:.2f}",
            "recommended_price": "${:.2f}",
            "price_change_pct": "{:+.1f}%",
            "monthly_profit_uplift": "+${:,.2f}"
        }),
        use_container_width=True,
        height=400
    )

    # Export Repricing Rules to CSV
    csv_repricing = repricing_view.to_csv(index=False).encode('utf-8')
    st.download_button(
        label=" Download Production Repricing Feed (CSV)",
        data=csv_repricing,
        file_name="optiprice_repricing_recommendations.csv",
        mime="text/csv"
    )

# ---------------------------------------------------------------------------
# TAB 5: SQL WAREHOUSE & LIVE QUERY CONSOLE
# ---------------------------------------------------------------------------
with tab_sql:
    st.markdown('<div class="section-header">Underlying SQL Architecture & Interactive DuckDB Console</div>', unsafe_allow_html=True)
    st.caption("Demonstrating production SQL data modeling: Window functions, CTEs, self-joins, and aggregations.")

    st.markdown("###  Interactive SQL Query Console")
    default_query = """-- Top 5 Most Vulnerable Products by Undercutting & Revenue Impact
SELECT 
    p.category,
    p.sku,
    p.product_name,
    COUNT(CASE WHEN f.market_position_status = 'Undercut by Market' THEN 1 END) AS days_undercut,
    ROUND(AVG(f.relative_price_index), 1) AS avg_relative_price_index,
    ROUND(SUM(f.total_revenue), 2) AS total_revenue,
    ROUND(SUM(f.total_gross_profit), 2) AS total_gross_profit
FROM fct_daily_pricing_performance f
JOIN dim_products p ON f.sku = p.sku
GROUP BY p.category, p.sku, p.product_name
ORDER BY days_undercut DESC, total_revenue DESC
LIMIT 5;"""

    user_query = st.text_area("Write or modify SQL query:", value=default_query, height=180)

    if st.button(" Run SQL Query"):
        try:
            con = duckdb.connect(database=DB_PATH, read_only=True)
            custom_df = con.execute(user_query).fetchdf()
            con.close()
            st.success(f" Query executed successfully! Returned {len(custom_df)} rows.")
            st.dataframe(custom_df, use_container_width=True)
        except Exception as err:
            st.error(f"SQL Error: {err}")

    st.markdown("---")
    st.markdown("###  Production SQL Transformation Scripts")
    
    with st.expander(" View `fct_daily_pricing_performance.sql` (Window Functions & Rolling Indexes)"):
        with open(os.path.join(PROJECT_ROOT, "sql", "fct_daily_pricing_performance.sql")) as f:
            st.code(f.read(), language="sql")

    with st.expander(" View `fct_stockout_opportunity.sql` (Competitor Stockout Arbitrage Model)"):
        with open(os.path.join(PROJECT_ROOT, "sql", "fct_stockout_opportunity.sql")) as f:
            st.code(f.read(), language="sql")
