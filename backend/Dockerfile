FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir web3 psycopg2-binary

COPY ingest.py .
COPY schema.sql .
COPY marts.sql .

CMD ["python", "ingest.py"]