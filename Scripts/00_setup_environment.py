# =============================================================================
# NOTEBOOK 00 — ENVIRONMENT SETUP
# GlobalMart Retail Intelligence Pipeline
# =============================================================================
# PURPOSE:
#   This notebook creates the three catalogs (bronze, silver, gold) and the
#   schemas/volumes you will need before running any other notebook.
#
# HOW TO USE IN DATABRICKS:
#   1. Click "New" → "Notebook" in the left sidebar.
#   2. Paste this code into the cells (one cell per section, separated by # COMMAND).
#   3. Click "Run All" at the top.
#   4. Run this notebook ONCE before running any other notebook.
# =============================================================================


# ---------------------------------------------------------------------------
# CELL 1 — Create the three Medallion Catalogs
# ---------------------------------------------------------------------------
# A "catalog" in Databricks Unity Catalog is like a top-level folder/database
# that holds all your schemas and tables.
# We create one catalog per layer of the Medallion Architecture.

spark.sql("CREATE CATALOG IF NOT EXISTS bronze")
spark.sql("CREATE CATALOG IF NOT EXISTS silver")
spark.sql("CREATE CATALOG IF NOT EXISTS gold")

print("✅ Catalogs created: bronze, silver, gold")


# COMMAND ----------


# ---------------------------------------------------------------------------
# CELL 2 — Create Schemas inside each Catalog
# ---------------------------------------------------------------------------
# A "schema" (also called a database) is a folder inside a catalog.
# It groups related tables together.

spark.sql("CREATE SCHEMA IF NOT EXISTS bronze.superstore")
spark.sql("CREATE SCHEMA IF NOT EXISTS silver.superstore")
spark.sql("CREATE SCHEMA IF NOT EXISTS gold.superstore")

print("✅ Schemas created: superstore inside each catalog")


# COMMAND ----------


# ---------------------------------------------------------------------------
# CELL 3 — Create a Volume inside Bronze to store the raw CSV file
# ---------------------------------------------------------------------------
# A "Volume" is like a file system folder inside Databricks.
# We will upload the Superstore CSV here, and then read it in Notebook 01.

spark.sql("CREATE VOLUME IF NOT EXISTS bronze.superstore.raw_superstore")

print("✅ Volume created: bronze.superstore.raw_superstore")
print()
print("👉 NEXT STEP:")
print("   1. In the left sidebar, go to Catalog → bronze → superstore → raw_superstore")
print("   2. Click 'Upload to this volume'")
print("   3. Upload the file: Sample - Superstore.csv")
print("   4. Then run Notebook 01 — Bronze Layer")
