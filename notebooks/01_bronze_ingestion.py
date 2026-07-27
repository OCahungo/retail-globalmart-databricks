from pyspark.sql import functions as F

CSV_PATH = "/Volumes/bronze/superstore/raw_superstore/"
BRONZE_TABLE = "bronze.superstore.raw_superstore"

spark.sql(f"DROP TABLE IF EXISTS {BRONZE_TABLE}")

print(f" Reading from : {CSV_PATH}")
print(f" Writing to   : {BRONZE_TABLE}")

df_raw = (
    spark.read
    .option("header", "true")         
    .option("multiLine", "true")      
    .csv(CSV_PATH)
)

colunas_limpas = [F.col(f"`{c}`").alias(c.strip().replace(" ", "_")) for c in df_raw.columns]
df_with_clean_cols = df_raw.select(colunas_limpas)

df_bronze = (
    df_with_clean_cols
    .withColumn("_ingest_timestamp", F.current_timestamp())  
    .withColumn("_source_file", F.col("_metadata.file_path"))         
)

(
    df_bronze
    .write
    .format("delta")              
    .mode("overwrite")  #Em sistemas de produção normalmente é para usar append e não overwrite na camada bronze, mas eu estou a testar apenas com um ficheiro por essa razão estou a utilizar o overwrite método         
    .option("overwriteSchema", "true") 
    .saveAsTable(BRONZE_TABLE)
)

print(f" Data successfully landed into Bronze table: {BRONZE_TABLE}")
