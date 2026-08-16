# Naqil Frappe Technical Design

**Document status:** Implementation design for review  
**Backend:** Frappe Framework custom application, `naqil`  
**Frontend:** Existing React application on Railway  
**Architecture principle:** Frappe is the system of record; React is an authenticated client of a stable Naqil API.

## 1. Architecture

```text
React web application (Railway)
  ├── Public marketing and authenticated customer screens
  ├── Carrier and fleet experiences
  └── Admin-facing web views where appropriate
            │
            │ HTTPS REST API + authenticated Socket.IO events
            ▼
Frappe custom app: naqil
  ├── DocTypes and workflows
  ├── Permission and ownership enforcement
  ├── API v1 methods
  ├── Private file upload and verification cases
  ├── Background workers and scheduler jobs
  ├── Admin workspace, reports, and audit events
  └── Integrations through adapter modules
            │
            ├── MariaDB (transactional records)
            ├── Redis (cache, queues, real-time transport)
            ├── Socket.IO real-time process
            └── Object storage for private documents
```

Frappe automatically provides DocType REST endpoints and supports custom whitelisted methods; it also supports token, password-session, and bearer-token authentication, plus file uploads. [1] The React application will use a restricted, versioned API layer rather than direct unrestricted DocType access for every business action.

## 2. Application Boundaries

| Responsibility | React application | Frappe `naqil` app |
|---|---|---|
| Page rendering and interaction | Owns. | Does not own public visual design. |
| Authoritative data | Reads controlled API views only. | Owns all source records and state transitions. |
| Permission decision | May hide unavailable controls for usability. | Enforces every access decision. |
| Auction award and commission | Displays result. | Validates and commits atomic transaction. |
| Documents | Shows user-safe status. | Stores private files and reviewer decisions. |
| Notifications | Receives and presents events. | Creates notification records and publishes events. |
| Route/matching logic | Shows recommendation explanation. | Calculates/schedules approved rule-based matching. |

## 3. Package and Deployment Baseline

The `naqil` application must be packaged as a tested custom app. It should not rely on direct container edits, `.pth` path workarounds, or a disposable Frappe demo. The app must declare a tested compatible Frappe version in `pyproject.toml`, maintain fixtures through migration, and be deployed through a private Frappe Cloud bench or an official multi-service Docker image. Frappe Cloud documents custom apps on private bench groups, while the official Frappe Docker repository separates disposable demos from production container configurations. [5] [6]

```toml
[tool.bench.frappe-dependencies]
frappe = ">=15.0.0,<16.0.0"
```

The exact range must be confirmed through integration tests before deployment. The first backend deployment should use an isolated staging site before production.

## 4. Data Model Strategy

### 4.1 Do Not Depend on ERPNext Customer and Supplier

The current prototype links shipment customers to ERPNext `Customer` and carrier bids to ERPNext `Supplier`. The production Naqil app should remove those hard dependencies so it can run as a standalone Frappe application. This avoids forcing marketplace identities into ERP accounting entities before that integration is actually needed.

The production model uses a Naqil-specific identity layer linked to Frappe `User` records.

### 4.2 Primary DocTypes

