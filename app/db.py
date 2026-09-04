"""
Conexión a PostgreSQL para el dashboard.

Las credenciales NUNCA se escriben en el código: se leen de variables de
entorno (que en Docker vienen del .env / docker-compose.yml) o, si existe,
de st.secrets (útil si se despliega en Streamlit Community Cloud).
"""
import os
import pathlib

import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text

# Streamlit imprime un aviso en pantalla cada vez que se toca st.secrets
# sin que exista un secrets.toml. Por eso solo lo consultamos si el
# archivo realmente existe; si no, se va directo a variables de entorno.
_SECRETS_PATHS = [
    pathlib.Path("/app/.streamlit/secrets.toml"),
    pathlib.Path(".streamlit/secrets.toml"),
]


def _secrets_available() -> bool:
    return any(p.exists() for p in _SECRETS_PATHS)


def _get_conf(key: str, default: str = "") -> str:
    # Prioridad: st.secrets (solo si el archivo existe) -> variable de entorno -> default
    if _secrets_available():
        try:
            if key in st.secrets:
                return str(st.secrets[key])
        except Exception:
            pass
    return os.environ.get(key, default)


@st.cache_resource(show_spinner=False)
def get_engine():
    db_host = _get_conf("DB_HOST", "postgres")
    db_port = _get_conf("DB_PORT", "5432")
    db_name = _get_conf("DB_NAME", "ecommerce")
    db_user = _get_conf("DB_USER", "postgres")
    db_password = _get_conf("DB_PASSWORD", "postgres")

    url = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    return create_engine(url, pool_pre_ping=True)


@st.cache_data(ttl=600, show_spinner=False)
def run_query(sql: str, params: dict | None = None) -> pd.DataFrame:
    engine = get_engine()
    with engine.connect() as conn:
        return pd.read_sql(text(sql), conn, params=params or {})
