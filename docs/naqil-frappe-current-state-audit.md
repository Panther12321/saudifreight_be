# Naqil Frappe App — Current-State Audit and Release-One Scope

## Current Assets

The existing `naqil` Frappe app is a credible technical starting point. It contains six DocTypes: **Shipment Request**, **Carrier Bid**, **Carrier Profile**, **Customer Profile**, **Backhaul Trip**, and **Naqil Settings**. It also includes a Naqil workspace, three initial role fixtures, basic REST-accessible Python methods, document event hooks, and scheduled functions for auction closing, backhaul matching, daily reporting, and carrier-statistics updates.

The present `Shipment Request` model already covers route cities and addresses, cargo characteristics, weight and volume, requested vehicle type, budget, auction timestamps, bid summaries, commission fields, winning carrier, tracking details, and delivery timestamps. `Carrier Bid` already records a related shipment, carrier, price, offer status, vehicle/driver details, and estimated timing.

## Reusable Foundation

| Existing component | Reuse decision | Required change before production |
|---|---|---|
| Shipment Request | Retain as the core marketplace record. | Add explicit workflow states, permissions, audit events, pickup/delivery time windows, client ownership mapping, and server-side transition validation. |
| Carrier Bid | Retain as the bid record. | Replace generic Supplier dependency with a consistent carrier/fleet entity model; add immutable accepted/rejected history, idempotency, offer rules, and ownership controls. |
| Carrier and Customer Profiles | Retain as starting profiles. | Map each profile to a Frappe User and company entity; add verification case/document relationships, dynamic policy references, and status reason fields. |
| Backhaul Trip | Retain as the capacity declaration. | Extend to capacity windows, vehicle link, route path, availability, match score, administrator policy reference, and opt-in marketplace exposure. |
| Naqil Settings | Retain as platform configuration. | Separate safe business settings from elevated technical settings, preserve configurable commission, and add policy versions. |
| Scheduler hooks | Retain the automation intent. | Replace simplistic hourly operations with explicit queue design, idempotent workers, retry tracking, metrics, and race-safe auction closure. |
| API methods | Rebuild behind a versioned public contract. | Remove broad permission bypasses, validate every input server-side, enforce ownership/role checks, and log consequential actions. |

## Critical Gaps

The current app is a prototype and does not yet have public-marketplace safeguards. Carrier Bid permissions currently target internal Frappe roles rather than marketplace roles. The existing endpoint and task implementations use `ignore_permissions=True` for writes, which cannot remain in a public API. Auction closure currently auto-selects the lowest bid, which conflicts with the product direction where the customer may choose the best eligible offer. Backhaul matching currently relies only on exact origin/destination city equality and can attach only one simple match; it does not model time, vehicle, capacity, pricing, direction, or explainability.

The package metadata is also incomplete for a managed custom-app deployment. The design will require a tested Frappe-version compatibility declaration and a supported custom-app packaging process.

## Release-One Boundary

The first production backend release should be limited to the secure marketplace foundation. Its purpose is to replace demo data in the existing React application with authoritative records while proving the operating model.

| Included in release one | Deferred until operational data exists |
|---|---|
| User, role, profile, and company mapping | Full demand forecasting or machine learning |
| Secure document submission, administrator-defined verification policy, and manual verification | Complex fleet telematics and continuous GPS ingestion |
| Shipment creation, customer-owned auctions, bids, acceptance, assignment, signed delivery evidence, and delivery milestones | Fully automated multi-stop route optimisation |
| Backhaul capacity declaration and explainable rule-based recommendations | Automatic dynamic pricing without approved market policy |
| Administrator-defined backhaul policy, administration queues, audit log, notifications, and operational reports | Advanced enterprise subscription billing automation |
| React API migration for core flows plus invoice, payment-reference, escrow, and settlement state records | Automated funds custody/transfer until a compliant provider is selected and approved |

## Required Design Decisions

Release one assumes the customer selects the winning eligible bid, with an administrator able to intervene only through an audited exception path. The 5% commission remains configurable. Invoice, payment-reference, escrow, and settlement records are included; actual custody or transfer is activated only after an approved compliant provider is integrated. Every carrier must be verified before bidding under the active administrator-defined policy, and a fleet company may expose empty capacity to the public marketplace only through explicit opt-in under the active backhaul policy.
