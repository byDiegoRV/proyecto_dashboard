FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ /app/
COPY db/ /db/
COPY .streamlit/ /app/.streamlit/

EXPOSE 8501

CMD ["sh", "-c", "python /db/load_data.py && streamlit run app.py --server.address=0.0.0.0"]
