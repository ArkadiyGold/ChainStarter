FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir web3

COPY simulate.py .

CMD ["python", "simulate.py"]