| DocType | Type | Purpose | Release-one decision |
|---|---|---|---|
| **Naqil Organization** | New | A shipper company, carrier company, fleet company, or independent operator. | Required. |
| **Naqil Membership** | New | Links Frappe User to an organization, role, authority level, and active status. | Required. |
| **Customer Profile** | Extend | Customer-specific operating and verification profile. | Retain and migrate to link to Organization/User. |
| **Carrier Profile** | Extend | Carrier credentials, service capability, verification status, and compliance state. | Retain and migrate to link to Organization/User. |
| **Vehicle** | New | Vehicle identity, equipment, capacity, verification, and availability. | Required for verified carrier bidding. |
| **Driver** | New | Driver identity, authorization, availability, and documents. | Required when assignment identifies driver. |
| **Verification Case** | New | Controlled review case for customer, carrier, vehicle, or driver evidence. | Required. |
| **Verification Document** | Child table | Document metadata and private File reference. | Required. |
| **Verification Policy** | New | Versioned administrator-managed requirements by party, document type, enforcement point, expiry, and review rule. | Required. |
| **Shipment Request** | Extend | Customer-owned transportation request and auction parent record. | Retain; substantial redesign. |
| **Carrier Bid** | Extend | Carrier offer for a shipment. | Retain; redesign permissions/statuses. |
| **Auction Event** | New | Immutable event history of open, close, bid state, award, reopen, and cancellation actions. | Required. |
| **Shipment Assignment** | New | Awarded carrier/vehicle/driver commitment separate from the bid. | Required. |
| **Shipment Milestone** | New | Pickup, in-transit, delivery, and exception timeline. | Required. |
| **Signed Delivery Evidence** | New | Private signed proof-of-delivery record linked to delivery milestone and customer confirmation/dispute. | Required. |
| **Backhaul Trip** | Extend | Empty capacity declaration with schedule and equipment constraints. | Retain; extend. |
| **Match Recommendation** | New | Explainable shipment-backhaul or multi-stop recommendation. | Required. |
| **Backhaul Policy** | New | Versioned administrator-managed price, detour, eligibility, visibility, and alert rules. | Required. |
| **Dispute Case** | New | Controlled commercial/service dispute workflow. | Required. |
| **Notification** | New | Delivered, queued, failed, and read notifications. | Required. |
| **Commission Ledger** | New | Immutable commission calculation and adjustment history. | Required. |
| **Invoice** | New | Customer payable document for an awarded shipment. | Required. |
| **Payment Reference** | New | External payment-provider transaction state and reconciliation reference. | Required. |
| **Escrow Case** | New | Provider-backed fund-hold, release, refund, and dispute lifecycle. | Required in design; enabled only after compliant provider integration. |
| **Carrier Settlement** | New | Carrier payable/release/payout lifecycle tied to award and escrow state. | Required in design. |
| **Naqil Settings** | Extend | Platform policy and controlled business configuration. | Retain. |
| **Audit Event** | New | Extra domain audit events for sensitive business actions. | Required. |
| **Fleet Subscription** | New | SaaS-plan and fleet-entitlement record. | Structure now; billing automation deferred. |

### 4.3 Key Relationships

```text
Frappe User ──< Naqil Membership >── Naqil Organization
      │                                    ├──< Vehicle
      │                                    ├──< Driver
      │                                    ├── Carrier Profile
      │                                    └── Customer Profile
      │
Customer Profile ──< Shipment Request ──< Carrier Bid
                                        │          │
                                        │          └── Vehicle / Carrier Profile
                                        ├──< Auction Event
                                        ├── Shipment Assignment ──< Shipment Milestone
                                        ├──< Dispute Case
                                        └── Commission Ledger

Backhaul Trip ──< Match Recommendation >── Shipment Request
Verification Case ──< Verification Document
Verification Policy ──< Verification Case
Backhaul Policy ──< Backhaul Trip / Match Recommendation
Shipment Assignment ──< Signed Delivery Evidence
```

### 4.4 Child Tables

| Parent | Child table | Purpose |
|---|---|---|
| Shipment Request | Cargo Item | Multiple cargo items, packaging, quantity, dimensions, handling requirements. |
| Shipment Request | Time Window | Pickup and delivery windows, time-zone-safe dates, and appointment needs. |
| Carrier Bid | Bid Vehicle Option | Optional eligible vehicle alternatives when policy allows. |
| Shipment Assignment | Assignment Contact | Authorised carrier/customer contact points for the job. |
| Backhaul Trip | Route Stop | Declared start, planned stops, intended direction, and detour tolerance. |
| Verification Case | Verification Document | Document type, File link, expiry, review result, and reviewer note. |
| Dispute Case | Dispute Evidence | Controlled evidence attachment, submitter, timestamp, and visibility. |

## 5. Permission Design

Frappe supports role-based DocType permissions, field permission levels, user-specific record restrictions, password handling, and login throttling. [2] Naqil will use three layers of enforcement.

| Layer | Rule |
|---|---|
| **Role permission** | Defines which DocTypes and broad actions a role may read, create, write, submit, cancel, report, export, or share. |
| **Record ownership / organization scope** | Ensures a customer sees only own shipment records and a carrier sees only own bids, vehicles, backhaul declarations, and awarded jobs. |
| **Business-state validation** | Ensures that even an authorised role cannot bid after close, award an ineligible offer, edit an accepted bid, or access private evidence without authority. |

### 5.1 Role Matrix

