# Use official lightweight Python 3.12 image
FROM python:3.12-slim

# Prevent Python from writing .pyc and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=5000
ENV ENVIRONMENT=production

# Set working directory inside container
WORKDIR /app

# Install system dependencies needed for compiling psycopg2 and C-extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency definition and install
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy application files
COPY . /app

# Run NLP training to ensure model artifacts are cached inside image
RUN python backend/nlp/train.py

# Make start script executable
RUN chmod +x /app/start.sh

# Expose default HTTP port
EXPOSE 5000

# Run entrypoint start script
CMD ["/bin/sh", "/app/start.sh"]
