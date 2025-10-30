# syntax=docker/dockerfile:1
FROM python:3.11-slim

# System deps (optional, keep slim)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies first for better caching
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app ./app
COPY templates ./templates
COPY README.md ./README.md
COPY spec.yaml ./spec.yaml
COPY .env.example ./.env.example

EXPOSE 8000

ENV PYTHONUNBUFFERED=1

# The app loads .env automatically if provided (python-dotenv). You can mount one at runtime.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
