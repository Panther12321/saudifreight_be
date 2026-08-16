#!/usr/bin/env bash
set -euo pipefail

BENCH_PATH="${FRAPPE_BENCH_PATH:-/home/frappe/frappe-bench}"
SITES_PATH="${BENCH_PATH}/sites"
APPS_FILE="${SITES_PATH}/apps.txt"
SERVICE_KIND="${NAQIL_SERVICE:-${1:-web}}"

if [[ "$(id -u)" == "0" ]]; then
  mkdir -p "${SITES_PATH}"
  chown -R frappe:frappe "${SITES_PATH}"
  exec runuser -u frappe -- "$0" "$@"
fi

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

write_combined_procfile() {
  cat > "${BENCH_PATH}/Procfile" <<'EOF'
web: bench serve --port ${PORT:-8000}
socketio: node apps/frappe/socketio.js
schedule: bench schedule
worker: bench worker --queue short,default,long
EOF
}

mkdir -p "$(dirname "${APPS_FILE}")"
touch "${APPS_FILE}"
if ! grep -qxF "naqil" "${APPS_FILE}"; then
  # Base images may omit a terminal newline in apps.txt. Prefixing the entry
  # with a newline prevents an invalid combined app name such as erpnextnaqil.
  printf "\nnaqil\n" >> "${APPS_FILE}"
fi

if [[ "${SERVICE_KIND}" == "migrate" ]]; then
  exec /usr/local/bin/naqil-migrate
fi

write_runtime_config

case "${SERVICE_KIND}" in
  combined)
    write_combined_procfile
    exec bench start
    ;;
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
  *)
    exec "$@"
    ;;
esac
