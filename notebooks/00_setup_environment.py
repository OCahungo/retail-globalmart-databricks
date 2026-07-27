# =============================================================================
# NENVIRONMENT SETUP
# GlobalMart Retail Intelligence Pipeline
# =============================================================================
# PURPOSE:
#   (bronze, silver, gold) and the schemas/volumes you will need before running any other notebook.


spark.sql("CREATE CATALOG IF NOT EXISTS bronze")
spark.sql("CREATE CATALOG IF NOT EXISTS silver")
spark.sql("CREATE CATALOG IF NOT EXISTS gold")

print(" Catalogs created: bronze, silver, gold")

spark.sql("CREATE SCHEMA IF NOT EXISTS bronze.superstore")
spark.sql("CREATE SCHEMA IF NOT EXISTS silver.superstore")
spark.sql("CREATE SCHEMA IF NOT EXISTS gold.superstore")

print(" Schemas created: superstore inside each catalog")

spark.sql("CREATE VOLUME IF NOT EXISTS bronze.superstore.raw_superstore")

print(" Volume created: bronze.superstore.raw_superstore")
