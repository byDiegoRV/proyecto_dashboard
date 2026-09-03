-- ============================================================
-- Esquema: ecommerce_dashboard
-- Diseño: estrella simple (customers = dimensión, purchases = hechos)
--
-- Por qué esta estructura:
--   Al analizar el CSV se confirmó que Age, Gender, Location,
--   Subscription Status, Previous Purchases y Churn son constantes
--   por Customer ID (no cambian entre filas del mismo cliente).
--   Son atributos DEL CLIENTE, no de cada compra. Separarlos evita
--   redundancia (guardar 26 veces el mismo Age/Location por cliente)
--   y hace que los filtros de cliente y las agregaciones sean más
--   rápidas y consistentes.
-- ============================================================

CREATE TABLE IF NOT EXISTS customers (
    customer_id          INTEGER PRIMARY KEY,              -- viene del CSV, es identificador natural -> PK directa
    age                  SMALLINT NOT NULL CHECK (age BETWEEN 0 AND 120),
    gender                VARCHAR(10) NOT NULL,             -- solo 2 valores (Male/Female), texto corto
    location              VARCHAR(50) NOT NULL,             -- nombres de estado (EEUU), longitud variable
    subscription_status  BOOLEAN NOT NULL,                 -- Yes/No -> booleano real, no texto
    previous_purchases   SMALLINT NOT NULL DEFAULT 0 CHECK (previous_purchases >= 0),
    churn                 BOOLEAN NOT NULL                  -- 0/1 -> booleano real
);

CREATE TABLE IF NOT EXISTS purchases (
    purchase_id           BIGSERIAL PRIMARY KEY,            -- no existe ID natural de compra en el CSV -> serial autogenerado
    customer_id            INTEGER NOT NULL REFERENCES customers(customer_id),
    item_purchased          VARCHAR(50) NOT NULL,
    category                VARCHAR(30) NOT NULL,
    purchase_amount         NUMERIC(10,2) NOT NULL CHECK (purchase_amount >= 0), -- dinero -> NUMERIC, nunca FLOAT (evita errores de redondeo)
    size                     VARCHAR(5),
    color                    VARCHAR(20),
    season                   VARCHAR(10),
    review_rating           NUMERIC(2,1) CHECK (review_rating BETWEEN 1 AND 5), -- rating 1.0-5.0 con 1 decimal
    shipping_type           VARCHAR(20),
    promo_code_used          BOOLEAN NOT NULL DEFAULT FALSE,
    payment_method           VARCHAR(20),
    purchase_date            DATE NOT NULL,                  -- fecha real DATE, no texto, permite filtros de rango y funciones de fecha
    weekday_num              SMALLINT,
    weekday_name             VARCHAR(10),
    is_weekend               BOOLEAN NOT NULL DEFAULT FALSE
);

-- Índices para acelerar los filtros y agregaciones que usa el dashboard
CREATE INDEX IF NOT EXISTS idx_purchases_customer_id   ON purchases (customer_id);
CREATE INDEX IF NOT EXISTS idx_purchases_date           ON purchases (purchase_date);
CREATE INDEX IF NOT EXISTS idx_purchases_category       ON purchases (category);
CREATE INDEX IF NOT EXISTS idx_purchases_item           ON purchases (item_purchased);
CREATE INDEX IF NOT EXISTS idx_purchases_payment        ON purchases (payment_method);
CREATE INDEX IF NOT EXISTS idx_purchases_season         ON purchases (season);
CREATE INDEX IF NOT EXISTS idx_customers_location        ON customers (location);
CREATE INDEX IF NOT EXISTS idx_customers_gender          ON customers (gender);
CREATE INDEX IF NOT EXISTS idx_customers_subscription    ON customers (subscription_status);
CREATE INDEX IF NOT EXISTS idx_customers_churn           ON customers (churn);

-- Vista que junta todo, para que las consultas del dashboard sean simples
CREATE OR REPLACE VIEW v_purchases_full AS
SELECT
    p.purchase_id,
    p.customer_id,
    c.age,
    c.gender,
    c.location,
    c.subscription_status,
    c.previous_purchases,
    c.churn,
    p.item_purchased,
    p.category,
    p.purchase_amount,
    p.size,
    p.color,
    p.season,
    p.review_rating,
    p.shipping_type,
    p.promo_code_used,
    p.payment_method,
    p.purchase_date,
    p.weekday_num,
    p.weekday_name,
    p.is_weekend
FROM purchases p
JOIN customers c ON c.customer_id = p.customer_id;
