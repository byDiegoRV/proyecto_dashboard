"""
Todas las consultas SQL del dashboard. Todo pasa por PostgreSQL (vista
v_purchases_full), nada se calcula leyendo el CSV directamente.

Los filtros se arman como WHERE parametrizado (nunca concatenando texto
del usuario directo en el SQL) para evitar inyección SQL.
"""
from __future__ import annotations

import pandas as pd

from db import run_query


def build_where(f: dict) -> tuple[str, dict]:
    """Convierte el diccionario de filtros del sidebar en una cláusula WHERE segura."""
    clauses = ["1=1"]
    params: dict = {}

    if f.get("date_from"):
        clauses.append("purchase_date >= :date_from")
        params["date_from"] = f["date_from"]
    if f.get("date_to"):
        clauses.append("purchase_date <= :date_to")
        params["date_to"] = f["date_to"]

    if f.get("gender"):
        clauses.append("gender = ANY(:gender)")
        params["gender"] = f["gender"]

    if f.get("age_range"):
        clauses.append("age BETWEEN :age_min AND :age_max")
        params["age_min"], params["age_max"] = f["age_range"]

    if f.get("subscription") is not None and f["subscription"] != "Todos":
        clauses.append("subscription_status = :subscription")
        params["subscription"] = (f["subscription"] == "Sí")

    if f.get("category"):
        clauses.append("category = ANY(:category)")
        params["category"] = f["category"]

    if f.get("item"):
        clauses.append("item_purchased = ANY(:item)")
        params["item"] = f["item"]

    if f.get("season"):
        clauses.append("season = ANY(:season)")
        params["season"] = f["season"]

    if f.get("promo") is not None and f["promo"] != "Todos":
        clauses.append("promo_code_used = :promo")
        params["promo"] = (f["promo"] == "Sí")

    if f.get("size"):
        clauses.append("size = ANY(:size)")
        params["size"] = f["size"]

    if f.get("color"):
        clauses.append("color = ANY(:color)")
        params["color"] = f["color"]

    if f.get("payment"):
        clauses.append("payment_method = ANY(:payment)")
        params["payment"] = f["payment"]

    if f.get("shipping"):
        clauses.append("shipping_type = ANY(:shipping)")
        params["shipping"] = f["shipping"]

    if f.get("location"):
        clauses.append("location = ANY(:location)")
        params["location"] = f["location"]

    if f.get("rating_range"):
        clauses.append("review_rating BETWEEN :rating_min AND :rating_max")
        params["rating_min"], params["rating_max"] = f["rating_range"]

    if f.get("prev_purchases_range"):
        clauses.append("previous_purchases BETWEEN :pp_min AND :pp_max")
        params["pp_min"], params["pp_max"] = f["prev_purchases_range"]

    if f.get("weekday"):
        clauses.append("weekday_name = ANY(:weekday)")
        params["weekday"] = f["weekday"]

    if f.get("weekend") is not None and f["weekend"] != "Todos":
        clauses.append("is_weekend = :weekend")
        params["weekend"] = (f["weekend"] == "Sí")

    if f.get("churn") is not None and f["churn"] != "Todos":
        clauses.append("churn = :churn")
        params["churn"] = (f["churn"] == "Sí")

    return " AND ".join(clauses), params


