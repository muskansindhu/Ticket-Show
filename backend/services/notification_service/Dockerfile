FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for Pillow and fonts
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libjpeg62-turbo-dev zlib1g-dev libfreetype6-dev \
        fonts-dejavu-core && \
    rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY ["services/notification_service/requirements.txt", "."]
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared modules
COPY shared /app/shared

# Copy application code
COPY ["services/notification_service/app", "/app/app"]

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
