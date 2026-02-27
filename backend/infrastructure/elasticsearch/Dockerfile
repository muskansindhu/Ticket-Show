FROM python:3.11-slim

WORKDIR /app

COPY infrastructure/elasticsearch/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY infrastructure/elasticsearch/es_init.py .

CMD ["python", "es_init.py"]
