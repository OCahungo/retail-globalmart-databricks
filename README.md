#**GlobalMart Retail Intelligence Pipeline** (Chris Gambill)

## **Summary**

*Current State*: GlobalMart currently manually compiles sales spreadsheets at the end of every month. This 30-day latency prevents the supply chain team from reacting to shipping delays and prevents the marketing team from identifying high-value customers in real-time.

*Future State*: The goal is to build an end-to-end data pipeline that ingests raw sales data, cleans and standardizes it, and produces a Gold-layer data model. This will power a Power BI dashboard allowing stakeholders to view profit margins and shipping performance with zero manual effort.

#Technical Architecture

Only Databricks Free Edition and Power BI Desktop (or Tableau).

- Ingestion (Source):
  - Data Source: Sample - Superstore.csv.
  - Ingest Pattern: Batch load into Databricks Volume
- Processing (Transformation):
  - Engine: Apache Spark (PySpark) on Databricks.
  - Orchestration: Notebook Execution And Set Up Databricks Job to schedule notebook run.
- Storage *(The Medallion Architecture)*:
  - Bronze Layer: Raw data ingestion (as-is) with metadata columns (ingest date).
  - Silver Layer: Cleaned, deduplicated, friendly field names, and validated data. (Schema enforcement).
  - Gold Layer: Aggregated Star Schema (Fact tables joined with Dimensions) optimized for reporting.
- Serving *(Visualization)*:
	- Tool: Power BI Desktop.
  - Connection: Import mode via partner connect integration (via marketplace inside of Databricks)


