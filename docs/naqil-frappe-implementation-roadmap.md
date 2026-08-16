# Naqil Frappe Implementation Roadmap, Migration, and Test Plan

**Purpose:** Convert the approved Naqil feature and technical designs into controlled implementation work.  
**Rule:** No production deployment proceeds until the preceding release gate is passed in staging.

## 1. Delivery Structure

The work is divided by operational value and risk, not by visual screens. Each package must leave the application more secure and testable than before. The existing React application continues to use demo data until the corresponding Frappe API flow has passed staging acceptance.

| Work package | Business outcome | Main deliverables |
|---|---|---|
| **A. Application foundation** | A deployable and testable custom app. | Packaging, Railway Docker service topology, version compatibility, role fixtures, secure configuration, logs, base audit service, CI checks. |
| **B. Identity and verification** | Trusted users and organisations. | Organization/membership model, dynamically managed verification policies, profiles, verification cases/documents, reviewer workspace, permission tests. |
| **C. Marketplace core** | Authoritative shipment and bid records. | Shipment workflow, bid service, auction events, API v1, ownership controls, React migration for listings and creation. |
| **D. Award and delivery operations** | A defensible path from auction to delivery and financial lifecycle. | Customer-selected atomic award service, assignment, signed delivery evidence, invoices, payment references, escrow/settlement records, notification records, delivery exceptions, commission ledger. |
| **E. Backhaul foundation** | Explainable empty-capacity matching under administrator policy. | Vehicle/driver data, dynamically managed backhaul policy, capacity declarations, deterministic score, match recommendation queue, carrier views. |
| **F. Enterprise fleet SaaS foundation** | Fleet companies can use structured operational data. | Fleet membership, fleet assets, assignment views, controlled entitlements, utilisation reports. |
| **G. Integrations and advanced intelligence** | Data-driven scale when policies are approved. | Maps/distance adapter, payment adapter, identity adapter, telematics adapter, pricing signals, advanced optimisation. |

## 2. Package A — Application Foundation

| Item | Implementation requirement | Acceptance evidence |
|---|---|---|
| Package metadata | Add tested Frappe dependency range to `pyproject.toml`; standardise package files and fixtures. | App installs cleanly in a fresh staging bench without manual container edits. |
| Deployment model | Build one custom Frappe/Naqil Docker image and map Frappe frontend, backend, websocket, workers, scheduler, MariaDB, Redis, and controlled migration job to separate Railway services. | Staging Railway project has private networking, volumes, reference variables, retries, health checks, and no public database/Redis service. |
| Configuration | Use site configuration/secrets for API keys, provider credentials, and feature flags. | No secret appears in source, browser bundle, fixtures, or logs. |
| Roles | Add Naqil roles and permissions through fixtures/migrations. | Role matrix tests prove deny-by-default access. |
| Audit service | Add reusable domain audit writer with request ID and source actor. | Sensitive action creates a readable audit event. |
| Test foundation | Add automated test structure and seeded synthetic fixture factory. | Tests run against a fresh isolated site/database. |

## 3. Package B — Identity and Verification

### Build Order

1. Create `Naqil Organization` and `Naqil Membership`.
2. Extend existing Customer and Carrier Profiles with User and Organization links.
3. Create Vehicle and Driver DocTypes with carrier/fleet ownership.
4. Create versioned Verification Policy, Verification Case, and private Verification Document child table.
5. Implement dynamic administrator policy enforcement, reviewer workflow, reviewer workspace, decision reason, expiry handling, and notification records.
6. Expose controlled profile and verification API methods to React.

### Release Gate

A customer, carrier, and fleet manager can register and access only their own profile data. A reviewer can approve/reject documents without accessing financial or unrelated company data. An unverified carrier cannot submit a bid. An administrator policy change is versioned and affects only the defined future enforcement scope. All decisions are auditable.

## 4. Package C — Marketplace Core

### Build Order

