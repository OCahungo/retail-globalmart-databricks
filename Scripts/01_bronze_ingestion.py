# =============================================================================
# NOTEBOOK 01 — BRONZE LAYER (Raw Ingestion)
# GlobalMart Retail Intelligence Pipeline
# =============================================================================
# PURPOSE:
#   Read the raw CSV from the Volume, add metadata columns, and save it as a
#   Delta Table in the bronze catalog. This is the "as-is" copy of the data
#   — no cleaning happens here.
#
# KEY CONCEPT — IDEMPOTENCY:
#   Idempotency means: "I can run this notebook 10 times and still get the
#   same result." We achieve this by using MERGE (upsert) so that re-running
#   this notebook never creates duplicate rows.
#
# PREREQUISITE:
#   Run Notebook 00 first, and upload the CSV to the Volume.
# =============================================================================


# ---------------------------------------------------------------------------
# CELL 1 — Imports and Config
# ---------------------------------------------------------------------------
# PySpark functions we need. Think of these like importing a toolbox.

from pyspark.sql import functions as F   # F.col(), F.current_timestamp(), etc.
from delta.tables import DeltaTable      # Needed for the MERGE (upsert) operation

# Path to the CSV file you uploaded to the Volume
CSV_PATH = "/Volumes/bronze/superstore/raw_superstore/"

# Where we want to save the Bronze Delta Table
BRONZE_TABLE = "bronze.superstore.raw_orders"

print(f"📂 Reading from : {CSV_PATH}")
print(f"💾 Writing to   : {BRONZE_TABLE}")


# COMMAND ----------


# ---------------------------------------------------------------------------
# CELL 2 — Read the Raw CSV
# ---------------------------------------------------------------------------
# We tell Spark:
#   - The file has a header row (column names are in row 1)
#   - Try to figure out data types automatically (inferSchema)
#   - The file might have fields wrapped in quotes (multiLine handles edge cases)

df_raw = (
    spark.read
    .option("header", "true")         # Row 1 = column names
    .option("inferSchema", "true")    # Auto-detect data types (int, string, etc.)
    .option("multiLine", "true")      # Handle fields that contain commas inside quotes
    .csv(CSV_PATH)
)

print(f"📊 Rows read from CSV: {df_raw.count():,}")
print(f"📋 Columns found    : {len(df_raw.columns)}")
df_raw.printSchema()  # Shows column names and their detected data types


# COMMAND ----------


# ---------------------------------------------------------------------------
# CELL 3 — Add Metadata Columns
# ---------------------------------------------------------------------------
# In the Bronze layer, we add two extra columns that don't exist in the CSV:
#   - _ingest_timestamp : the exact moment this record was loaded (audit trail)
#   - _source_file      : which file this record came from (useful for debugging)

df_bronze = (
    df_raw
    .withColumn("_ingest_timestamp", F.current_timestamp())  # Timestamp of ingestion
    .withColumn("_source_file", F.input_file_name())         # Full path of source file
)

print("✅ Metadata columns added: _ingest_timestamp, _source_file")
df_bronze.limit(3).display()  # Preview the first 3 rows


# COMMAND ----------


# ---------------------------------------------------------------------------
# CELL 4 — Save to Delta Table (Idempotent using MERGE)
# ---------------------------------------------------------------------------
# We use a MERGE operation (also called "upsert"):
#   - If a row with the same Row ID already exists → UPDATE it
#   - If the row is brand new → INSERT it
#
# This means you can upload a new CSV with extra rows, re-run this notebook,
# and only the NEW rows get added. No duplicates!
#
# IMPORTANT: The Superstore CSV uses "Row ID" as the unique identifier per order.

MERGE_KEY = "`Row ID`"  # The column that uniquely identifies each record

# --- First run: if the table doesn't exist yet, just create it normally ---
if not spark.catalog.tableExists(BRONZE_TABLE):
    print(f"🆕 Table does not exist yet. Creating {BRONZE_TABLE} for the first time...")
    (
        df_bronze
        .write
        .format("delta")              # Delta format = versioned, ACID-compliant table
        .mode("overwrite")            # Safe on first run
        .option("overwriteSchema", "true")
        .saveAsTable(BRONZE_TABLE)
    )
    print(f"✅ Bronze table created with {df_bronze.count():,} rows.")

# --- Subsequent runs: MERGE to avoid duplicates ---
else:
    print(f"🔄 Table already exists. Merging new records into {BRONZE_TABLE}...")

    bronze_delta = DeltaTable.forName(spark, BRONZE_TABLE)  # Reference to existing table

    (
        bronze_delta.alias("existing")          # Existing data in the table
        .merge(
            df_bronze.alias("incoming"),         # New data coming from the CSV
            f"existing.{MERGE_KEY} = incoming.{MERGE_KEY}"  # Match on Row ID
        )
        .whenMatchedUpdateAll()                  # If Row ID matches → update all columns
        .whenNotMatchedInsertAll()               # If Row ID is new → insert the row
        .execute()
    )

    print(f"✅ Merge complete. Bronze table now has {spark.table(BRONZE_TABLE).count():,} rows.")


# COMMAND ----------


# ---------------------------------------------------------------------------
# CELL 5 — Validate the Bronze Table
# ---------------------------------------------------------------------------
# Quick sanity checks to confirm the data landed correctly.

df_check = spark.table(BRONZE_TABLE)

print("=" * 50)
print("BRONZE TABLE VALIDATION")
print("=" * 50)
print(f"Total rows        : {df_check.count():,}")
print(f"Total columns     : {len(df_check.columns)}")
print(f"Null Row IDs      : {df_check.filter(F.col('`Row ID`').isNull()).count()}")
print(f"Distinct Row IDs  : {df_check.select('`Row ID`').distinct().count():,}")
print()
print("Sample data:")
df_check.limit(5).display()
