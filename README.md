# 📊 GlobalMart Retail Intelligence Pipeline
### End-to-End Analytics Engineering Pipeline with PySpark, Delta Lake & Power BI

![Spark](https://shields.io)
![Databricks](https://shields.io)
![DeltaLake](https://shields.io)
![PowerBI](https://shields.io)


---

## Project Summary & Business Impact

* **Current State:** GlobalMart currently compiles sales spreadsheets manually at the end of every month. This 30-day latency prevents the supply chain team from reacting to shipping delays and prevents the marketing team from identifying high-value customers in real-time.
* **Future State (Solution):** Built an automated, end-to-end data pipeline that ingests raw sales data, cleans, standardizes, and consolidates a dimensional model into the Gold layer. This ecosystem powers a production-ready Power BI dashboard, allowing stakeholders to monitor profit margins and shipping performance with zero manual effort.

---

## The Business ROI Dashboard
The final report connects directly via **DirectQuery** mode to the Databricks cluster to dynamically answer three strategic executive questions:
1. **Profitability:** Which product sub-categories have the lowest profit margins (dragging down total company revenue)?
2. **Logistics Efficiency:** What is the average days to ship per region? (Mapping operational bottlenecks).
3. **Customer Value:** Who are the Top 10 high-value customers by total accumulated spend in the most recent fiscal year?

![Dashboard Preview](./images/dashboard_globalmart_retail_intelligence_preview.png)

---

## Technical Architecture & Medallion Layers

The distributed data processing architecture was developed using **PySpark** on **Databricks Community Edition** with permanent storage managed through **Delta Lake** tables:

| Layer | Load Type | Description & Applied Engineering |
| :--- | :--- | :--- |
| **Bronze** | Overwrite (Dev) | Ingests raw data as-is from a Databricks *Volume*. Automatically applies audit metadata (`_ingest_timestamp`, `_source_file`) and **dynamically handles automated cleaning for whitespace/special characters in column headers**. |
| **Silver** | Overwrite (Dev) | Cleans null values (`coalesce`), filters out corrupted records/returns (`order_quantity > 0`), and enforces strict structural typing (`try_cast`). Models data into a professional **Star Schema** with cryptographic surrogate primary keys (**Surrogate Keys via SHA-256**). |
| **Gold** | Overwrite (Dev) | Consolidates complex derived business metrics (rounded profit margins and shipping delta metrics via `datediff`). Generates specialized pre-aggregated structures optimized for fast serving and low-cost BI consumption. |

---

## Technical Challenges Overcome & Senior Performance Tuning

### 1. Data Schema Misalignment in Delta Lake (`[DELTA_FAILED_TO_MERGE_FIELDS]`)
* **The Problem:** During development cycles, changing primitive data types upstream (such as reading columns as strings without a heavy `inferSchema` block during Bronze staging) caused physical type mismatches when overwriting existing Delta tables. 
* **The Solution:** Implemented environment teardown tasks (`DROP TABLE IF EXISTS`) at the initialization block of the dev notebooks, paired with the storage option `.option("overwriteSchema", "true")` at execution time to securely reinitialize disk structures.

### 2. Dynamic Special Character & Column Whitespace Normalization
* **The Problem:** Source column headers containing spaces and special characters (e.g., `Row ID`, `Product ID`) broke downstream SQL engines and caused compatibility issues in physical Data Lake storage files.
* **The Solution:** Avoided writing repetitive, brittle column-by-column renaming blocks. Built a scalable, programmatically clean Python *list comprehension* script to trim trailing whitespace and replace internal characters with underscores dynamically:
```python
clean_columns = [F.col(f"`{c}`").alias(c.strip().replace(" ", "_")) for c in df_raw.columns]
df_with_clean_cols = df_raw.select(clean_columns)
```

### 3. Mitigating Global Shuffling Warnings (`WindowExpression Warning`)
* **The Problem:** The Spark optimizer issued a severe performance warning stating that evaluating a global `Window` row-ranking function over top-spending customers without a `.partitionBy` clause forced the entire dataset across the cluster to shuffle into a **single computing node**—introducing an immediate *Out of Memory (OOM)* risk.
* **The Solution:** Refactored the ranking logic to apply a distributed parallel filter `.limit(10)` directly on the nodes *before* executing the final sequential ranking ID allocation over a isolated `.repartition(1)` dataset, maintaining full scalability.

---

## How to Run the Project

1. Import the source code scripts located in the `/notebooks` folder into your Databricks Workspace.
2. Upload the raw dataset `Sample - Superstore.csv` into your configured Bronze Databricks Volume.
3. Verify and map your catalogue paths matching your cluster configuration inside the `CSV_PATH` variables.
4. Execute the notebooks sequentially (01 -> 02 -> 03) or deploy a **Databricks Job** to schedule and orchestrate automated execution.
5. Open the `.pbix` file from the `/dashboard` folder inside Power BI Desktop, navigate to Data Source Settings, and update the **Server Hostname** and **HTTP Path** to run your dashboard live under **DirectQuery** mode.
