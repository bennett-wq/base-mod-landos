FROM python:3.12-slim

WORKDIR /app

# Install Python deps
COPY landos/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY landos/ ./landos/

# Data directory — mount a persistent volume here in production
# The SQLite DB lives at /app/landos/data/landos.db
RUN mkdir -p /app/landos/data

WORKDIR /app/landos

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
