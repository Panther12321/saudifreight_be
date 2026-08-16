# Railway Service Map

Railway imports multi-service Docker Compose as individual services. The production topology below is the preferred scalable design. The currently deployed starter configuration uses a single combined Frappe service because the available Railway plan permits only one application service alongside MariaDB and Redis.

| Railway service | Image / command | Required private dependencies | Public exposure |
|---|---|---|---|
| `naqil-backend` | This repository’s Docker image running the Frappe web process | MariaDB, Redis cache, Redis queue, Redis Socket.IO | Yes, HTTPS domain |
| `naqil-websocket` | Same image running Socket.IO | Redis Socket.IO | Optional; expose only through the configured proxy/domain route |
| `naqil-worker-short` | Same image running the short/default worker | Redis queue, MariaDB | No |
| `naqil-worker-long` | Same image running the long worker | Redis queue, MariaDB | No |
| `naqil-scheduler` | Same image running `bench schedule` | Redis queue, MariaDB | No |
| `naqil-migrate` | Same image running `naqil-migrate` exactly once per release | MariaDB, Redis services | No |
| `naqil-db` | Railway MariaDB service | Persistent volume | No |
| `naqil-redis-cache` | Railway Redis service | None | No |
| `naqil-redis-queue` | Railway Redis service | None | No |
| `naqil-redis-socketio` | Railway Redis service | None | No |

## Required variables

Every application service receives the same private connection variables: `SITE_NAME`, `DB_HOST`, `DB_PORT`, `DB_ROOT_PASSWORD`, `REDIS_CACHE`, `REDIS_QUEUE`, and `REDIS_SOCKETIO`. Credentials are entered in Railway variables; do not commit them to this repository. Configure Frappe site credentials and encryption keys only through Railway’s secret variables.

## Release order

The database and Redis services must be healthy before any Frappe service starts. Run `naqil-migrate` as a controlled release step after the image build and before routing traffic to a new web deployment. A failed migration blocks the release; it must not be retried blindly against production.

## Files

`docker-compose.local.yml` is for development topology verification. Railway uses the same image and service map, but actual Railway deployment settings are maintained as service configuration and protected variables.

## Starter topology on Railway

The starter deployment runs `NAQIL_SERVICE=combined` in one application service. It uses `bench start` to run the Frappe web process, Socket.IO, scheduler, and workers together. MariaDB has a persistent volume and Redis stays private. This is suitable only for initial review and controlled testing; it must be upgraded to the separate-service topology above before production transaction volume or time-critical auction operations.
