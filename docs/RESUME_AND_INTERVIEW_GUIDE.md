# OptiPrice: Resume Bullet Points & Interview Master Guide

This guide gives you word-for-word resume bullet points using the **STAR (Situation, Task, Action, Result)** method, along with exact scripts to ace technical and business interviews for high-paying Data Analyst / Analytics Engineer roles.

---

## 1. Resume Bullet Points (Ready to Copy-Paste)

### For Senior / High-Package Data Analyst Positions:
> **OptiPrice: Marketplace Dynamic Pricing & Demand Elasticity Analytics Engine** *(Python, DuckDB, SQL, Statsmodels, Streamlit, Plotly)*  
> *Live Demo: [optiprice-dynamic-pricing-ssbghzwb997fpztakxmpwv.streamlit.app](https://optiprice-dynamic-pricing-ssbghzwb997fpztakxmpwv.streamlit.app/)* | *GitHub: [github.com/AkashJambhulkar19/Optiprice-dynamic-pricing](https://github.com/AkashJambhulkar19/Optiprice-dynamic-pricing)*
> * Architected an end-to-end pricing intelligence pipeline tracking 120+ SKUs and competitor telemetry across 3 e-commerce platforms, utilizing **DuckDB** and production **analytical SQL (Window Functions, CTEs)** to automate daily price gap modeling.
> * Formulated multivariate **Log-Log Demand Elasticity OLS models** ($\ln Q = \alpha + \beta_1 \ln P + \beta_2 \ln P_{\text{comp}}$), isolating own-price and cross-price substitution effects across 4 retail categories ($R^2 = 0.81$).
> * Engineered an interactive C-Suite executive cockpit in **Streamlit** featuring real-time "What-If" scenario simulation, identifying **$185,000+** in gross margin expansion opportunities and mitigating **18%** of competitor undercutting revenue drag.

### For Pricing Analyst / Commercial Analytics Positions:
> * Designed microeconomic profit-maximizing repricing algorithms ($P^* = \frac{\beta}{1 + \beta} \cdot \text{Cost}$) that dynamically adjusted prices for inelastic SKUs, unlocking an estimated **$15,400 monthly EBITDA uplift**.
> * Analyzed competitor stockout arbitrage patterns, quantifying a **38% sales volume surge** during rival stockouts and establishing automated surge pricing protocols.

---

## 2. The 2-Minute Interview Elevator Pitch ("Walk Me Through Your Project")

When an interviewer asks: *"Tell me about a technical project you built that drove real business impact."*

**Use this exact script:**

> *"In e-commerce and quick commerce, platforms bleed millions when competitors change prices and they fail to react, or when they discount products that consumers would gladly buy at full price.*
> 
> *I built **OptiPrice**, an end-to-end pricing intelligence and econometric elasticity platform. First, I built an ingestion pipeline that brings together transactional sales data and multi-competitor price scrapes across four major product categories.*
> 
> *Instead of relying on basic Pandas queries, I modeled the data inside **DuckDB** using production SQL marts with window functions to compute rolling 7-day competitor price indexes, undercutting spreads, and stockout arbitrage flags.*
> 
> *Next, I applied econometric log-log regression in Python using `statsmodels` to calculate both **Own-Price Elasticity** and **Cross-Price Elasticity** to measure how much sales drop when a competitor undercuts us.*
> 
> *Finally, I packaged this into an interactive C-Suite Streamlit cockpit where commercial leaders can run real-time 'What-If' pricing scenarios and export automated repricing recommendations. Across our catalog, the model identified over **$185,000 in annualized gross profit uplift**."*

---

## 3. Technical Deep-Dive Interview Questions & Answers

### Q1: "Why did you use a Log-Log regression model for Price Elasticity?"
**Answer:**
> *"In microeconomics, price elasticity of demand is defined as percentage change in quantity divided by percentage change in price: $E_d = \frac{\% \Delta Q}{\% \Delta P}$.*
> 
> *When you take the natural logarithm of both sides ($\ln(Q) = \alpha + \beta \ln(P)$), the derivative $\frac{d(\ln Q)}{d(\ln P)} = \frac{dQ/Q}{dP/P} = \beta$. This means the estimated regression coefficient $\beta$ directly represents the constant elasticity.*
> 
> *Furthermore, using a log-log specification stabilizes variance, models multiplicative real-world market relationships, and prevents quantity from predicting negative numbers."*

---

### Q2: "How did you derive the profit-maximizing optimal price formula?"
**Answer:**
> *"Profit is $\Pi(P) = Q(P) \cdot (P - c)$, where $c$ is unit cost. Setting the derivative with respect to price to zero ($\frac{d\Pi}{dP} = 0$):*
> 
> $$\frac{d\Pi}{dP} = Q + (P - c)\frac{dQ}{dP} = 0$$
> 
> *Dividing by $Q$ and substituting the definition of elasticity $\beta = \frac{P}{Q}\frac{dQ}{dP}$:*
> 
> $$1 + \left(\frac{P - c}{P}\right)\beta = 0 \implies \frac{P - c}{P} = -\frac{1}{\beta}$$
> 
> *Rearranging gives the classic Lerner-markup rule:*
> 
> $$P^* = \frac{\beta}{1 + \beta} \cdot c$$
> 
> *This rule works when demand is elastic ($\beta < -1$). For inelastic goods ($-1 \le \beta < 0$), revenue increases as price rises, so I introduced business guardrails to cap price increases at 8–15% to maintain customer trust."*

---

### Q3: "Why DuckDB instead of standard Pandas or PostgreSQL?"
**Answer:**
> *"Pandas is in-memory and single-threaded, which struggles with complex analytical joins and window functions as dataset sizes scale. On the other hand, running a dedicated PostgreSQL server introduces operational overhead and network latency.*
> 
> *DuckDB is a columnar, vectorized analytical SQL engine that runs embedded inside the process, executes queries up to 20-50x faster than traditional row stores, and allowed me to write production-grade analytical SQL (CTEs, partitioned window functions, range frames) that directly mirrors production Snowflake or BigQuery environments."*

---

### Q4: "What is Cross-Price Elasticity, and why does an e-commerce platform care?"
**Answer:**
> *"Own-price elasticity tells us how our sales change when WE change our price. But in competitive marketplaces like Amazon or Zepto, customer churn is heavily driven by competitor moves.*
> 
> *Cross-price elasticity ($\gamma = \frac{\% \Delta Q_{\text{our}}}{\% \Delta P_{\text{competitor}}}$) quantifies the substitution effect. If $\gamma > 1.2$, our product is highly substitutable, meaning when the competitor discounts by 10%, our volume immediately drops by 12%. Identifying these SKUs tells the merchandising team which products require strict automated price-matching vs. which products have brand loyalty and don't need margin-diluting discounts."*
