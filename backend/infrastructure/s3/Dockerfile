FROM python:3.11-slim

WORKDIR /app

COPY backend/infrastructure/s3/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/infrastructure/s3/s3_init.py .
COPY frontend/src/assets/posters/ /app/posters/

CMD ["python", "s3_init.py"]