| Action | Customer | Carrier | Fleet Manager | Reviewer | Operations | Finance | Admin |
|---|---:|---:|---:|---:|---:|---:|---:|
| Create own shipment | Yes | No | Optional for own organization | No | Exception only | No | Yes |
| Submit bid | No | Yes | Yes for own fleet | No | No | No | Exception only |
| Select winning bid | Own shipment only | No | No | No | Exception approval only | No | Yes, audited |
| Review documents | Own status only | Own status only | Own company status | Yes | Read only if needed | No | Yes |
| Manage vehicle/driver | No | Own organization | Own organization | No | Read only | No | Yes |
| View commission records | Own shipment summary only | Own awarded-job summary only | Own organization summary | No | Read only | Yes | Yes |
| Change policy/settings | No | No | No | No | Limited flags only | Limited finance policy | Yes |

No public endpoint may use a broad `ignore_permissions=True` write. System-level operations may run as a service user, but each must record the original actor, policy version, and affected record.

## 6. Workflow and State Implementation

Frappe Workflow is suitable for reviewer and administration states. Custom Python services are required for transactional operations where multiple records change together, such as bid award and auction closure.

### 6.1 Service Modules

```text
naqil/
  api/v1/                 # Stable public API methods
  services/
    authz.py               # Role, organization, and ownership guards
    shipments.py           # Submission and lifecycle transitions
    auctions.py            # Bid validation, closure, award, reopen
    assignments.py         # Carrier confirmation and milestones
    verification.py        # Case/document decision rules
    matching.py            # Rule-based backhaul and multi-stop scores
    commissions.py         # Commission snapshot and ledger events
    notifications.py       # Notification records and publication
    audit.py               # Domain audit event writer
  integrations/
    maps.py                # Route/distance provider adapter
    payments.py            # Payment provider adapter
    identity.py            # Verification provider adapter
    telematics.py          # GPS provider adapter
  tasks/
    auctions.py            # Due-auction sweep and escalation
    matching.py            # Recommendation refresh
    reports.py             # Daily operational report
  realtime/
    handlers.py            # Future authenticated subscription handlers
```

### 6.2 Atomic Award Operation

The `award_bid` service must validate shipment ownership, shipment state, auction-close condition, bid eligibility, carrier verification, and bid state. It must then lock or transactionally update the shipment and related bids so that one accepted bid is possible. The service writes an `Auction Event`, creates `Shipment Assignment`, snapshots commission into `Commission Ledger`, changes all remaining bids to `Not Selected`, queues notification records, and publishes a real-time event only after commit.

### 6.3 Audit Policy

The application writes an Audit Event for: profile verification decision, document replacement, shipment publication, bid submission/withdrawal/invalidation, auction close, award, assignment confirmation, milestone update, dispute decision, commission adjustment, policy change, and privileged administrator override. Frappe’s built-in change tracking is retained where suitable; the domain audit record adds business context and source actor.

## 7. API Contract

### 7.1 API Rules

The public API is namespaced under `/api/method/naqil.api.v1.*`. Read-only listing methods must apply organization/record scope in the server query. State-changing methods use `POST`, enforce authentication, accept an `Idempotency-Key` for actions that can be retried, and return a standard envelope.

```json
{
  "data": {},
  "meta": {
    "request_id": "..."
  },
  "error": null
}
```

Validation failures return a stable error code and safe user-facing message. Internal details stay in server logs and audit records.

### 7.2 Core Endpoints

| Operation | Method path | Required role | Notes |
|---|---|---|---|
| Current user and memberships | `me.get_context` | Authenticated user | Returns safe profile, roles, organization memberships, and entitlements. |
| Start/submit verification | `verification.create_case`, `verification.submit_case` | Profile owner | Creates controlled review case. |
| Upload a document | Frappe upload endpoint through guarded flow | Profile owner | Private file, expected document type, server-side case check. |
| Create shipment | `shipments.create` | Customer/Fleet Manager | Returns draft or submitted request. |
| Publish shipment | `shipments.publish` | Shipment owner | Validates required fields and starts auction. |
| List accessible shipments | `shipments.list` | Scoped authenticated user | Filters by viewer, route, status, and pagination. |
| Submit or replace bid | `auctions.submit_bid` | Verified carrier/fleet | Requires idempotency key and eligibility check. |
| Withdraw bid | `auctions.withdraw_bid` | Bid owner | Only before close and before award. |
| Close due auction | Worker only | Service operation | Not publicly callable. |
| Award bid | `auctions.award_bid` | Shipment owner or audited operations exception | Atomic multi-record operation. |
| Declare backhaul capacity | `backhaul.create_or_update` | Verified carrier/fleet | Validated against vehicle. |
| List recommendations | `matching.list_recommendations` | Scoped user | Returns score explanations, not hidden weight internals. |
| Confirm assignment | `assignments.confirm` | Awarded carrier | Requires eligible vehicle/driver. |
| Record milestone | `assignments.record_milestone` | Assigned carrier / controlled operations | Applies state rules. |
| Open dispute | `disputes.open` | Shipment party | Captures case and evidence. |

