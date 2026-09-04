FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ /app/
COPY db/ /db/
COPY .streamlit/ /app/.streamlit/
COPY data/ /data/

# Render (y otros PaaS) inyectan el puerto real en $PORT en tiempo de ejecución.
# En local (docker-compose) no se define, por eso el default a 8501.
ENV PORT=8501
EXPOSE 8501

CMD ["sh", "-c", "python /db/load_data.py && streamlit run app.py --server.address=0.0.0.0 --server.port=$PORT --server.enableXsrfProtection=false"]
