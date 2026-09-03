import datetime as dt

import plotly.express as px
import streamlit as st

import queries as q
from db import get_engine

st.set_page_config(page_title="E-commerce Analytics", page_icon="🛍️", layout="wide")

# ---------------------------------------------------------------- estilos
st.markdown(
    """
    <style>
    .kpi-card {
        background: linear-gradient(145deg, #161B22, #1C2230);
        border: 1px solid #2A3040;
        border-radius: 14px;
        padding: 18px 20px;
        text-align: left;
    }
    .kpi-label { font-size: 0.8rem; color: #9CA3AF; margin-bottom: 4px; }
    .kpi-value { font-size: 1.6rem; font-weight: 700; color: #F3F4F6; }
    section[data-testid="stSidebar"] { border-right: 1px solid #2A3040; }
    div[data-testid="stMetricValue"] { font-size: 1.4rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

PLOTLY_TEMPLATE = "plotly_dark"
ACCENT = "#7C5CFC"
ACCENT2 = "#22D3B6"


def kpi_card(col, label, value):
    with col:
        st.markdown(
            f'<div class="kpi-card"><div class="kpi-label">{label}</div>'
            f'<div class="kpi-value">{value}</div></div>',
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------- conexión + opciones
try:
    get_engine()
    opts = q.get_filter_options()
except Exception as e:
    st.error(
        "No se pudo conectar a PostgreSQL. Verifica que el contenedor de base de "
        f"datos esté corriendo y que las credenciales sean correctas.\n\nDetalle: {e}"
    )
    st.stop()

DEFAULTS = {
    "date_from": opts["date_bounds"][0],
    "date_to": opts["date_bounds"][1],
    "gender": opts["gender"],
    "age_range": opts["age_bounds"],
    "subscription": "Todos",
    "category": opts["category"],
    "item": opts["item"],
    "season": opts["season"],
    "promo": "Todos",
    "size": opts["size"],
    "color": opts["color"],
    "payment": opts["payment"],
    "shipping": opts["shipping"],
    "location": opts["location"],
    "rating_range": (1, 5),
    "prev_purchases_range": opts["prev_purchases_bounds"],
    "weekday": opts["weekday"],
    "weekend": "Todos",
    "churn": "Todos",
}

for k, v in DEFAULTS.items():
    st.session_state.setdefault(k, v)

# ---------------------------------------------------------------- sidebar
st.sidebar.markdown("## ⚙️ Filtros")

view_all = st.sidebar.checkbox("Ver todo el dataset (ignorar filtros)", value=False)

col_a, col_b = st.sidebar.columns(2)
if col_a.button("🔄 Limpiar", use_container_width=True):
    for k, v in DEFAULTS.items():
        st.session_state[k] = v
    st.rerun()
clear_placeholder = col_b.empty()  # reservado por simetría visual

with st.sidebar.expander("📅 Fecha", expanded=True):
    d_from, d_to = opts["date_bounds"]
    st.date_input("Fecha inicial", key="date_from", min_value=d_from, max_value=d_to)
    st.date_input("Fecha final", key="date_to", min_value=d_from, max_value=d_to)

with st.sidebar.expander("👤 Cliente"):
    st.multiselect("Género", opts["gender"], key="gender")
    st.slider("Rango de edad", opts["age_bounds"][0], opts["age_bounds"][1], key="age_range")
    st.selectbox("Suscripción", ["Todos", "Sí", "No"], key="subscription")

with st.sidebar.expander("🛍️ Compra"):
    st.multiselect("Categoría", opts["category"], key="category")
    st.multiselect("Producto", opts["item"], key="item")
    st.multiselect("Temporada", opts["season"], key="season")
    st.selectbox("Código promocional usado", ["Todos", "Sí", "No"], key="promo")
    st.multiselect("Talla", opts["size"], key="size")
    st.multiselect("Color", opts["color"], key="color")

with st.sidebar.expander("💳 Pago y envío"):
    st.multiselect("Método de pago", opts["payment"], key="payment")
    st.multiselect("Tipo de envío", opts["shipping"], key="shipping")

with st.sidebar.expander("📍 Ubicación"):
    st.multiselect("Estado", opts["location"], key="location")

with st.sidebar.expander("📊 Otros"):
    st.slider("Calificación", 1, 5, key="rating_range")
    st.slider(
        "Compras anteriores",
        opts["prev_purchases_bounds"][0],
        opts["prev_purchases_bounds"][1],
        key="prev_purchases_range",
    )
    st.multiselect("Día de la semana", opts["weekday"], key="weekday")
    st.selectbox("Fin de semana", ["Todos", "Sí", "No"], key="weekend")
    st.selectbox("Churn", ["Todos", "Sí", "No"], key="churn")

filters = {k: st.session_state[k] for k in DEFAULTS}
where, params = ("1=1", {}) if view_all else q.build_where(filters)

record_count = q.get_record_count(where, params)
st.sidebar.markdown(f"**🔢 Registros encontrados:** {record_count:,}")

# ---------------------------------------------------------------- header + KPIs
st.title("🛍️ E-commerce Analytics Dashboard")
st.caption("Datos servidos en vivo desde PostgreSQL · se actualiza automáticamente con los filtros")

kpis = q.get_kpis(where, params)

c1, c2, c3, c4 = st.columns(4)
kpi_card(c1, "💰 Ventas totales", f"${kpis['total_sales']:,.0f}")
kpi_card(c2, "🛒 Compras", f"{int(kpis['num_purchases']):,}")
kpi_card(c3, "💵 Ticket promedio", f"${kpis['avg_ticket']:,.2f}")
kpi_card(c4, "👥 Clientes", f"{int(kpis['num_customers']):,}")

c5, c6, c7 = st.columns(3)
kpi_card(c5, "⭐ Calificación promedio", f"{kpis['avg_rating']:.2f} / 5")
kpi_card(c6, "📈 % Suscripción", f"{kpis['pct_subscribed']:.1f}%")
kpi_card(c7, "📉 % Churn", f"{kpis['pct_churn']:.1f}%")

st.write("")

tab_resumen, tab_explorador = st.tabs(["📊 Resumen", "🔎 Explorador de datos"])

# ================================================================ TAB RESUMEN
with tab_resumen:
    st.subheader("Ventas")
    col1, col2 = st.columns(2)
    with col1:
        df = q.sales_by_category(where, params)
        fig = px.bar(df, x="category", y="ventas", template=PLOTLY_TEMPLATE,
                     color_discrete_sequence=[ACCENT], title="Ventas por categoría")
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        df = q.sales_by_product(where, params)
        fig = px.bar(df, x="producto", y="ventas", template=PLOTLY_TEMPLATE,
                     color_discrete_sequence=[ACCENT2], title="Ventas por producto")
        st.plotly_chart(fig, use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        df = q.sales_by_location(where, params)
        fig = px.bar(df, x="ventas", y="location", orientation="h", template=PLOTLY_TEMPLATE,
                     color_discrete_sequence=[ACCENT], title="Top 15 ubicaciones por ventas")
        fig.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, use_container_width=True)
    with col4:
        df = q.sales_by_payment(where, params)
        fig = px.pie(df, names="metodo_pago", values="ventas", template=PLOTLY_TEMPLATE,
                     title="Ventas por método de pago", hole=0.45)
        st.plotly_chart(fig, use_container_width=True)

    df = q.sales_over_time(where, params)
    fig = px.line(df, x="mes", y="ventas", template=PLOTLY_TEMPLATE, markers=True,
                  color_discrete_sequence=[ACCENT2], title="Evolución de ventas por mes")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Clientes")
    col5, col6 = st.columns(2)
    with col5:
        df = q.gender_distribution(where, params)
        fig = px.pie(df, names="gender", values="clientes", template=PLOTLY_TEMPLATE,
                     title="Distribución de clientes por género", hole=0.45)
        st.plotly_chart(fig, use_container_width=True)
    with col6:
        df = q.age_distribution(where, params)
        fig = px.bar(df, x="age", y="clientes", template=PLOTLY_TEMPLATE,
                     color_discrete_sequence=[ACCENT], title="Distribución de edades")
        st.plotly_chart(fig, use_container_width=True)

    df = q.age_vs_amount(where, params)
    fig = px.scatter(df, x="age", y="purchase_amount", template=PLOTLY_TEMPLATE,
                     opacity=0.35, color_discrete_sequence=[ACCENT2],
                     title="Relación entre edad y monto de compra",
                     labels={"age": "Edad", "purchase_amount": "Monto (USD)"})
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Comportamiento")
    col7, col8, col9 = st.columns(3)
    with col7:
        df = q.sales_by_season(where, params)
        fig = px.bar(df, x="season", y="ventas", template=PLOTLY_TEMPLATE,
                     color_discrete_sequence=[ACCENT], title="Ventas según temporada")
        st.plotly_chart(fig, use_container_width=True)
    with col8:
        df = q.promo_impact(where, params)
        df["promo_code_used"] = df["promo_code_used"].map({True: "Con promoción", False: "Sin promoción"})
        fig = px.bar(df, x="promo_code_used", y="ticket_promedio", template=PLOTLY_TEMPLATE,
                     color_discrete_sequence=[ACCENT2], title="Impacto de promociones en ticket promedio")
        st.plotly_chart(fig, use_container_width=True)
    with col9:
        df = q.rating_distribution(where, params)
        fig = px.bar(df, x="review_rating", y="compras", template=PLOTLY_TEMPLATE,
                     color_discrete_sequence=[ACCENT], title="Distribución de calificaciones")
        st.plotly_chart(fig, use_container_width=True)

    col10, col11 = st.columns(2)
    with col10:
        df = q.subscription_distribution(where, params)
        df["subscription_status"] = df["subscription_status"].map({True: "Suscrito", False: "No suscrito"})
        fig = px.pie(df, names="subscription_status", values="clientes", template=PLOTLY_TEMPLATE,
                     title="Suscripción", hole=0.45)
        st.plotly_chart(fig, use_container_width=True)
    with col11:
        df = q.churn_distribution(where, params)
        df["churn"] = df["churn"].map({True: "Churn", False: "Activo"})
        fig = px.pie(df, names="churn", values="clientes", template=PLOTLY_TEMPLATE,
                     title="Churn de clientes", hole=0.45,
                     color_discrete_sequence=["#EF4444", ACCENT2])
        st.plotly_chart(fig, use_container_width=True)

# ================================================================ TAB EXPLORADOR
with tab_explorador:
    st.subheader("Explorador de datos")
    search = st.text_input("🔎 Buscar (producto, categoría, ubicación, color, pago, envío)")

    left, right = st.columns([3, 1])
    with right:
        page_size = st.selectbox("Filas por página", [25, 50, 100, 250], index=1)
    total_rows = q.get_record_count(
        (where + (" AND (item_purchased ILIKE :s OR category ILIKE :s OR location ILIKE :s "
                  "OR color ILIKE :s OR payment_method ILIKE :s OR shipping_type ILIKE :s)")
         if search else where),
        {**params, **({"s": f"%{search}%"} if search else {})},
    )
    max_page = max(1, -(-total_rows // page_size))
    with left:
        page = st.number_input("Página", min_value=1, max_value=max_page, value=1, step=1)

    st.caption(f"Mostrando página {page} de {max_page} · {total_rows:,} registros en total")

    df_page = q.get_explorer_data(where, params, search, limit=page_size, offset=(page - 1) * page_size)
    st.dataframe(df_page, use_container_width=True, height=500)

    st.download_button(
        "⬇️ Descargar resultados filtrados (CSV)",
        data=q.get_explorer_full(where, params, search).to_csv(index=False).encode("utf-8"),
        file_name="ecommerce_filtrado.csv",
        mime="text/csv",
    )
