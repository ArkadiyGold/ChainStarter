FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir \
    streamlit pandas matplotlib sqlalchemy "psycopg[binary]" web3

COPY dashboard.py .

EXPOSE 8501

CMD ["streamlit", "run", "dashboard.py", "--server.address=0.0.0.0", "--server.port=8501"]