# =============================================================================
# NOTEBOOK 02 — SILVER LAYER (Cleaning & Dimension Tables)
# GlobalMart Retail Intelligence Pipeline
# =============================================================================
# PURPOSE:
#   Take the raw Bronze data and:
#     1. Rename columns to business-friendly names (no abbreviations/acronyms)
#     2. Fix data types (dates as proper timestamps, not strings)
#     3. Remove bad data (negative quantities = returns)
#     4. Handle nulls (missing City, Postal Code)
#     5. Create surrogate primary keys
#     6. Split into Dimension tables (Customers, Products, Dates) + a Fact table


from pyspark.sql import functions as F
from pyspark.sql.types import DateType

# Source table (output from Notebook 01)
BRONZE_TABLE = "bronze.superstore.raw_orders"

# Destination tables in Silver
SILVER_FACT_TABLE      = "silver.superstore.fact_orders"
SILVER_DIM_CUSTOMERS   = "silver.superstore.dim_customers"
SILVER_DIM_PRODUCTS    = "silver.superstore.dim_products"
SILVER_DIM_DATE        = "silver.superstore.dim_date"

print("cReading from:", BRONZE_TABLE)



df_bronze = spark.table(BRONZE_TABLE)

print(f"Rows in Bronze: {df_bronze.count():,}")
df_bronze.printSchema()

df_renamed = (
    df_bronze
    .withColumnRenamed("Row ID",        "row_id")
    .withColumnRenamed("Order ID",      "order_id")
    .withColumnRenamed("Order Date",    "order_date")
    .withColumnRenamed("Ship Date",     "ship_date")
    .withColumnRenamed("Ship Mode",     "shipping_mode")
    .withColumnRenamed("Customer ID",   "customer_id_raw")   
    .withColumnRenamed("Customer Name", "customer_name")
    .withColumnRenamed("Segment",       "customer_segment")
    .withColumnRenamed("Country",       "country")
    .withColumnRenamed("City",          "city")
    .withColumnRenamed("State",         "state")
    .withColumnRenamed("Postal Code",   "postal_code")
    .withColumnRenamed("Region",        "region")
    .withColumnRenamed("Product ID",    "product_id_raw")
    .withColumnRenamed("Category",      "product_category")
    .withColumnRenamed("Sub-Category",  "product_sub_category")
    .withColumnRenamed("Product Name",  "product_name")
    .withColumnRenamed("Sales",         "sales_amount")
    .withColumnRenamed("Quantity",      "order_quantity")
    .withColumnRenamed("Discount",      "discount_rate")
    .withColumnRenamed("Profit",        "profit_amount")
)

print(f" Columns renamed. Total columns: {len(df_renamed.columns)}")


df_typed = (
    df_renamed
    # Convert date strings like "01/03/2017" to proper date objects
    .withColumn("order_date", F.to_date(F.col("order_date"), "M/d/yyyy"))
    .withColumn("ship_date",  F.to_date(F.col("ship_date"),  "M/d/yyyy"))
    # Ensure numeric columns are the right type
    .withColumn("sales_amount",   F.col("sales_amount").cast("double"))
    .withColumn("order_quantity", F.col("order_quantity").cast("integer"))
    .withColumn("discount_rate",  F.col("discount_rate").cast("double"))
    .withColumn("profit_amount",  F.col("profit_amount").cast("double"))
    # Postal code stays as string (leading zeros, e.g. "01234")
    .withColumn("postal_code",    F.col("postal_code").cast("string"))
)

print(" Data types fixed.")
print("Checking date sample:")
df_typed.select("order_date", "ship_date").limit(3).display()


#Data Quality: Remove Bad Records

rows_before = df_typed.count()

df_clean = df_typed.filter(F.col("order_quantity") > 0)

rows_after = df_clean.count()
rows_removed = rows_before - rows_after

print(f"Rows before filter : {rows_before:,}")
print(f"Rows after filter  : {rows_after:,}")
print(f"Rows removed       : {rows_removed:,}  (returns/bad records)")



# Handle Null Values

df_nulls_handled = (
    df_clean
    .withColumn("city",        F.coalesce(F.col("city"),        F.lit("Unknown City")))
    .withColumn("postal_code", F.coalesce(F.col("postal_code"), F.lit("00000")))
)

# Check how many nulls remain (should be 0 for those columns)
print("Null check after handling:")
df_nulls_handled.select(
    F.sum(F.col("city").isNull().cast("int")).alias("null_city"),
    F.sum(F.col("postal_code").isNull().cast("int")).alias("null_postal_code")
).display()


# Create Surrogate Primary Keys (SHA-256 Hash Keys)

