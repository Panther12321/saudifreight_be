# Naqil Frappe Feature Specification

**Document status:** Review draft for approval before implementation  
**Product:** Naqil — Saudi Freight Marketplace and Fleet SaaS  
**Primary backend:** Frappe custom app (`naqil`)  
**Public interface:** Existing React application  
**First-release focus:** Secure marketplace operations, carrier verification, reverse auctions, backhaul recommendations, administration, and authoritative records.

## 1. Product Purpose

Naqil enables a shipper to request freight transportation, eligible carriers to compete through a reverse auction, and the platform to manage verification, assignment, commission, delivery milestones, and operational exceptions. The platform also establishes the data foundation for later enterprise fleet SaaS capabilities.

The first release must prioritise trust and operational correctness over automation claims. A customer should be able to publish a valid request, receive eligible bids, choose a winning bid, track key milestones, and resolve exceptions through an accountable platform process. A carrier should be able to complete verification, declare qualified vehicles and capacity, bid only when eligible, and receive a clear outcome.

## 2. Users and Responsibilities

| User | Primary responsibility | First-release access |
|---|---|---|
| **Customer / Shipper** | Creates and manages own shipment requests. | Registers, submits documents, publishes shipments, views bids, selects an offer, confirms milestones, rates the completed service. |
| **Carrier** | Provides transport capacity and submits offers. | Registers, completes verification, maintains vehicle details, declares backhaul capacity, bids on eligible shipments, manages awarded assignments. |
| **Fleet Manager** | Manages a transport company’s drivers and vehicles. | Manages company profile, vehicles, drivers, capacity declarations, assignments, and fleet reports. |
| **Verification Reviewer** | Checks submitted compliance evidence. | Reviews documents, approves or rejects verification, requests more information, records a reason and decision history. |
| **Operations Manager** | Oversees active marketplace operations. | Monitors auctions, handles exceptions, intervenes in assignments, manages disputes, and follows delivery risks. |
| **Finance Officer** | Oversees commercial records. | Reviews commissions, invoice references, payment references, adjustments, and reconciliation status. |
| **Support Agent** | Assists users with controlled access. | Opens and follows support cases without broad financial or configuration access. |
| **Naqil Administrator** | Owns platform configuration and audit access. | Manages roles, settings, policy versions, elevated exceptions, and audit reporting. |

## 3. Verification and Onboarding

### 3.1 Registration

Every user begins as a Frappe User linked to a role-specific profile. A person can hold more than one role only if the platform explicitly approves that relationship. A carrier operating as a company must have a company profile and at least one authorised manager before it can bid.

| Profile | Required outcome before marketplace activity |
|---|---|
| Customer / Shipper | Verified contact information and required organisation/identity information under the approved policy. |
| Carrier | Approved carrier profile, required commercial/transport credentials, authorised contact, and at least one verified operating vehicle where applicable. |
| Fleet Company | Approved company profile, authorised manager, and vehicles/drivers recorded before enterprise operations. |

### 3.2 Verification Case

Every verification submission creates a **Verification Case** with a state of `Draft`, `Submitted`, `Under Review`, `More Information Required`, `Approved`, `Rejected`, `Suspended`, or `Expired`. The reviewer must not overwrite source documents silently. Every decision requires a reason, the reviewing user, a timestamp, and any policy version used.

### 3.3 Document Rules

Documents must be stored privately and linked to the profile or verification case, not exposed through a public URL. The system must record document type, owner, expiry date where applicable, verifier decision, and replacement history. The public frontend may show only safe status labels such as “verification in review” or “document needs replacement.”

### 3.4 Administrator-Defined Verification Policy

Verification is governed by a versioned **Verification Policy** managed by a Naqil Administrator. The policy defines required document types, applicable party types, whether a document is mandatory before registration, bidding, award, or payout, expiry requirements, review SLA, and suspension rules. A submitted verification case records the policy version in force at the time of submission, so later policy changes never rewrite the historical basis of a decision.