### 7.3 File Upload Contract

Frappe includes a dedicated upload method. [1] Naqil wraps the upload action with a verification-case check so a user may upload only the allowed document type to an accessible case. The server sets private visibility, stores metadata, rejects unapproved file types and size policy violations, and returns a safe document status—not a durable public download URL.

### 7.4 Authentication

The preferred browser approach is secure session or OAuth-based authentication under a shared parent domain when feasible. If a separate frontend and backend domain are used, introduce a dedicated token/session exchange with short-lived access tokens and refresh controls; do not embed static Frappe API key/secret pairs in the React application. Token-based API calls remain appropriate for server-to-server integrations, where the token is associated with a restricted service user. [1]

## 8. Real-Time Contract

Frappe’s real-time service uses Socket.IO and Redis; custom clients can authenticate using browser cookies or an Authorization header. [4] The React client subscribes only after API-level user authentication and must not join broad rooms without permission checks.

| Event | Audience | Data returned |
|---|---|---|
| `auction.bid_created` | Shipment owner | Safe bid summary and refreshed bid count. |
| `auction.closing_soon` | Shipment owner and participating bidders | Shipment ID and remaining time. |
| `auction.closed` | Shipment owner and bidders | Closed state and next allowed action. |
| `auction.awarded` | Shipment owner, winner, participating bidders | Safe outcome status; no unnecessary competitor data. |
| `verification.updated` | Profile owner and reviewer queue | Case ID and status. |
| `assignment.updated` | Shipment parties and operations | Assignment/milestone status. |
| `matching.recommendation_ready` | Relevant carrier/fleet | Recommendation ID and safe explanation. |

Events are published after database commit. The browser always refetches the authoritative resource after receiving an event rather than relying on an event payload as the sole source of truth.

## 9. Automation and Queue Design

Frappe supports asynchronous jobs through queues and recurring work through scheduler events. [3] Naqil will divide work by duration and risk.

| Job | Trigger | Queue / execution | Idempotency rule |
|---|---|---|---|
| Close due auctions | Frequent scheduler sweep | Short/default worker | Skip if shipment already closed/awarded/cancelled. |
| Notify users after event | Post-commit | Short worker | Notification type + recipient + source event unique key. |
| Refresh backhaul recommendations | New/updated backhaul or shipment, plus periodic sweep | Default worker | Replace only outdated recommendations for the same input version. |
| Expiring-document reminders | Daily scheduler | Default worker | One reminder per case/document/threshold. |
| Daily operations summary | Daily scheduler | Long worker if report volume requires | Stored report date unique key. |
| Route/distance provider call | User action or worker | Default worker | Cache provider result by route/constraint fingerprint. |

Scheduler timing is not a substitute for API validation. For example, auction bids must be rejected after the stored close time even if a sweep job has not yet processed the shipment.

## 10. Matching and Pricing Design

### 10.1 Explainable Match Score

The first matching score is deterministic and configurable. It is not presented as machine learning.

```text
score = route_alignment
      + origin_proximity
      + destination_compatibility
      + departure_window_overlap
      + vehicle_equipment_fit
      + capacity_fit
      + cargo_constraint_fit
      + urgency_compatibility
      + commercial_feasibility
      - route_detour_penalty
      - policy_risk_penalty
```

Each component stores a numeric contribution and human-readable explanation. A user may see summary reasons; administrators may see the full calculation for audit and tuning.

### 10.2 Dynamic Pricing Signal

