#!/usr/bin/env bash
set -euo pipefail

BENCH_PATH="${FRAPPE_BENCH_PATH:-/home/frappe/frappe-bench}"
SITES_PATH="${BENCH_PATH}/sites"
APPS_FILE="${SITES_PATH}/apps.txt"
SERVICE_KIND="${NAQIL_SERVICE:-${1:-web}}"

require_variable() {
  local key="$1"
  if [[ -z "${!key:-}" ]]; then
    echo "Missing required environment variable: ${key}" >&2
    exit 64
  fi
}

write_runtime_config() {
  require_variable SITE_NAME
  require_variable SITE_DB_NAME
  require_variable SITE_DB_PASSWORD
  require_variable DB_HOST
  require_variable DB_PORT
  require_variable REDIS_CACHE
  require_variable REDIS_QUEUE
  require_variable REDIS_SOCKETIO
  require_variable FRAPPE_ENCRYPTION_KEY

  mkdir -p "${SITES_PATH}/${SITE_NAME}"
  cat > "${SITES_PATH}/common_site_config.json" <<EOF
{
  "db_host": "${DB_HOST}",
  "db_port": ${DB_PORT},
  "redis_cache": "${REDIS_CACHE}",
  "redis_queue": "${REDIS_QUEUE}",
  "redis_socketio": "${REDIS_SOCKETIO}"
}
EOF
  cat > "${SITES_PATH}/${SITE_NAME}/site_config.json" <<EOF
{
  "db_name": "${SITE_DB_NAME}",
  "db_password": "${SITE_DB_PASSWORD}",
  "db_type": "mariadb",
  "encryption_key": "${FRAPPE_ENCRYPTION_KEY}"
}
EOF
}

mkdir -p "$(dirname "${APPS_FILE}")"
touch "${APPS_FILE}"
grep -qxF "naqil" "${APPS_FILE}" || echo "naqil" >> "${APPS_FILE}"

write_runtime_config

case "${SERVICE_KIND}" in
  web)
    exec gunicorn --chdir "${BENCH_PATH}" --bind "0.0.0.0:${PORT:-8000}" --workers "${GUNICORN_WORKERS:-2}" --threads "${GUNICORN_THREADS:-4}" --timeout "${GUNICORN_TIMEOUT:-120}" frappe.app:application
    ;;
  websocket)
    exec node "${BENCH_PATH}/apps/frappe/socketio.js"
    ;;
  worker-short)
    exec bench worker --queue short,default
    ;;
  worker-long)
    exec bench worker --queue long,default,short
    ;;
  scheduler)
    exec bench schedule
    ;;
  migrate)
    exec /usr/local/bin/naqil-migrate
    ;;
  *)
    exec "$@"
    ;;
esac