| Administrator-configured policy field | Example use |
|---|---|
| Party type and operation | Require a carrier transport licence before bidding, or a company registration before publishing commercial freight. |
| Required document set | Define identity, licence, company, vehicle, driver, insurance, or other approved evidence. |
| Expiry and renewal window | Trigger renewal warnings and restrict selected actions after expiry. |
| Review rule | Require manual review, allow approved provider result, or request more information. |
| Enforcement point | Control whether the policy blocks registration, bidding, award, assignment confirmation, invoice, or settlement. |

## 4. Shipment Request Lifecycle

### 4.1 Shipment Creation

The customer creates a **Shipment Request** with an origin, destination, pickup and delivery windows, cargo details, required vehicle/equipment, estimated weight and volume, special handling needs, bid deadline, and a maximum budget only if the customer chooses to disclose one.

The request remains in `Draft` until the customer submits it. Server-side validation must confirm that route, time, cargo, equipment, and auction fields are complete and internally consistent. The system creates a permanent tracking code only after the request becomes public.

### 4.2 Shipment States

| State | Meaning | Permitted next states |
|---|---|---|
| `Draft` | Customer is still preparing the request. | Submitted, Cancelled. |
| `Pending Review` | Platform review is required by policy or risk rule. | Open for Bidding, Returned for Changes, Cancelled. |
| `Open for Bidding` | Eligible carriers may bid until the auction closes. | Bid Selection, Expired Without Award, Cancelled. |
| `Bid Selection` | The auction is closed; customer evaluates eligible offers. | Awarded, Reopened, Expired Without Award. |
| `Awarded` | One carrier is assigned through an accepted bid. | Carrier Confirmed, Cancelled by Exception. |
| `Carrier Confirmed` | Carrier has confirmed the assignment. | Pickup Scheduled, Cancelled by Exception. |
| `Pickup Scheduled` | Pickup time and vehicle are confirmed. | In Transit, Cancelled by Exception. |
| `In Transit` | Cargo has been collected. | Delivered, Delivery Exception. |
| `Delivery Exception` | A delivery issue requires recorded operations action. | In Transit, Delivered, Cancelled by Exception, Disputed. |
| `Delivered` | Delivery has been confirmed under the agreed proof process. | Rated, Disputed. |
| `Disputed` | A commercial or service dispute is open. | Resolved, Cancelled by Exception. |
| `Closed` | Commercial and operational records are complete. | None except audited administrative correction. |
| `Cancelled` | Request ended before normal completion. | None except audited administrative correction. |

## 5. Reverse Auction

### 5.1 Bid Eligibility

A carrier may submit a bid only when all of the following are true:

| Rule | Validation owner |
|---|---|
| Shipment is `Open for Bidding` and before its close timestamp. | Server-side auction service. |
| Carrier account and profile are approved and not suspended or expired. | Verification service. |
| Carrier is permitted to access the route and cargo category. | Role, profile, and capability rules. |
| Proposed vehicle fits required equipment, capacity, and cargo restrictions. | Vehicle-capability rules. |
| Carrier does not have an unresolved restriction that blocks bidding. | Operations and compliance rules. |

### 5.2 Bid Submission

Each **Carrier Bid** contains a monetary amount, selected vehicle, driver or driver placeholder, estimated pickup and delivery time, optional explanatory note, and a status. The bid is immutable after the auction close. Before close, a carrier may withdraw a pending bid or replace it according to the auction policy; the system preserves the prior bid as history rather than deleting it.

The backend validates numeric amounts, currency, relevant dates, eligibility, and whether the same carrier has an active bid. It must support idempotency so a mobile-network retry cannot create duplicate offers.

### 5.3 Auction Close and Award

The scheduled job identifies due auctions, but the API must independently reject any bid submitted after the close timestamp. When an auction closes, all valid offers are frozen and the shipment moves to `Bid Selection`. The customer selects the winning eligible offer. Automatic selection is not part of the first release unless an explicit future policy is approved.

