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

site_database_exists() {
  mysql --host="${DB_HOST}" --port="${DB_PORT}" --user="${DB_ROOT_USER}" --password="${DB_ROOT_PASSWORD}" --batch --skip-column-names \
    --execute="SHOW DATABASES LIKE '${SITE_DB_NAME}'" | grep -qx "${SITE_DB_NAME}"
}

if ! site_database_exists; then
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
  bench --site "${SITE_NAME}" install-app naqil
fi

bench --site "${SITE_NAME}" migrate
