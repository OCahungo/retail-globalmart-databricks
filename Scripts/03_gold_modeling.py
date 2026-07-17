# =============================================================================
# NOTEBOOK 03 — GOLD LAYER (Business Logic & Reporting)
# GlobalMart Retail Intelligence Pipeline


from pyspark.sql import functions as F

# Silver source tables
SILVER_FACT      = "silver.superstore.fact_orders"
SILVER_CUSTOMERS = "silver.superstore.dim_customers"
SILVER_PRODUCTS  = "silver.superstore.dim_products"
SILVER_DATE      = "silver.superstore.dim_date"

# Gold destination tables
GOLD_FACT_SALES           = "gold.superstore.fact_sales"
GOLD_DIM_CUSTOMER         = "gold.superstore.dim_customer"
GOLD_DIM_PRODUCT          = "gold.superstore.dim_product"
GOLD_DIM_DATE             = "gold.superstore.dim_date"
GOLD_PROFITABILITY        = "gold.superstore.agg_profitability_by_subcategory"
GOLD_SHIPPING_PERFORMANCE = "gold.superstore.agg_shipping_performance_by_region"
GOLD_TOP_CUSTOMERS        = "gold.superstore.agg_top_customers_by_spend"


fact      = spark.table(SILVER_FACT)
customers = spark.table(SILVER_CUSTOMERS)
products  = spark.table(SILVER_PRODUCTS)
dates     = spark.table(SILVER_DATE)

print("Silver tables loaded:")
print(f"  fact_orders   : {fact.count():,} rows")
print(f"  dim_customers : {customers.count():,} rows")
print(f"  dim_products  : {products.count():,} rows")
print(f"  dim_date      : {dates.count():,} rows")


customers.write.format("delta").mode("overwrite").saveAsTable(GOLD_DIM_CUSTOMER)
products.write.format("delta").mode("overwrite").saveAsTable(GOLD_DIM_PRODUCT)
dates.write.format("delta").mode("overwrite").saveAsTable(GOLD_DIM_DATE)

print(" Gold dimension tables written:")
print(f"   {GOLD_DIM_CUSTOMER}")
print(f"   {GOLD_DIM_PRODUCT}")
print(f"   {GOLD_DIM_DATE}")


df_joined = (
    fact
    .join(customers, on="customer_key", how="left")
    .join(products,  on="product_key",  how="left")
    .join(
        dates.select("date_key", "year", "month_number", "month_name", "quarter")
             .withColumnRenamed("date_key", "order_date_key")
             .withColumnRenamed("year", "order_year")
             .withColumnRenamed("month_number", "order_month_number")
             .withColumnRenamed("month_name", "order_month_name")
             .withColumnRenamed("quarter", "order_quarter"),
        on="order_date_key",
        how="left"
    )
)

# Step 2: Add derived metrics
fact_sales = (
    df_joined
    .withColumn(
        "delivery_days",
        F.datediff(F.col("ship_date"), F.col("order_date"))  # Ship date minus order date
    )
    .withColumn(
        "profit_margin_pct",
        F.round(
            F.when(F.col("sales_amount") != 0,
                   (F.col("profit_amount") / F.col("sales_amount")) * 100
            ).otherwise(0),
            2  
        )
    )
    .withColumn(
        "discounted_sales_amount",
        F.round(F.col("sales_amount") * (1 - F.col("discount_rate")), 2)
    )
    # Select final columns in a clean, logical order
    .select(
        "row_id", "order_id",
        "order_date", "ship_date", "order_year", "order_quarter",
        "order_month_number", "order_month_name",
        "customer_key", "customer_name", "customer_segment",
        "city", "state", "region", "country",
        "product_key", "product_name", "product_category", "product_sub_category",
        "shipping_mode", "order_quantity",
        "sales_amount", "discount_rate", "discounted_sales_amount",
        "profit_amount", "profit_margin_pct",
        "delivery_days"
    )
)

fact_sales.write.format("delta").mode("overwrite").saveAsTable(GOLD_FACT_SALES)

print(f" Gold fact_sales written: {fact_sales.count():,} rows → {GOLD_FACT_SALES}")
print()
print("Preview:")
fact_sales.select(
    "order_id", "customer_name", "product_sub_category",
    "sales_amount", "profit_margin_pct", "delivery_days"
).limit(5).display()