# ---------- Opciones para poblar los selects del sidebar ----------
def get_filter_options() -> dict:
    opts = {}
    opts["gender"] = run_query("SELECT DISTINCT gender FROM customers ORDER BY 1")["gender"].tolist()
    opts["category"] = run_query("SELECT DISTINCT category FROM purchases ORDER BY 1")["category"].tolist()
    opts["item"] = run_query("SELECT DISTINCT item_purchased FROM purchases ORDER BY 1")["item_purchased"].tolist()
    opts["season"] = run_query("SELECT DISTINCT season FROM purchases ORDER BY 1")["season"].tolist()
    opts["size"] = run_query("SELECT DISTINCT size FROM purchases ORDER BY 1")["size"].tolist()
    opts["color"] = run_query("SELECT DISTINCT color FROM purchases ORDER BY 1")["color"].tolist()
    opts["payment"] = run_query("SELECT DISTINCT payment_method FROM purchases ORDER BY 1")["payment_method"].tolist()
    opts["shipping"] = run_query("SELECT DISTINCT shipping_type FROM purchases ORDER BY 1")["shipping_type"].tolist()
    opts["location"] = run_query("SELECT DISTINCT location FROM customers ORDER BY 1")["location"].tolist()
    opts["weekday"] = run_query(
        "SELECT DISTINCT weekday_name, MIN(weekday_num) w FROM purchases GROUP BY weekday_name ORDER BY w"
    )["weekday_name"].tolist()
    row = run_query("SELECT MIN(age) mn, MAX(age) mx FROM customers").iloc[0]
    opts["age_bounds"] = (int(row["mn"]), int(row["mx"]))
    row = run_query("SELECT MIN(previous_purchases) mn, MAX(previous_purchases) mx FROM customers").iloc[0]
    opts["prev_purchases_bounds"] = (int(row["mn"]), int(row["mx"]))
    row = run_query("SELECT MIN(purchase_date) mn, MAX(purchase_date) mx FROM purchases").iloc[0]
    opts["date_bounds"] = (row["mn"], row["mx"])
    return opts


# ---------- KPIs ----------
def get_kpis(where: str, params: dict) -> dict:
    sql = f"""
        SELECT
            COALESCE(SUM(purchase_amount), 0)               AS total_sales,
            COUNT(*)                                          AS num_purchases,
            COALESCE(AVG(purchase_amount), 0)                AS avg_ticket,
            COUNT(DISTINCT customer_id)                       AS num_customers,
            COALESCE(AVG(review_rating), 0)                  AS avg_rating,
            COALESCE(AVG(CASE WHEN subscription_status THEN 1 ELSE 0 END) * 100, 0) AS pct_subscribed,
            COALESCE(AVG(CASE WHEN churn THEN 1 ELSE 0 END) * 100, 0)               AS pct_churn
        FROM v_purchases_full
        WHERE {where}
    """
    return run_query(sql, params).iloc[0].to_dict()


def get_record_count(where: str, params: dict) -> int:
    sql = f"SELECT COUNT(*) AS n FROM v_purchases_full WHERE {where}"
    return int(run_query(sql, params).iloc[0]["n"])


# ---------- Gráficas ----------
def sales_by_category(where, params) -> pd.DataFrame:
    return run_query(
        f"SELECT category, SUM(purchase_amount) AS ventas, COUNT(*) AS compras "
        f"FROM v_purchases_full WHERE {where} GROUP BY category ORDER BY ventas DESC",
        params,
    )


def sales_by_product(where, params) -> pd.DataFrame:
    return run_query(
        f"SELECT item_purchased AS producto, SUM(purchase_amount) AS ventas "
        f"FROM v_purchases_full WHERE {where} GROUP BY item_purchased ORDER BY ventas DESC",
        params,
    )


def sales_by_location(where, params) -> pd.DataFrame:
    return run_query(
        f"SELECT location, SUM(purchase_amount) AS ventas "
        f"FROM v_purchases_full WHERE {where} GROUP BY location ORDER BY ventas DESC LIMIT 15",
        params,
    )


def sales_by_payment(where, params) -> pd.DataFrame:
    return run_query(
        f"SELECT payment_method AS metodo_pago, SUM(purchase_amount) AS ventas "
        f"FROM v_purchases_full WHERE {where} GROUP BY payment_method ORDER BY ventas DESC",
        params,
    )


def sales_over_time(where, params) -> pd.DataFrame:
    return run_query(
        f"SELECT date_trunc('month', purchase_date)::date AS mes, SUM(purchase_amount) AS ventas "
        f"FROM v_purchases_full WHERE {where} GROUP BY 1 ORDER BY 1",
        params,
    )


