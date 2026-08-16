#!/usr/bin/env bash
set -euo pipefail

: "${SITE_NAME:?SITE_NAME is required}"
: "${SITE_DB_NAME:?SITE_DB_NAME is required}"
: "${SITE_DB_PASSWORD:?SITE_DB_PASSWORD is required}"
: "${DB_HOST:?DB_HOST is required}"
: "${DB_PORT:?DB_PORT is required}"
: "${DB_ROOT_USER:?DB_ROOT_USER is required}"
: "${DB_ROOT_PASSWORD:?DB_ROOT_PASSWORD is required}"
: "${ADMIN_PASSWORD:?ADMIN_PASSWORD is required}"
BENCH_PATH="${FRAPPE_BENCH_PATH:-/home/frappe/frappe-bench}"
cd "${BENCH_PATH}"

if [[ ! -f "${BENCH_PATH}/sites/${SITE_NAME}/site_config.json" ]]; then
  bench new-site "${SITE_NAME}" \
    --db-name "${SITE_DB_NAME}" \
    --db-password "${SITE_DB_PASSWORD}" \
    --db-root-username "${DB_ROOT_USER}" \
    --db-root-password "${DB_ROOT_PASSWORD}" \
    --admin-password "${ADMIN_PASSWORD}" \
    --db-host "${DB_HOST}" \
    --db-port "${DB_PORT}" \
    --no-mariadb-socket
fi

if ! bench --site "${SITE_NAME}" list-apps | grep -qx "naqil"; then
  # A first install can create Module Def records before a transient worker
  # failure. --force makes the operation resumable without recreating data.
  bench --site "${SITE_NAME}" install-app naqil --force
fi

bench --site "${SITE_NAME}" migrate