# Gold Aggregate 1: Profitability by Product Sub-Category

agg_profitability = (
    fact_sales
    .groupBy("product_category", "product_sub_category")
    .agg(
        F.sum("sales_amount").alias("total_sales"),
        F.sum("profit_amount").alias("total_profit"),
        F.count("row_id").alias("total_orders"),
        F.round(
            (F.sum("profit_amount") / F.sum("sales_amount")) * 100, 2
        ).alias("profit_margin_pct")  
    )
    .orderBy("profit_margin_pct")      
)

agg_profitability.write.format("delta").mode("overwrite").saveAsTable(GOLD_PROFITABILITY)

print(f" agg_profitability_by_subcategory written → {GOLD_PROFITABILITY}")
print()
print("Bottom 5 sub-categories by profit margin:")
agg_profitability.limit(5).display()


#Gold Aggregate 2: Shipping Performance by Region

agg_shipping = (
    fact_sales
    .groupBy("region", "shipping_mode")
    .agg(
        F.round(F.avg("delivery_days"), 1).alias("average_delivery_days"),
        F.min("delivery_days").alias("min_delivery_days"),
        F.max("delivery_days").alias("max_delivery_days"),
        F.count("row_id").alias("total_shipments")
    )
    .orderBy("region", "average_delivery_days")
)

agg_shipping.write.format("delta").mode("overwrite").saveAsTable(GOLD_SHIPPING_PERFORMANCE)

print(f" agg_shipping_performance_by_region written → {GOLD_SHIPPING_PERFORMANCE}")
print()
agg_shipping.display()


# Gold Aggregate 3: Top Customers by Total Spend (Year-to-Date)

# Find the latest year in the dataset
latest_year = fact_sales.agg(F.max("order_year")).collect()[0][0]
print(f"Latest year found in data: {latest_year}  → filtering to year-to-date")

agg_top_customers = (
    fact_sales
    .filter(F.col("order_year") == latest_year)   
    .groupBy("customer_key", "customer_name", "customer_segment", "region")
    .agg(
        F.round(F.sum("sales_amount"),  2).alias("total_spend"),
        F.round(F.sum("profit_amount"), 2).alias("total_profit_generated"),
        F.count("order_id").alias("total_orders"),
        F.countDistinct("order_id").alias("distinct_orders")
    )
    .orderBy(F.desc("total_spend"))    
    .limit(10)                          
    .withColumn("rank", F.monotonically_increasing_id() + 1) 
)

agg_top_customers.write.format("delta").mode("overwrite").saveAsTable(GOLD_TOP_CUSTOMERS)

print(f" agg_top_customers_by_spend written → {GOLD_TOP_CUSTOMERS}")
print()
print(f"Top 10 Customers in {latest_year}:")
agg_top_customers.select("rank", "customer_name", "customer_segment", "region", "total_spend").display()


# KPI Summary (for the Power BI KPI Card)

print("=" * 60)
print("DASHBOARD KPI SUMMARY")
print("=" * 60)

kpis = fact_sales.agg(
    F.round(F.sum("sales_amount"),   2).alias("Total Revenue"),
    F.round(F.sum("profit_amount"),  2).alias("Total Profit"),
    F.round(F.avg("profit_margin_pct"), 2).alias("Avg Profit Margin %"),
    F.countDistinct("order_id").alias("Total Orders"),
    F.round(F.avg("delivery_days"), 1).alias("Avg Delivery Days")
)

kpis.display()

print()
print(" Gold layer complete! All tables are ready for Power BI.")
print()
print("Tables to connect in Power BI:")
print(f"  1. {GOLD_FACT_SALES}           ← main fact table")
print(f"  2. {GOLD_DIM_CUSTOMER}")
print(f"  3. {GOLD_DIM_PRODUCT}")
print(f"  4. {GOLD_DIM_DATE}")
print(f"  5. {GOLD_PROFITABILITY}  ← for profitability chart")
print(f"  6. {GOLD_SHIPPING_PERFORMANCE}  ← for logistics chart")
print(f"  7. {GOLD_TOP_CUSTOMERS}   ← for top customers chart")
