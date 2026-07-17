# =============================================================================
# NOTEBOOK 01 — BRONZE LAYER (Raw Ingestion)
# GlobalMart Retail Intelligence Pipeline
# =============================================================================


from pyspark.sql import functions as F   
from delta.tables import DeltaTable      


CSV_PATH = "/Volumes/bronze/superstore/raw_superstore/"

BRONZE_TABLE = "bronze.superstore.raw_orders"

print(f" Reading from : {CSV_PATH}")
print(f" Writing to   : {BRONZE_TABLE}")


df_raw = (
    spark.read
    .option("header", "true")         
    .option("inferSchema", "true")    
    .option("multiLine", "true")      
    .csv(CSV_PATH)
)

print(f" Rows read from CSV: {df_raw.count():,}")
print(f" Columns found    : {len(df_raw.columns)}")
df_raw.printSchema()  

df_bronze = (
    df_raw
    .withColumn("_ingest_timestamp", F.current_timestamp())  
    .withColumn("_source_file", F.input_file_name())         
)

print(" Metadata columns added: _ingest_timestamp, _source_file")
df_bronze.limit(3).display()  



MERGE_KEY = "`Row ID`"  

# Check if the table exist or just create it normally 
if not spark.catalog.tableExists(BRONZE_TABLE):
    print(f" Table does not exist yet. Creating {BRONZE_TABLE} for the first time...")
    (
        df_bronze
        .write
        .format("delta")              
        .mode("overwrite")            
        .option("overwriteSchema", "true")
        .saveAsTable(BRONZE_TABLE)
    )
    print(f" Bronze table created with {df_bronze.count():,} rows.")

# --- Subsequent runs: MERGE to avoid duplicates ---
else:
    print(f" Table already exists. Merging new records into {BRONZE_TABLE}...")

    bronze_delta = DeltaTable.forName(spark, BRONZE_TABLE)  

    (
        bronze_delta.alias("existing")         
        .merge(
            df_bronze.alias("incoming"),         
            f"existing.{MERGE_KEY} = incoming.{MERGE_KEY}"  
        )
        .whenMatchedUpdateAll()                  
        .whenNotMatchedInsertAll()              
        .execute()
    )

    print(f" Merge complete. Bronze table now has {spark.table(BRONZE_TABLE).count():,} rows.")


# sanity checks to confirm the data landed correctly.

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
