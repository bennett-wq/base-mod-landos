#!/usr/bin/env bash
# daily_pipeline.sh — Run LandOS pipeline daily, log output, notify on failure.
#
# Usage:
#   ./landos/scripts/daily_pipeline.sh          # normal run
#   ./landos/scripts/daily_pipeline.sh --dry-run # print what would happen
#
# Called by: com.basemodhomes.landos-pipeline launchd plist
# Writes to: landos/logs/pipeline_YYYY-MM-DD.log
#
# Install the daily schedule:
#   cp landos/scripts/com.basemodhomes.landos-pipeline.plist ~/Library/LaunchAgents/
#   launchctl load ~/Library/LaunchAgents/com.basemodhomes.landos-pipeline.plist
#
# Uninstall:
#   launchctl unload ~/Library/LaunchAgents/com.basemodhomes.landos-pipeline.plist
#   rm ~/Library/LaunchAgents/com.basemodhomes.landos-pipeline.plist
#
# Manual run:
#   launchctl start com.basemodhomes.landos-pipeline
#
# Check status:
#   launchctl list | grep landos

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
LANDOS_DIR="${PROJECT_ROOT}/landos"
VENV="${PROJECT_ROOT}/.venv"
LOG_DIR="${LANDOS_DIR}/logs"
ENV_FILE="${PROJECT_ROOT}/.env"

# Ensure log directory exists
mkdir -p "${LOG_DIR}"

DATE_STAMP="$(date +%Y-%m-%d)"
TIMESTAMP="$(date '+%Y-%m-%d %H:%M:%S')"
LOG_FILE="${LOG_DIR}/pipeline_${DATE_STAMP}.log"

# Dry-run mode
if [[ "${1:-}" == "--dry-run" ]]; then
    echo "DRY RUN — would execute:"
    echo "  Project root: ${PROJECT_ROOT}"
    echo "  Python: ${VENV}/bin/python3"
    echo "  Script: ${LANDOS_DIR}/scripts/run_pipeline_to_db.py"
    echo "  Log: ${LOG_FILE}"
    echo "  Env: ${ENV_FILE}"
    exit 0
fi

# Load .env (for SPARK_API_KEY)
if [[ -f "${ENV_FILE}" ]]; then
    set -a
    source "${ENV_FILE}"
    set +a
else
    echo "[${TIMESTAMP}] ERROR: .env not found at ${ENV_FILE}" | tee -a "${LOG_FILE}"
    exit 1
fi

# Verify SPARK_API_KEY is set
if [[ -z "${SPARK_API_KEY:-}" ]]; then
    echo "[${TIMESTAMP}] ERROR: SPARK_API_KEY not set in .env" | tee -a "${LOG_FILE}"
    exit 1
fi

# Verify venv exists
if [[ ! -f "${VENV}/bin/python3" ]]; then
    echo "[${TIMESTAMP}] ERROR: Python venv not found at ${VENV}" | tee -a "${LOG_FILE}"
    exit 1
fi

echo "========================================" >> "${LOG_FILE}"
echo "[${TIMESTAMP}] Pipeline run starting" >> "${LOG_FILE}"
echo "========================================" >> "${LOG_FILE}"

# Run the pipeline
if "${VENV}/bin/python3" "${LANDOS_DIR}/scripts/run_pipeline_to_db.py" \
    --top 200 --historical >> "${LOG_FILE}" 2>&1; then
    END_TIME="$(date '+%Y-%m-%d %H:%M:%S')"
    echo "[${END_TIME}] Pipeline completed successfully" >> "${LOG_FILE}"
else
    EXIT_CODE=$?
    END_TIME="$(date '+%Y-%m-%d %H:%M:%S')"
    echo "[${END_TIME}] Pipeline FAILED (exit code ${EXIT_CODE})" >> "${LOG_FILE}"

    # macOS notification on failure
    osascript -e "display notification \"Pipeline failed — check ${LOG_FILE}\" with title \"LandOS Pipeline\" sound name \"Basso\"" 2>/dev/null || true

    exit ${EXIT_CODE}
fi

# Prune logs older than 30 days
find "${LOG_DIR}" -name "pipeline_*.log" -mtime +30 -delete 2>/dev/null || true
