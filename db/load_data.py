"""
Carga EcommData_CSV.csv -> PostgreSQL (tablas customers / purchases).

Se ejecuta una sola vez al levantar el proyecto (o cada vez que se quiera
recargar desde cero). Es idempotente: si las tablas ya tienen datos, no
duplica (usa TRUNCATE antes de insertar).
"""
import os
import sys
import time

import pandas as pd
from sqlalchemy import create_engine, text

CSV_PATH = os.environ.get("CSV_PATH", "/data/EcommData_CSV.csv")

DB_HOST = os.environ.get("DB_HOST", "postgres")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "ecommerce")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "postgres")

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


def wait_for_db(engine, retries=20, delay=3):
    for i in range(retries):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("Conexion a PostgreSQL OK.")
            return
        except Exception as e:
            print(f"Esperando a PostgreSQL... intento {i+1}/{retries} ({e})")
            time.sleep(delay)
    print("No se pudo conectar a PostgreSQL. Abortando.")
    sys.exit(1)


def main():
    engine = create_engine(DATABASE_URL)
    wait_for_db(engine)

    # 1. Aplicar el esquema (tablas + indices + vista)
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()
    with engine.begin() as conn:
        conn.execute(text(schema_sql))
    print("Esquema aplicado (customers, purchases, indices, vista).")

    # 2. Si ya hay datos cargados, no repetir
    with engine.connect() as conn:
        count = conn.execute(text("SELECT COUNT(*) FROM purchases")).scalar()
    if count and count > 0:
        print(f"La tabla purchases ya tiene {count} filas. No se vuelve a cargar.")
        return

    # 3. Leer CSV (mismo formato detectado en el analisis: separador ';', decimales con ',')
    print(f"Leyendo CSV desde {CSV_PATH} ...")
    df = pd.read_csv(CSV_PATH, sep=";", decimal=",")

    # 4. Parsear fecha (formato dd.mm.yyyy)
    df["Purchase Date"] = pd.to_datetime(df["Purchase Date"], format="%d.%m.%Y")

    # 5. Construir tabla de clientes (dimension) - un registro por Customer ID
    customers = (
        df[["Customer ID", "Age", "Gender", "Location", "Subscription Status",
            "Previous Purchases", "Churn"]]
        .drop_duplicates(subset=["Customer ID"])
        .rename(columns={
            "Customer ID": "customer_id",
            "Age": "age",
            "Gender": "gender",
            "Location": "location",
            "Subscription Status": "subscription_status",
            "Previous Purchases": "previous_purchases",
            "Churn": "churn",
        })
    )
    customers["subscription_status"] = customers["subscription_status"].eq("Yes")
    customers["churn"] = customers["churn"].eq(1)

    # 6. Construir tabla de compras (hechos)
    purchases = df.rename(columns={
        "Customer ID": "customer_id",
        "Item Purchased": "item_purchased",
        "Category": "category",
        "Purchase Amount (USD)": "purchase_amount",
        "Size": "size",
        "Color": "color",
        "Season": "season",
        "Review Rating": "review_rating",
        "Shipping Type": "shipping_type",
        "Promo Code Used": "promo_code_used",
        "Payment Method": "payment_method",
        "Purchase Date": "purchase_date",
        "WeekdayNum": "weekday_num",
        "Weekday": "weekday_name",
        "Weekend": "is_weekend",
    })[[
        "customer_id", "item_purchased", "category", "purchase_amount",
        "size", "color", "season", "review_rating", "shipping_type",
        "promo_code_used", "payment_method", "purchase_date",
        "weekday_num", "weekday_name", "is_weekend",
    ]]
    purchases["promo_code_used"] = purchases["promo_code_used"].eq(1)
    purchases["is_weekend"] = purchases["is_weekend"].eq(1)

    # 7. Insertar (customers primero por la FK)
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE purchases, customers RESTART IDENTITY CASCADE"))
    customers.to_sql("customers", engine, if_exists="append", index=False, method="multi", chunksize=1000)
    print(f"Insertados {len(customers)} clientes.")
    purchases.to_sql("purchases", engine, if_exists="append", index=False, method="multi", chunksize=2000)
    print(f"Insertadas {len(purchases)} compras.")

    print("Carga completa.")


if __name__ == "__main__":
    main()
