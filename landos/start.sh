#!/bin/bash
# Railway startup script: run pipeline to populate DB, then start API server.
# The pipeline takes ~40s, then the API serves real data.

set -e

echo "=== LandOS API Startup ==="

# Run pipeline if DB doesn't exist or is older than 12 hours
DB_PATH="data/landos.db"
REFRESH=false

if [ ! -f "$DB_PATH" ]; then
    echo "No database found. Running pipeline..."
    REFRESH=true
elif [ "$(find "$DB_PATH" -mmin +720 2>/dev/null)" ]; then
    echo "Database older than 12 hours. Refreshing..."
    REFRESH=true
else
    echo "Database exists and is fresh. Skipping pipeline."
fi

if [ "$REFRESH" = true ]; then
    if [ -n "$SPARK_API_KEY" ]; then
        echo "Running full pipeline (Spark + Regrid)..."
        python3 scripts/run_pipeline_to_db.py --top 200 2>&1 || echo "Pipeline failed, starting API with existing data"
    else
        echo "No SPARK_API_KEY set. Running Regrid-only pipeline..."
        python3 scripts/run_pipeline_to_db.py --skip-spark 2>&1 || echo "Pipeline failed, starting API with existing data"
    fi
fi

echo "Starting API server on port ${PORT:-8000}..."
exec uvicorn api.main:app --host 0.0.0.0 --port "${PORT:-8000}"