Once an award succeeds, the platform changes exactly one bid to `Accepted`, marks all remaining eligible bids as `Not Selected`, records the award decision, calculates the configured commission, and emits notifications. This action must be atomic: two concurrent acceptance attempts cannot produce two winners.

### 5.4 Bid Statuses

| Bid status | Meaning |
|---|---|
| `Draft` | Carrier has not yet submitted the offer. |
| `Submitted` | Valid pending offer during the open auction. |
| `Withdrawn` | Carrier withdrew the offer before the deadline. |
| `Invalidated` | The system or operations team invalidated the offer with a recorded reason. |
| `Eligible at Close` | Offer was valid when bidding ended and is available for selection. |
| `Accepted` | Customer award has selected this offer. |
| `Not Selected` | Auction closed or customer chose another eligible offer. |
| `Expired` | Offer became invalid because the auction ended without selection or the shipment was cancelled. |

## 6. Backhaul and Empty Capacity

### 6.1 Capacity Declaration

A verified carrier or fleet manager may declare a **Backhaul Trip** with vehicle, current or expected location, intended direction, earliest/latest departure, available weight and volume, equipment, cargo restrictions, willingness to accept detours, target price guidance, and public-marketplace opt-in.

The declaration is not an automatic booking. It is a capacity signal that can create recommendations for eligible shipments. A carrier must explicitly accept an assignment or submit a bid unless a future enterprise contract creates a separate allocation rule.

### 6.2 Match Recommendations

The first release uses transparent rule-based matching. A recommendation score is calculated from route direction, origin proximity, destination compatibility, timing, vehicle/equipment fit, available weight/volume, cargo constraints, urgency, and price feasibility. The score is accompanied by concise reasons such as “same destination city,” “fits 4-ton remaining capacity,” or “pickup window overlaps planned departure.”

No match may automatically take a public shipment away from normal marketplace participation. A backhaul recommendation gives the carrier another eligible opportunity, while the shipment continues to follow its approved auction policy.

### 6.3 Market-Balance Protection

Backhaul opportunities may create lower-cost offers because a carrier would otherwise return empty. The platform must not let this permanently exclude carriers that need normal outbound economics. First-release safeguards are:

| Safeguard | Product rule |
|---|---|
| Transparent label | The customer can see that an offer uses return capacity when the carrier elects to disclose it under policy. |
| Price-floor policy | The platform may enforce a configurable route/category floor once approved by operations policy. |
| Market separation in analytics | Backhaul performance is measured separately from ordinary outbound auctions. |
| No automatic prioritisation | A backhaul offer is eligible but is not auto-selected solely because it is cheaper. |
| Review alerts | Operations receives an alert when repeated undercutting on a route crosses the defined policy threshold. |

### 6.4 Administrator-Defined Backhaul Policy

The **Backhaul Policy** is dynamically managed by the Naqil Administrator instead of being hard-coded. Policies are versioned, effective-dated, and scoped by route, city pair, cargo category, vehicle type, customer class, or carrier/fleet class. A recommendation and any related bid record the policy version used when it was calculated.

| Dynamic backhaul control | Operational purpose |
|---|---|
| Public-marketplace opt-in default | Determines whether a carrier/fleet must explicitly opt in before empty capacity is visible to marketplace matching. |
| Price floor and ceiling rule | Protects market balance while allowing a defined return-capacity discount. |
| Maximum permitted detour | Limits recommendations that add excessive distance or time. |
| Capacity and equipment eligibility | Restricts matching to safe and compliant vehicle/cargo combinations. |
| Route/category promotion rule | Allows administrators to temporarily prioritise strategic routes or categories with an auditable reason. |
| Visibility label | Controls whether customers see a “return capacity” label on qualifying offers. |
| Alert threshold | Defines when repeated undercutting, non-response, or poor acceptance rates require operations review. |

## 7. Assignment, Pickup, and Delivery

