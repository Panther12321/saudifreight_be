#!/usr/bin/env bash
set -euo pipefail

BENCH_PATH="${FRAPPE_BENCH_PATH:-/home/frappe/frappe-bench}"
APPS_FILE="${BENCH_PATH}/sites/apps.txt"

mkdir -p "$(dirname "${APPS_FILE}")"
touch "${APPS_FILE}"
grep -qxF "naqil" "${APPS_FILE}" || echo "naqil" >> "${APPS_FILE}"

exec "$@"
