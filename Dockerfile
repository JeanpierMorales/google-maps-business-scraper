# Imagen oficial de Playwright: trae Chromium y sus dependencias del sistema.
FROM mcr.microsoft.com/playwright/python:v1.62.0-noble

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY . .
ENV PYTHONUNBUFFERED=1 CLOUD=1

# Un solo proceso: los trabajos viven en memoria. Hilos para el progreso en vivo.
CMD gunicorn app:app --bind 0.0.0.0:${PORT:-8080} --workers 1 --threads 8 --timeout 0