After award, the carrier confirms the selected vehicle and driver within an approved confirmation window. Operations may intervene only through an exception workflow. The system then records scheduled pickup, actual pickup, in-transit milestones, delivery proof, and actual delivery.

| Milestone | Evidence or authority |
|---|---|
| Carrier confirmation | Carrier manager or authorised carrier user; assigned vehicle remains eligible. |
| Pickup scheduled | Customer/carrier agreement or operations confirmation. |
| Pickup completed | Carrier action with timestamp; optional policy-required pickup evidence may be attached privately. |
| Delivery completed | Carrier submits a signed delivery document; customer confirmation or approved operations exception finalises the milestone. |
| Delivery exception | Carrier, customer, or operations creates a case with reason and supporting evidence. |

### 7.1 Signed Delivery Evidence

Delivery completion requires a **Signed Delivery Evidence** record. The carrier uploads a private signed document—such as a signed delivery receipt, bill of lading, or approved proof-of-delivery form—and records document type, signer name, signer role, signed timestamp, receiving location, and any declared exception. The platform stores the file privately and preserves its version history.

The customer receives a safe notification and can confirm or dispute the evidence. If the customer does not respond within the administrator-defined confirmation window, the case is escalated to operations; no silent automatic completion occurs unless a future policy expressly permits it. An operations reviewer may finalise delivery only through an audited exception decision.

## 8. Notifications and Real-Time Events

Naqil sends notifications through an auditable notification record. The first release supports in-app and email-ready notification events; SMS, WhatsApp, or push providers are integration choices rather than assumptions.

| Trigger | Customer | Carrier | Operations |
|---|---|---|---|
| Verification submitted or decided | Yes | Yes | Reviewer queue update. |
| Shipment opened | Confirmation | Eligible route opportunity where policy permits. | Optional monitoring. |
| New bid | Bid-count and offer update. | Submission acknowledgement. | None unless risk rule triggers. |
| Auction closing soon | Reminder. | Reminder to participating bidders. | Exception alert if necessary. |
| Award and confirmation | Winning-offer summary. | Award/confirmation action. | Escalation if unconfirmed. |
| Delivery exception or dispute | Case update. | Case update. | Operations case assignment. |

## 9. Disputes, Ratings, and Support

Every dispute is a **Dispute Case** linked to a shipment, assignment, and relevant parties. The case records category, description, supporting documents, evidence timeline, owner, internal notes, decision, and any financial adjustment reference. No ordinary user can alter another party’s evidence.

Ratings are permitted only after a delivered shipment. A customer may rate a carrier and a carrier may rate a customer according to a controlled policy. Ratings must be separated from verification status and must not be editable after the policy-defined window except through an audited support process.

## 10. Enterprise Fleet SaaS

The first release establishes the fleet-company structure without claiming full optimisation. A fleet manager can manage company records, authorised users, vehicles, drivers, capacity declarations, and assigned jobs. The system can produce basic utilisation, available-capacity, verified-driver, and assignment-status reporting.

| Enterprise capability | First-release status | Later expansion |
|---|---|---|
| Fleet company and user management | Included. | Multi-entity group reporting. |
| Vehicles and drivers | Included. | Telematics synchronization and maintenance planning. |
| Empty-capacity declaration | Included. | Automatic capacity extraction from external dispatch systems. |
| Fleet assignments | Included for marketplace-awarded jobs. | Internal job dispatch and advanced route allocation. |
| Route planning | Recommendation explanation only. | Multi-stop optimisation with real distance and operating constraints. |
| Dynamic pricing | Policy-ready signal record only. | Measured pricing model after approved data governance. |

## 11. Administration Workspace

The Frappe Desk workspace is the trusted operations centre. It must contain role-specific queues rather than one unrestricted dashboard.

