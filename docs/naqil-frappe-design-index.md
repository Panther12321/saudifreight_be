# Naqil Frappe Design Package

This design package defines the planned Frappe backend for Naqil before implementation. It does **not** modify the live React application, Railway deployment, current Frappe installation, or any business data.

## Recommended Review Order

| Order | Document | Review purpose |
|---:|---|---|
| 1 | `naqil-frappe-current-state-audit.md` | Confirms what can be reused from the existing Frappe app and limits the first release. |
| 2 | `naqil-frappe-feature-specification.md` | Reviews the product features, user journeys, workflows, business rules, and operating decisions. |
| 3 | `naqil-frappe-technical-design.md` | Reviews the Frappe data model, roles, APIs, real-time events, automation, security, and deployment topology. |
| 4 | `naqil-frappe-implementation-roadmap.md` | Reviews implementation order, migration safeguards, test strategy, deployment gates, and definition of done. |

## Approved Decisions

| Area | Approved direction |
|---|---|
| Award method | The customer selects the winning eligible bid; the platform does not automatically award the lowest bid. |
| Financial model | The design includes invoices, payment references, escrow cases, carrier settlement, refunds/adjustments, and commission records. Real custody or transfer of funds activates only with an approved compliant provider. |
| Verification policy | The Naqil Administrator defines versioned verification requirements dynamically by party type, document type, expiry, review rule, and enforcement point. |
| Backhaul policy | The Naqil Administrator dynamically defines versioned backhaul rules, including price floors/ceilings, detour limits, eligibility, visibility, and market-balance alerts. |
| Delivery evidence | A private signed delivery document is required, followed by customer confirmation or an audited operations exception. |
| Deployment model | The Frappe backend uses Docker mapped to separate Railway services for frontend, API, websocket, workers, scheduler, MariaDB, Redis, and controlled migration. |
| First-release scope | Advanced routing, GPS, automated pricing, and machine learning remain gated until operating data, policy, and integrations are approved. |

## Approval Outcome

Implementation begins with the secure Frappe foundation: package compatibility, Railway Docker service topology, roles and permissions, organization/profile mapping, dynamic verification policy, private documents, audited API v1, and a staging environment. Marketplace migration follows only after those controls are in place.