def gender_distribution(where, params) -> pd.DataFrame:
    return run_query(
        f"SELECT gender, COUNT(DISTINCT customer_id) AS clientes "
        f"FROM v_purchases_full WHERE {where} GROUP BY gender",
        params,
    )


def age_distribution(where, params) -> pd.DataFrame:
    return run_query(
        f"SELECT age, COUNT(DISTINCT customer_id) AS clientes "
        f"FROM v_purchases_full WHERE {where} GROUP BY age ORDER BY age",
        params,
    )


def age_vs_amount(where, params) -> pd.DataFrame:
    return run_query(
        f"SELECT age, purchase_amount FROM v_purchases_full WHERE {where}",
        params,
    )


def sales_by_season(where, params) -> pd.DataFrame:
    return run_query(
        f"SELECT season, SUM(purchase_amount) AS ventas "
        f"FROM v_purchases_full WHERE {where} GROUP BY season",
        params,
    )


def promo_impact(where, params) -> pd.DataFrame:
    return run_query(
        f"SELECT promo_code_used, AVG(purchase_amount) AS ticket_promedio, COUNT(*) AS compras "
        f"FROM v_purchases_full WHERE {where} GROUP BY promo_code_used",
        params,
    )


def churn_distribution(where, params) -> pd.DataFrame:
    return run_query(
        f"SELECT churn, COUNT(DISTINCT customer_id) AS clientes "
        f"FROM v_purchases_full WHERE {where} GROUP BY churn",
        params,
    )


def subscription_distribution(where, params) -> pd.DataFrame:
    return run_query(
        f"SELECT subscription_status, COUNT(DISTINCT customer_id) AS clientes "
        f"FROM v_purchases_full WHERE {where} GROUP BY subscription_status",
        params,
    )


def rating_distribution(where, params) -> pd.DataFrame:
    return run_query(
        f"SELECT review_rating, COUNT(*) AS compras "
        f"FROM v_purchases_full WHERE {where} GROUP BY review_rating ORDER BY review_rating",
        params,
    )


# ---------- Explorador de datos ----------
def get_explorer_data(where: str, params: dict, search: str, limit: int, offset: int) -> pd.DataFrame:
    p = dict(params)
    search_clause = ""
    if search:
        search_clause = """ AND (
            item_purchased ILIKE :search OR category ILIKE :search OR location ILIKE :search
            OR color ILIKE :search OR payment_method ILIKE :search OR shipping_type ILIKE :search
        )"""
        p["search"] = f"%{search}%"
    p["limit"] = limit
    p["offset"] = offset
    sql = f"""
        SELECT purchase_id, customer_id, age, gender, location, item_purchased, category,
               purchase_amount, size, color, season, review_rating, subscription_status,
               shipping_type, promo_code_used, previous_purchases, payment_method,
               purchase_date, weekday_name, is_weekend, churn
        FROM v_purchases_full
        WHERE {where} {search_clause}
        ORDER BY purchase_date DESC
        LIMIT :limit OFFSET :offset
    """
    return run_query(sql, p)


def get_explorer_full(where: str, params: dict, search: str) -> pd.DataFrame:
    """Para descarga CSV: sin límite de filas."""
    p = dict(params)
    search_clause = ""
    if search:
        search_clause = """ AND (
            item_purchased ILIKE :search OR category ILIKE :search OR location ILIKE :search
            OR color ILIKE :search OR payment_method ILIKE :search OR shipping_type ILIKE :search
        )"""
        p["search"] = f"%{search}%"
    sql = f"""
        SELECT purchase_id, customer_id, age, gender, location, item_purchased, category,
               purchase_amount, size, color, season, review_rating, subscription_status,
               shipping_type, promo_code_used, previous_purchases, payment_method,
               purchase_date, weekday_name, is_weekend, churn
        FROM v_purchases_full
        WHERE {where} {search_clause}
        ORDER BY purchase_date DESC
    """
    return run_query(sql, p)