| Workspace area | Responsible role | Core actions |
|---|---|---|
| Verification Queue | Verification Reviewer | Open case, review documents, request information, approve/reject, record reason. |
| Marketplace Monitor | Operations Manager | View active auctions, deadlines, bid count, award/confirmation risks, and exceptions. |
| Delivery Exceptions | Operations Manager and Support | Assign case, request evidence, apply approved resolution path. |
| Finance Review | Finance Officer | View commissions, invoice/payment references, adjustments, and reconciliation status. |
| Platform Settings | Naqil Administrator | Manage approved configuration, commission policy, auction defaults, document policy, and feature flags. |
| Audit and Reports | Naqil Administrator | Review state changes, access-sensitive actions, and operational reports. |

## 12. Finance, Invoicing, Escrow, and Settlement

Naqil will include a complete **financial lifecycle** in the design: invoice issuance, payment references, escrow state, carrier settlement, commission calculation, refunds/adjustments, and reconciliation. A regulated payment or escrow provider executes any real movement or custody of money; Frappe records the authoritative commercial state, provider references, and audit trail. The platform must never claim to hold funds unless the approved provider and legal operating model support that function.

When a bid is awarded, the system snapshots bid amount, commission percentage, commission amount, finance policy version, customer liability, carrier payable amount, and any applicable tax fields. A **Commission Ledger** records adjustments separately and never overwrites the original award calculation.

| Financial record | Responsibility |
|---|---|
| Invoice | Customer-facing payable document linked to shipment, award, policy version, due date, and line items. |
| Payment Reference | Provider transaction identifier, payment method, amount, status, webhook/audit history, and reconciliation result. |
| Escrow Case | Records intended amount, held/released/refunded/disputed state, provider reference, release conditions, and exception history. |
| Carrier Settlement | Records payable amount, release condition, settlement reference, payout status, and adjustment links. |
| Commission Ledger | Records Naqil commission, tax treatment, adjustment, refund impact, and reconciliation state. |
| Refund/Adjustment | Records reason, authority, affected invoice/escrow/settlement, and provider reference. |

The first payment integration must be selected and legally validated before money movement is enabled. Until that integration is live, records may remain in a controlled `Awaiting Payment Setup` state and cannot be misrepresented as real escrow.

## 13. Explicit First-Release Exclusions

The following remain excluded until reliable operating data, policy, and integrations are approved: automatic award to the lowest bid, always-on GPS tracking, machine-learning demand prediction, automated multi-stop route optimisation, and automatic price changes outside an approved dynamic policy. Financial records and escrow state are included, but external fund custody or transfer is enabled only after a compliant provider integration and operational approval.

## 14. Acceptance Scenarios

The implementation is acceptable only when the following outcomes can be demonstrated against real backend records:

| Scenario | Required result |
|---|---|
| Unverified carrier attempts to bid | Server rejects the action and records no bid. |
| Customer creates a valid shipment | Shipment is stored, owned by the customer, and transitions through the defined workflow. |
| Carrier submits a valid bid twice due to retry | One bid is created; retry returns the original result. |
| Auction deadline passes | Late bid is rejected even if the scheduler has not yet run. |
| Customer selects a bid | Exactly one bid becomes accepted and all linked records are updated atomically. |
| Carrier is awarded but does not confirm | Operations sees an escalation after the configured window. |
| Backhaul recommendation is shown | Recommendation has recorded score inputs and human-readable reasons. |
| Reviewer rejects a document | User sees safe status and the decision/audit reason remains available internally. |
| Unauthorised user accesses another record | Frappe permission checks deny access at API level. |

## 15. Approved Product Decisions and Remaining Parameters

The customer selects the winning eligible bid. The financial model includes invoices, payment references, escrow, and settlement records. Verification policy and backhaul policy are dynamically defined by the Naqil Administrator with policy versioning. Delivery evidence is a private signed-document upload. The Frappe backend will use a Docker architecture deployed as multiple Railway services.

The remaining administrator-defined parameters are the required document sets, review SLA, backhaul price floors/ceilings, detour limits, delivery-confirmation window, commission/tax rules, escrow release conditions, dispute authority, supported languages/currencies, and the approved external payment/escrow provider.