1. Redesign Shipment Request fields, child tables, state machine, ownership model, and tracking code service.
2. Redesign Carrier Bid statuses, ownership, vehicle link, idempotency record, and validity rules.
3. Create Auction Event history.
4. Implement `shipments.create`, `shipments.publish`, `shipments.list`, `auctions.submit_bid`, and `auctions.withdraw_bid` API methods.
5. Add notification records and authenticated real-time bid events.
6. Connect React shipment listing, creation, and bid flows to staging endpoints behind a feature flag.

### Release Gate

Customer users see only their shipments and bids received. Eligible carriers can see only permitted open opportunities and their own bids. A duplicate network retry does not create a duplicate bid. A late bid is rejected even if the scheduler sweep has not yet executed.

## 5. Package D — Award, Assignment, and Delivery

### Build Order

1. Create `Shipment Assignment`, `Shipment Milestone`, `Signed Delivery Evidence`, `Dispute Case`, `Commission Ledger`, `Invoice`, `Payment Reference`, `Escrow Case`, and `Carrier Settlement`.
2. Implement atomic `auctions.award_bid` service.
3. Implement carrier confirmation deadline and escalation job.
4. Implement pickup, in-transit, signed delivery-evidence upload, customer confirmation/dispute, and exception services.
5. Implement invoice/payment-reference/escrow/settlement state machines and provider-adapter boundary.
6. Create operations monitor and finance review reports.
7. Connect React award, signed-document, financial-status, and tracking experiences to the API.

### Release Gate

Two concurrent award attempts cannot create two winners. The customer selects the winning eligible bid, and award snapshots the commission and event history. Only the awarded carrier can confirm the assignment. Delivery requires private signed evidence plus customer confirmation or an audited operations exception. Finance records retain invoice, payment, escrow, and settlement state without claiming provider custody before provider activation.

## 6. Package E — Backhaul Foundation

### Build Order

1. Create versioned Backhaul Policy with administrator-managed price, detour, visibility, eligibility, and alert controls.
2. Extend Backhaul Trip with vehicle, availability windows, capacity, route stops, opt-in setting, policy reference, and constraints.
3. Create Match Recommendation and score-explanation fields.
4. Implement matching service and queue refresh process.
5. Provide carrier/fleet endpoints for capacity declaration and recommendation list.
6. Add operations analytics for market-balance alerts.

### Release Gate

Every displayed recommendation has stored score inputs, policy version, and clear reasons. Recommendations never award a public shipment automatically. Match calculation is repeatable from the same input set and does not expose another party’s private information.

## 7. Package F — Enterprise Fleet SaaS Foundation

### Build Order

1. Add Fleet Subscription and entitlement rules.
2. Build fleet manager workspace and reports for vehicles, drivers, assignments, and capacity.
3. Provide organisation-scoped fleet API views for React SaaS screens.
4. Add basic route/job visibility and operational utilisation reporting.

### Release Gate

A fleet manager can only access assets belonging to their own organisation. Enterprise entitlement is consistently checked in both API and workspace operations. Marketplace visibility of fleet return capacity depends on explicit opt-in.

## 8. Package G — Integrations and Advanced Intelligence

This package begins only when policy, contracts, and reliable operating data exist. Each provider is implemented behind an adapter interface so that a provider change does not require rewriting marketplace logic.

| Integration | Initial purpose | Required safeguards |
|---|---|---|
| Maps/distance | Route distance, city proximity, and detour scoring. | Cache, rate limit, failure fallback, request audit. |
| Payments and escrow | Activate the already-designed invoice, payment-reference, escrow, refund, and settlement lifecycle with an approved provider. | Provider webhook validation, idempotency, legal/commercial approval, finance reconciliation, and release-condition controls. |
| Identity provider | Automated or assisted verification. | Manual-review fallback, consent, evidence retention policy. |
| Telematics | Optional vehicle location summaries. | Explicit consent, retention policy, least-privilege access, outage handling. |
| Optimisation engine | Multi-stop and fleet route recommendation. | Constraint versioning, explainability, manual override, score monitoring. |

## 9. Migration Strategy for the Existing App

