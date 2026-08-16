# Naqil Backend

The Naqil backend is a custom Frappe application for a Saudi freight marketplace and fleet SaaS. It is the authoritative system for organizations, verification, shipments, reverse-auction bids, assignments, signed delivery evidence, financial records, backhaul policies, and platform administration.

The public React application remains a separate client. It consumes the versioned Naqil API and authenticated real-time events; it does not make trusted business decisions.

## Current foundation

This repository contains the first implementation milestone: a Frappe-compatible application package, role fixtures, secure service boundaries, source-controlled design documentation, and the planned Docker/Railway topology. Marketplace workflows are added incrementally and tested before any Railway deployment is created.

## Repository layout

| Path | Purpose |
|---|---|
| `naqil/` | Custom Frappe application package. |
| `docs/` | Approved product, technical, migration, and deployment design documents. |
| `docker/` | Docker, bootstrap, health-check, and Railway service support files. |
| `tests/` | Static and application-level tests. |

## Local development

The app targets Frappe Framework v15. It must be installed into a developer-mode Frappe bench, then migrated against a dedicated test site. Do not install it by editing Python paths or changing a running container manually.

```bash
bench get-app <this-repository-url>
bench --site <site-name> install-app naqil
bench --site <site-name> migrate
```

## Deployment

The approved production design is Docker on Railway. Railway maps each Frappe responsibility to a separate service: frontend proxy, API/backend, websocket, workers, scheduler, MariaDB, Redis services, and a controlled migration job. See `docs/naqil-frappe-technical-design.md` before deployment.

## Security baseline

No mutable API method may use broad permission bypasses. Private verification and signed-delivery files must use protected storage. Finance and escrow records are modeled in the app, while actual custody or transfer is enabled only after a compliant payment provider is approved.
