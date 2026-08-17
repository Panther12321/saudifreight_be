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

  mkdir -p \
    "${SITES_PATH}/${SITE_NAME}/logs" \
    "${SITES_PATH}/${SITE_NAME}/private/files" \
    "${SITES_PATH}/${SITE_NAME}/public/files"
  cat > "${SITES_PATH}/common_site_config.json" <<EOF
{
  "db_host": "${DB_HOST}",
  "db_port": ${DB_PORT},
  "redis_cache": "${REDIS_CACHE}",
  "redis_queue": "${REDIS_QUEUE}",
  "redis_socketio": "${REDIS_SOCKETIO}",
  "default_site": "${SITE_NAME}"
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
  touch "${SITES_PATH}/${SITE_NAME}/logs/frappe.log"
}

write_combined_procfile() {
  cat > "${BENCH_PATH}/nginx.conf" <<EOF
pid /tmp/naqil-nginx.pid;
error_log /dev/stderr warn;

events {
  worker_connections 1024;
}

http {
  include /etc/nginx/mime.types;
  default_type application/octet-stream;
  access_log /dev/stdout;
  client_body_temp_path /tmp/naqil-nginx-client;
  proxy_temp_path /tmp/naqil-nginx-proxy;
  fastcgi_temp_path /tmp/naqil-nginx-fastcgi;
  uwsgi_temp_path /tmp/naqil-nginx-uwsgi;
  scgi_temp_path /tmp/naqil-nginx-scgi;

  server {
    listen ${PORT:-8000};
    server_name _;

    location /socket.io {
      proxy_http_version 1.1;
      proxy_set_header Upgrade \$http_upgrade;
      proxy_set_header Connection "upgrade";
      proxy_set_header Host \$host;
      proxy_set_header X-Frappe-Site-Name ${SITE_NAME};
      proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
      proxy_set_header X-Forwarded-Proto \$scheme;
      proxy_pass http://127.0.0.1:9000;
    }

    location / {
      proxy_http_version 1.1;
      proxy_set_header Host \$host;
      proxy_set_header X-Frappe-Site-Name ${SITE_NAME};
      proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
      proxy_set_header X-Forwarded-Proto \$scheme;
      proxy_read_timeout 120;
      proxy_pass http://127.0.0.1:8001;
    }
  }
}
EOF

  cat > "${BENCH_PATH}/Procfile" <<'EOF'
proxy: nginx -c /home/frappe/frappe-bench/nginx.conf -g 'daemon off;'
web: bench serve --port 8001
socketio: node apps/frappe/socketio.js
schedule: bench schedule
worker: bench worker --queue short,default,long
EOF
}

write_site_hostname_alias() {
  if [[ -n "${SITE_HOSTNAME:-}" && "${SITE_HOSTNAME}" != "${SITE_NAME}" ]]; then
    ln -sfn "${SITE_NAME}" "${SITES_PATH}/${SITE_HOSTNAME}"
  fi
}

write_default_site() {
  printf "%s\n" "${SITE_NAME}" > "${SITES_PATH}/currentsite.txt"
}

sync_site_definitions() {
  if [[ "${NAQIL_AUTO_MIGRATE:-1}" != "1" ]]; then
    return
  fi
  bench --site "${SITE_NAME}" migrate
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
write_default_site
write_site_hostname_alias

if [[ "${SERVICE_KIND}" == "combined" ]]; then
  sync_site_definitions
fi

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