The first release creates a **Pricing Signal** record rather than automatically changing market prices. It records route, service category, observed supply/demand indicator, recommended range, confidence, source data window, policy version, and manual approval status. Automatic price modification remains disabled until a market policy is approved and measured data supports it.

### 10.3 Market Balance

Backhaul offers remain market offers. A versioned Backhaul Policy selected by the Naqil Administrator governs price floors/ceilings, maximum detour, eligible routes/categories, marketplace opt-in defaults, visibility labels, and operations alert thresholds. The service stores the policy version used for each recommendation or policy-sensitive bid. It does not force selection or reserve public demand for either backhaul or ordinary carriers.

## 11. Administration and Reporting

| Report / workspace | Data sources | Audience |
|---|---|---|
| Verification Queue | Verification Case, Document, profile status | Reviewers, administrators. |
| Auction Monitor | Shipment Request, Carrier Bid, Auction Event | Operations. |
| Assignment Risk Board | Shipment Assignment, milestones, overdue confirmations | Operations, support. |
| Backhaul Opportunity Monitor | Backhaul Trip, Match Recommendation, response outcome | Operations, fleet managers. |
| Commission and Reconciliation | Commission Ledger, payment/invoice references | Finance, administrators. |
| Marketplace Health | Shipment lifecycle, bid activity, verification turnaround, dispute status | Administrators. |
| Audit Explorer | Audit Event, Frappe change tracking | Administrators and restricted compliance users. |

## 12. Security and Data Handling

| Control | Technical design |
|---|---|
| Data access | Role + organization/ownership query filters + business-state guard. |
| Documents | Private file access, verification-case link, type/size policy, reviewer-only evidence visibility. |
| Secrets | Stored only in deployment secret manager; never React code or client-side configuration. |
| API reliability | Idempotency keys for mutable public actions, request correlation ID, safe error envelope. |
| Audit | Domain Audit Event for sensitive state changes and overrides. |
| Data minimisation | Store only the identity, operational, and location data required by approved policy. |
| Integration safety | Provider adapters, signed webhook validation, retry record, dead-letter/exception visibility. |
| Exports | Restrict report/export rights by role; avoid broad data downloads for support users. |

## 13. Railway Docker Deployment Topology

The approved deployment model is **Docker on Railway**. Railway does not execute a Compose file as one deployment; each Frappe Compose responsibility must become a separate Railway service in the same Railway project. Railway services communicate automatically over the private network at `<service-name>.railway.internal`, use Railway Variables for configuration, and must implement connection retries because Compose `depends_on` is not available. [7]

The Frappe `naqil` app is built once as a custom Docker image from GitHub. All Frappe application services use that exact image so code and fixtures remain consistent. Only the `frappe-frontend` service receives a public Railway domain. The React/Railway web application remains a separate public service and calls the Frappe frontend/API domain over HTTPS.

| Railway service | Docker command responsibility | Exposure | Persistent data |
|---|---|---|---|
| `frappe-frontend` | Nginx/frontend proxy; serves Desk/assets, routes `/api` to backend and `/socket.io` to websocket. | Public Frappe domain only. | None; image assets only. |
| `frappe-backend` | Python/Gunicorn Frappe web and API process. | Private network only. | None; app code in image. |
| `frappe-websocket` | Frappe Socket.IO real-time process. | Private network only via frontend proxy. | None. |
| `frappe-worker-default` | Short/default queue consumer for notifications and normal matching work. | Private network only. | None. |
| `frappe-worker-long` | Long queue consumer for reports, provider reconciliation, and heavier work. | Private network only. | None. |
| `frappe-scheduler` | Frappe scheduler for auction sweeps, reminders, and recurring policy jobs. | Private network only. | None. |
| `frappe-mariadb` | MariaDB 10.6 service required by the selected Frappe stack. | Private network only. | Railway Volume mounted at MariaDB data directory, plus external backups. |
| `redis-cache` | Cache and rate/temporary state Redis. | Private network only. | No durable business records. |
| `redis-queue` | Background-job Redis queues. | Private network only. | Queue persistence only as required by Redis configuration. |
| `redis-socketio` | Redis pub/sub transport for real-time events. | Private network only. | No durable business records. |
| `frappe-migrate` | Controlled release job for `bench migrate` and fixture changes. | Private network only; invoked through approved release runbook. | No persistent filesystem. |

