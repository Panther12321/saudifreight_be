#!/usr/bin/env bash
set -euo pipefail

: "${SITE_NAME:?SITE_NAME is required}"
BENCH_PATH="${FRAPPE_BENCH_PATH:-/home/frappe/frappe-bench}"
cd "${BENCH_PATH}"

if ! bench --site "${SITE_NAME}" list-apps | grep -qx "naqil"; then
  bench --site "${SITE_NAME}" install-app naqil
fi

bench --site "${SITE_NAME}" migrate