The migration protects the current prototype’s data structures while moving to a standalone Naqil identity model. No existing production data is assumed to be clean or complete; every migration must be repeatable and logged.

| Migration step | Action | Rollback / protection |
|---|---|---|
| 1. Snapshot | Export Frappe site/database and custom app version before migration. | Restore snapshot only in isolated recovery process. |
| 2. Staging clone | Copy only approved/sanitised records into staging. | Never rehearse against the sole live dataset. |
| 3. Schema addition | Add new DocTypes and nullable links without removing existing fields. | Old fields remain read-only during transition. |
| 4. Identity backfill | Create Naqil Organization/Membership links from legacy Customer/Supplier/profile data where a clear mapping exists. | Unmapped records enter a manual-review report; no guessed match. |
| 5. API switch | Introduce API v1 and move React flow by flow behind feature flags. | Switch only the affected flow back to demo/read-only fallback if staging validation fails. |
| 6. Data integrity review | Compare legacy and new counts, ownership, status, and bid relationships. | Block production release on mismatch report. |
| 7. Legacy retirement | Stop writing legacy ERPNext Customer/Supplier links only after approved migration sign-off. | Preserve archived legacy mapping table for reference. |

## 10. Test Strategy

### 10.1 Automated Tests

| Test type | Scope | Examples |
|---|---|---|
| Unit tests | Pure validation and scoring functions. | Capacity fit, score contribution, commission calculation, state transition rules. |
| DocType tests | Save hooks and permissions. | Profile link requirements, document expiry, forbidden field mutation. |
| Service tests | Multi-record business transactions. | Atomic award, bid withdrawal, cancellation, assignment confirmation. |
| API tests | Authenticated request/response and error contract. | Customer cannot award another customer’s shipment; invalid bid returns safe error code. |
| Worker/scheduler tests | Deferred and recurring jobs. | Due auction closes once; notification retry does not duplicate message. |
| Real-time tests | Permissioned event publication. | Only shipment owner receives safe bid summary. |
| Migration tests | Schema and data transforms. | Legacy profile maps to correct organization or enters exception report. |

### 10.2 Security Tests

The suite must test unauthenticated access, cross-organisation access, role escalation, direct DocType endpoint abuse, expired verification, stale browser actions, forged ID values, duplicate idempotency keys, private document access, and privileged override audit trails.

### 10.3 Operational Acceptance Tests

Before production, run a controlled end-to-end scenario with synthetic accounts: customer registration, carrier verification, shipment publication, multiple valid bids, auction close, customer award, carrier confirmation, pickup, signed delivery-document upload, customer confirmation or dispute, financial-state progression, rating, and an exception/dispute case. Record each expected audit event and permission boundary.

## 11. Deployment Checklist

| Gate | Required evidence |
|---|---|
| Application package | Fresh install succeeds from GitHub/custom image with no manual Python path changes. |
| Railway topology | Each Frappe process has a mapped Railway service; only React and Frappe frontend have public domains; all dependencies use private networking and startup retries. |
| Database and files | Automated backups enabled; restore rehearsal documented; private document storage verified. |
| Release migration | One controlled migration job completes before production service promotion; no app service runs migration independently. |
| Workers and scheduler | Queue processing, scheduler jobs, retry visibility, and real-time process health verified. |
| Security | Secrets in deployment manager; HTTPS enabled; role tests pass; admin accounts controlled. |
| API | React staging origin configured; CORS/session/token policy tested; no browser API secrets. |
| Observability | Structured logs, error monitoring, queue visibility, and operational alerts available. |
| Release approval | Product owner signs off feature spec, operations signs off workflows, and technical reviewer signs off test results. |

## 12. Definition of Done for the First Production Backend

The first release is complete only when a verified customer and carrier can complete the core journey through authoritative Frappe records; all permissions are enforced at API level; every sensitive action has audit evidence; the React application reads the live backend for the enabled flows; required workers and scheduler jobs are healthy; private documents are protected; and the deployment can be rebuilt from source without ad hoc container modification.