### 13.1 Service Networking and Variables

The Frappe site configuration uses Railway private hostnames, such as `frappe-mariadb.railway.internal` and `redis-queue.railway.internal`. Every service receives its credentials through Railway Variables or reference variables; no credentials are committed to GitHub. The backend, workers, scheduler, and websocket process must retry startup until database and Redis dependencies become available.

| Configuration group | Examples |
|---|---|
| Site identity | `FRAPPE_SITE_NAME`, allowed host/domain, public API URL, React origin. |
| MariaDB | Host, port, database name, root/bootstrap secret, application database secret. |
| Redis | Cache, queue, and Socket.IO Redis URLs using private Railway hostnames. |
| Application secrets | Encryption key, session/auth secret, webhook signing secret, provider credentials. |
| Object storage | Private bucket, region, access key, secret, endpoint, and document path prefix. |
| Feature flags | Enable staged API flows, real-time events, financial records, signed delivery evidence, and provider adapters separately. |

### 13.2 Files, Documents, and Backups

Railway volumes persist for the attached service, but service-local filesystems are not shared between Frappe frontend and workers. Therefore private verification documents and signed delivery evidence must use external object storage, with the Frappe File record storing protected metadata and a private object key. MariaDB receives a dedicated Railway Volume, and the production runbook must include scheduled encrypted off-platform backups and a tested restore process.

### 13.3 Custom Image and Repository Layout

The production repository will include a Dockerfile that starts from a compatible official Frappe image, installs the pinned `naqil` app through the supported package path, and produces a repeatable tagged image. Railway automatically builds from a root `Dockerfile` or a configured Dockerfile path when code changes are pushed to the linked branch. [8]

```text
naqil-erp/
  Dockerfile                 # Custom image with pinned Frappe and naqil app
  apps.json                  # App source/version manifest for build
  compose.local.yml          # Local/staging parity only; Railway does not run it directly
  scripts/
    wait-for-dependencies.sh # Retry MariaDB/Redis readiness
    bootstrap-site.sh        # Idempotent site creation/install for new environment
    migrate-site.sh          # Controlled migration command
    healthcheck.sh           # Service readiness checks
  naqil/                     # Custom Frappe app
```

### 13.4 Release and Migration Runbook

Database migrations are not run independently by every app service. The `frappe-migrate` job is run once per approved release after image build and dependency readiness, with a database backup verified first. It runs `bench migrate`, applies fixtures, validates the Naqil app version, and exits with an observable result. The deployment is promoted only when migration, health checks, worker connectivity, scheduler visibility, and a basic API request succeed.

### 13.5 Railway Operational Controls

Railway services expose logs, deployment history, and metrics. [9] The production setup must define public domains only for the React service and `frappe-frontend`; MariaDB, Redis, workers, scheduler, backend, migrate, and websocket stay private. Each service receives a health check appropriate to its responsibility. Application service failures must alert operations, while database and migration failures block release approval.

| Environment | Purpose | Required controls |
|---|---|---|
| Development | Local app work and automated tests. | Synthetic data only; no production secrets. |
| Staging | Railway multi-service integration, API/realtime, and migration validation. | Isolated Railway project, test identities, deploy/release rehearsal, restore rehearsal. |
| Production | Authoritative marketplace operations. | Private internal services, HTTPS public gateways, database volume plus off-platform backups, object storage, migration approval, monitoring, and access logging. |

## References

[1]: https://docs.frappe.io/framework/user/en/api/rest "Frappe Framework — REST API"
[2]: https://docs.frappe.io/framework/user/en/basics/users-and-permissions "Frappe Framework — Users and Permissions"
[3]: https://docs.frappe.io/framework/user/en/api/background_jobs "Frappe Framework — Background Jobs"
[4]: https://docs.frappe.io/framework/user/en/api/realtime "Frappe Framework — Realtime (Socket.IO)"
[5]: https://frappecloud.com/docs/installing-an-app "Frappe Cloud — Installing an App"
[6]: https://github.com/frappe/frappe_docker "Frappe Docker — Official Container Setup"
[7]: https://docs.railway.com/guides/docker-compose "Railway — Deploy a Docker Compose App to Production"
[8]: https://docs.railway.com/builds/dockerfiles "Railway — Dockerfiles"
[9]: https://docs.railway.com/services "Railway — Services"
