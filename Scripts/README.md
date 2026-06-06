# GlobalMart Retail Intelligence Pipeline
### Databricks Free Edition — Beginner's Step-by-Step Guide

---

## What You're Building

You are building a **data pipeline** that takes raw sales data (a CSV file) and transforms it into clean, reliable data that a Power BI dashboard can read. Think of it like a kitchen:

- **Bronze Layer** = raw ingredients (straight from the CSV, untouched)
- **Silver Layer** = prepped ingredients (cleaned, chopped, labelled)
- **Gold Layer** = finished dishes (ready to serve to the business)

This pattern is called the **Medallion Architecture** and is used by companies like Netflix, Airbnb, and Databricks itself.

---

## Folder Structure

```
globalmart/
├── setup/
│   └── 00_setup_environment.py    ← Run FIRST (creates catalogs/schemas/volumes)
├── bronze/
│   └── 01_bronze_ingestion.py     ← Run SECOND (reads CSV → saves raw Delta table)
├── silver/
│   └── 02_silver_cleaning.py      ← Run THIRD (cleans data → dimension + fact tables)
└── gold/
    └── 03_gold_modeling.py        ← Run LAST (aggregates for Power BI)
```

---

## Step-by-Step Instructions

### Step 1 — Create a Databricks Account

---

### Step 2 — Create a Cluster (Your Computing Engine)
A cluster is the server that runs your Spark code. Without it, nothing executes.

1. In the left sidebar, click **Compute**.
2. Click **Create compute**.
3. Settings:
   - **Policy**: Personal Compute
   - **Cluster mode**: Single node
   - **Databricks Runtime**: Pick the latest **LTS** version (e.g. `14.3 LTS`)
   - **Node type**: Default is fine
4. Click **Create compute**.
5. Wait ~3 minutes for the green circle (it's starting up).

---

### Step 3 — Create Notebooks and Run Them in Order

For each `.py` file in this project:

1. In the left sidebar, click **New** → **Notebook**.
2. Give it a name matching the file (e.g. `00_setup_environment`).
3. Make sure **Python** is selected as the language.
4. Open the `.py` file from your computer, copy all the code.
5. Paste it into the first cell of the Databricks notebook.
6. At the top, make sure your cluster is selected in the dropdown.
7. Click **Run all**.

**Run notebooks in this order:**
```
00_setup_environment.py  →  01_bronze_ingestion.py  →  02_silver_cleaning.py  →  03_gold_modeling.py
```

> ⚠️ Do NOT skip steps or run out of order. Each notebook depends on the one before it.

---

### Step 4 — Upload the CSV File (Between Notebook 00 and 01)

After running Notebook 00, upload your data:

1. In the left sidebar, click **Catalog** (the book icon).
2. Navigate to: `bronze` → `superstore` → `raw_superstore`
3. Click **Upload to this volume**.
4. Upload `Sample - Superstore.csv`.
5. Then run Notebook 01.

Download the dataset here: https://www.kaggle.com/datasets/vivek468/superstore-dataset-final

---

### Step 5 — Connect Power BI to Databricks

After running all four notebooks:

1. In Databricks, click **Partner Connect** (lightning bolt icon in left sidebar).
2. Find **Power BI** and click it.
3. Download and run the `.pbids` connection file it generates.
4. Power BI Desktop will open and prompt you to sign in with your Databricks credentials.
5. Select the **gold** catalog and import these tables:
   - `gold.superstore.fact_sales`
   - `gold.superstore.dim_customer`
   - `gold.superstore.dim_product`
   - `gold.superstore.dim_date`
   - `gold.superstore.agg_profitability_by_subcategory`
   - `gold.superstore.agg_shipping_performance_by_region`
   - `gold.superstore.agg_top_customers_by_spend`

---

## Dashboard Requirements Checklist

Your final Power BI dashboard must answer these three questions:

| # | Business Question | Gold Table to Use |
|---|------------------|-------------------|
| 1 | Which Product Sub-Categories have the lowest profit margins? | `agg_profitability_by_subcategory` |
| 2 | What is the Average Days to Ship per Region? | `agg_shipping_performance_by_region` |
| 3 | Who are the Top 10 Customers by total spend year-to-date? | `agg_top_customers_by_spend` |

**Required visual:** A KPI Card at the top showing **Total Profit** formatted as currency.
- Use the `total_profit` column from `fact_sales` for this.

---

## Key Concepts Glossary (For Beginners)

| Term | What it means |
|------|--------------|
| **Spark / PySpark** | A computing engine for processing large datasets. PySpark is the Python API for it. |
| **Delta Table** | A special table format used in Databricks. It supports versioning and ACID transactions (like a database). |
| **Medallion Architecture** | Bronze → Silver → Gold pattern for organizing data pipelines. |
| **Idempotent** | "Safe to run multiple times." Re-running doesn't create duplicates or errors. |
| **Surrogate Key** | An artificial primary key we create (e.g. a hash). Differs from the original source ID. |
| **Fact Table** | Stores measurable events/transactions (sales). Contains foreign keys to dimensions. |
| **Dimension Table** | Stores descriptive reference data (who? what? when?). |
| **Star Schema** | A model where one central Fact table is surrounded by Dimension tables — looks like a star. |
| **Upsert / MERGE** | Insert new rows AND update existing ones in one operation. Prevents duplicates. |
| **Derived Metric** | A value calculated from other columns (e.g. `delivery_days = ship_date - order_date`). |

---

## Troubleshooting

**"Table not found" error**
→ You skipped a notebook. Run them in order: 00 → 01 → 02 → 03.

**"Path does not exist" error on the CSV**
→ You haven't uploaded the CSV to the Volume yet. See Step 4 above.

**Cluster shows as "Terminated"**
→ Free Edition clusters auto-terminate after 2 hours of inactivity. Click the cluster name → **Start**.

**"AnalysisException: schema mismatch"**
→ Add `.option("overwriteSchema", "true")` to the write command, or drop and recreate the table.

**Power BI can't connect**
→ Make sure your cluster is running (not terminated) before connecting from Power BI.
