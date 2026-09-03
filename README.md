# 🛍️ E-commerce Analytics Dashboard

Dashboard interactivo (Streamlit + PostgreSQL + Docker) sobre `EcommData_CSV.csv`.

## Análisis del dataset

- 102,771 filas · 21 columnas · 0 nulos · 0 duplicados.
- 3,900 clientes únicos (`Customer ID`).
- `Age`, `Gender`, `Location`, `Subscription Status`, `Previous Purchases` y `Churn`
  son constantes por cliente → se modelan como tabla `customers` (dimensión).
- El resto de columnas varía por transacción → tabla `purchases` (hechos).
- Fechas: 2022-01-01 a 2024-12-31 (formato original `dd.mm.yyyy`, separador `;`,
  decimales con coma).

## Arquitectura

```
Streamlit (puerto 8501)  ──SQL──▶  PostgreSQL (puerto 5432)
```

Al levantar el contenedor `dashboard`, primero se ejecuta `db/load_data.py`
(crea el esquema y carga el CSV una sola vez) y luego arranca Streamlit.

## Cómo correrlo en este Codespace (3 pasos)

1. **Ubica el CSV**: crea la carpeta `data/` en la raíz del repo y coloca ahí
   `EcommData_CSV.csv` (si ya está en otra ruta del repo, simplemente muévelo
   o cópialo a `data/EcommData_CSV.csv`).

   ```bash
   mkdir -p data
   mv EcommData_CSV.csv data/   # ajusta la ruta si el CSV está en otro lugar
   ```

2. **Crea el archivo de variables de entorno** (las credenciales nunca van
   en el código):

   ```bash
   cp .env.example .env
   ```

   Puedes editar `.env` y poner tu propia contraseña si quieres.

3. **Levanta todo con Docker**:

   ```bash
   docker compose up --build
   ```

   Cuando termine de construir, el Codespace mostrará una notificación
   "Open in Browser" para el puerto **8501** (o ve a la pestaña **Ports**
   abajo y ábrelo ahí). Esa es tu dashboard.

Para apagarlo: `Ctrl + C` y luego `docker compose down` (o `docker compose down -v`
si además quieres borrar los datos cargados en PostgreSQL y recargar desde cero
la próxima vez).

## Estructura del proyecto

```
.
├── app/
│   ├── app.py        # Dashboard Streamlit (sidebar, KPIs, gráficas, explorador)
│   ├── db.py          # Conexión a PostgreSQL (env vars / st.secrets, sin credenciales en código)
│   └── queries.py     # Todas las consultas SQL y el armado de filtros
├── db/
│   ├── schema.sql      # customers + purchases + índices + vista v_purchases_full
│   └── load_data.py    # Carga el CSV a PostgreSQL (idempotente)
├── data/
│   └── EcommData_CSV.csv
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── .streamlit/config.toml   # tema oscuro
```

## Subir esto a GitHub desde el Codespace

Si quieres guardar estos cambios en tu repo:

```bash
git add .
git commit -m "Dashboard de e-commerce: Streamlit + PostgreSQL + Docker"
git push
```
