# Use the official lightweight python image
FROM python:3.11-slim

WORKDIR /app

# Install system deps required by some wheels (if any)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# Use gunicorn for production
# The module is main:app (app variable in main.py)
ENV PORT 8080
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "main:app", "--workers", "1", "--threads", "8", "--timeout", "120"]