df_silver_full = (
    df_nulls_handled
    # Customer key: hash of name + city + postal code
    .withColumn("customer_key",
        F.sha2(F.concat_ws("|", F.col("customer_name"),
                                F.col("city"),
                                F.col("postal_code")), 256))
    # Product key: hash of product id
    .withColumn("product_key",
        F.sha2(F.col("product_id_raw"), 256))
    # Date key: integer in format YYYYMMDD (easy to join on)
    .withColumn("order_date_key",
        F.date_format(F.col("order_date"), "yyyyMMdd").cast("integer"))
    .withColumn("ship_date_key",
        F.date_format(F.col("ship_date"), "yyyyMMdd").cast("integer"))
)

print(" Surrogate keys created: customer_key, product_key, order_date_key, ship_date_key")


dim_customers = (
    df_silver_full
    .select(
        "customer_key",       
        "customer_id_raw",    
        "customer_name",
        "customer_segment",   
        "city",
        "state",
        "region",
        "country",
        "postal_code"
    )
    .distinct()               
)

dim_customers.write.format("delta").mode("overwrite").saveAsTable(SILVER_DIM_CUSTOMERS)

print(f" dim_customers saved: {dim_customers.count():,} rows → {SILVER_DIM_CUSTOMERS}")


# Create Dimension Table: dim_products

dim_products = (
    df_silver_full
    .select(
        "product_key",          
        "product_id_raw",       
        "product_name",
        "product_category",     
        "product_sub_category"   
    )
    .distinct()
)

dim_products.write.format("delta").mode("overwrite").saveAsTable(SILVER_DIM_PRODUCTS)

print(f" dim_products saved: {dim_products.count():,} rows → {SILVER_DIM_PRODUCTS}")

#Create Dimension Table: dim_date

dim_date = (
    df_silver_full
    .select(F.col("order_date").alias("calendar_date"))
    .union(df_silver_full.select(F.col("ship_date").alias("calendar_date")))
    .distinct()
    .filter(F.col("calendar_date").isNotNull())
    .withColumn("date_key",         F.date_format("calendar_date", "yyyyMMdd").cast("integer"))
    .withColumn("year",             F.year("calendar_date"))
    .withColumn("quarter",          F.quarter("calendar_date"))
    .withColumn("month_number",     F.month("calendar_date"))
    .withColumn("month_name",       F.date_format("calendar_date", "MMMM"))   
    .withColumn("week_of_year",     F.weekofyear("calendar_date"))
    .withColumn("day_of_month",     F.dayofmonth("calendar_date"))
    .withColumn("day_name",         F.date_format("calendar_date", "EEEE"))   
    .withColumn("is_weekend",       F.dayofweek("calendar_date").isin(1, 7))  # Sun=1, Sat=7
    .orderBy("calendar_date")
)

dim_date.write.format("delta").mode("overwrite").saveAsTable(SILVER_DIM_DATE)

print(f" dim_date saved: {dim_date.count():,} rows → {SILVER_DIM_DATE}")


# Create Fact Table: fact_orders

fact_orders = (
    df_silver_full
    .select(
        "row_id",              
        "order_id",            
        "order_date_key",      
        "ship_date_key",       
        "customer_key",        
        "product_key",         
        "shipping_mode",       
        "order_quantity",       
        "sales_amount",        
        "discount_rate",       
        "profit_amount",        
        "order_date",
        "ship_date"
    )
)

fact_orders.write.format("delta").mode("overwrite").saveAsTable(SILVER_FACT_TABLE)

print(f" fact_orders saved: {fact_orders.count():,} rows → {SILVER_FACT_TABLE}")


#  Validate Silver Layer

print("=" * 60)
print("SILVER LAYER VALIDATION")
print("=" * 60)

fact  = spark.table(SILVER_FACT_TABLE)
custs = spark.table(SILVER_DIM_CUSTOMERS)
prods = spark.table(SILVER_DIM_PRODUCTS)
dates = spark.table(SILVER_DIM_DATE)

print(f"fact_orders    : {fact.count():,} rows")
print(f"dim_customers  : {custs.count():,} rows")
print(f"dim_products   : {prods.count():,} rows")
print(f"dim_date       : {dates.count():,} rows")
print()

# Check for duplicates in the fact table
dup_count = fact.count() - fact.select("row_id").distinct().count()
print(f"Duplicate row_ids in fact table: {dup_count}  (should be 0)")

# Check for nulls in key columns
print(f"Null customer_key in fact: {fact.filter(F.col('customer_key').isNull()).count()}")
print(f"Null product_key in fact : {fact.filter(F.col('product_key').isNull()).count()}")
print()
print(" Silver layer ready!")
