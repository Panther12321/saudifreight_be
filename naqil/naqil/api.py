"""Version-one RPC endpoints for the Naqil React client and Frappe Desk."""

import frappe
from frappe.utils import cint, now_datetime

from naqil.permissions import is_platform_staff, require_any_role, require_organization_access
from naqil.policies import get_active_verification_policy
from naqil.services.auction import award_offer, close_due_auction, issue_invoice


def _limit(value, default=20, maximum=100):
    return max(1, min(cint(value or default), maximum))


def _run_as_organization_owner(organization_name, callback):
    owner_user = frappe.db.get_value("Naqil Organization", organization_name, "owner_user")
    if not owner_user:
        frappe.throw("The organization does not have an owner user.")

    original_user = frappe.session.user
    frappe.set_user(owner_user)
    try:
        return callback()
    finally:
        frappe.set_user(original_user)


@frappe.whitelist()
def portal_create_customer_shipment(customer_organization, **shipment_values):
    """Create a shipment on behalf of an organization after server-side authorization."""
    require_any_role("Naqil Administrator")

    def create_shipment():
        shipment_values.update(
            {
                "doctype": "Naqil Shipment",
                "customer_organization": customer_organization,
                "created_by_customer": frappe.session.user,
            }
        )
        shipment = frappe.get_doc(shipment_values)
        shipment.insert()
        return {"name": shipment.name, "status": shipment.status}

    return _run_as_organization_owner(customer_organization, create_shipment)


@frappe.whitelist()
def portal_submit_carrier_offer(carrier_organization, shipment, amount, estimated_pickup, estimated_delivery, vehicle_type, offer_notes=None):
    """Submit a carrier offer as the verified carrier organization owner."""
    require_any_role("Naqil Administrator")

    def create_offer():
        offer = frappe.get_doc(
            {
                "doctype": "Naqil Carrier Offer",
                "shipment": shipment,
                "carrier_organization": carrier_organization,
                "amount": amount,
                "estimated_pickup": estimated_pickup,
                "estimated_delivery": estimated_delivery,
                "vehicle_type": vehicle_type,
                "offer_notes": offer_notes,
            }
        )
        offer.insert()
        return {"name": offer.name, "status": offer.status}

    return _run_as_organization_owner(carrier_organization, create_offer)


@frappe.whitelist()
def portal_submit_verification_document(organization, requirement_code, document_label, document_file, expiry_date=None, identity_type=None, document_number=None):
    """Persist a privately stored verification document under the active policy."""
    require_any_role("Naqil Administrator")

    def create_document():
        case_name = frappe.db.get_value(
            "Naqil Verification Case",
            {"organization": organization, "status": ["in", ["Open", "Under Review", "Action Required"]]},
        )
        if not case_name:
            policy = get_active_verification_policy()
            case = frappe.get_doc(
                {
                    "doctype": "Naqil Verification Case",
                    "organization": organization,
                    "verification_policy": policy.name,
                    "policy_version": policy.policy_version,
                    "status": "Open",
                    "opened_on": now_datetime(),
                }
            )
            case.insert()
            case_name = case.name
            frappe.db.set_value("Naqil Organization", organization, "verification_case", case_name)

        verification_case = frappe.get_doc("Naqil Verification Case", case_name)

        evidence = frappe.get_doc(
            {
                "doctype": "Naqil Document Evidence",
                "organization": organization,
                "verification_case": case_name,
                "requirement_code": requirement_code,
                "document_label": document_label,
                "document_file": document_file,
                "expiry_date": expiry_date,
                "status": "Submitted",
            }
        )
        evidence.insert()

        applicant = frappe.get_doc("Naqil Organization", organization)
        profile_updates = {}
        if requirement_code == "identity":
            if applicant.organization_type == "Carrier" and identity_type not in {"National ID", "Iqama"}:
                frappe.throw("Carrier identity type must be National ID or Iqama.")
            profile_updates["identity_expiry_date"] = expiry_date
            if (document_number or "").strip():
                profile_updates["identity_number"] = document_number.strip()
            if identity_type:
                profile_updates["identity_type"] = identity_type
        elif requirement_code == "transport_license":
            profile_updates["transport_license_expiry_date"] = expiry_date
            if (document_number or "").strip():
                profile_updates["transport_license_number"] = document_number.strip()
        elif requirement_code == "vehicle_registration":
            profile_updates["vehicle_registration_expiry_date"] = expiry_date
            if (document_number or "").strip():
                profile_updates["vehicle_registration_number"] = document_number.strip()
        if profile_updates:
            applicant.update(profile_updates)
            applicant.save()

        policy = frappe.get_doc("Naqil Verification Policy", verification_case.verification_policy)
        required_codes = {
            requirement.requirement_code
            for requirement in policy.requirements
            if requirement.is_mandatory and requirement.applies_to == applicant.organization_type
        }
        submitted_codes = {
            document.requirement_code
            for document in frappe.get_all(
                "Naqil Document Evidence",
                filters={"organization": organization, "status": "Submitted"},
                fields=["requirement_code"],
            )
        }
        submitted_to_review = bool(required_codes) and required_codes.issubset(submitted_codes)
        if submitted_to_review and applicant.status == "Draft":
            applicant.status = "Pending Verification"
            applicant.status_reason = ""
            applicant.save()

        return {
            "name": evidence.name,
            "verification_case": case_name,
            "status": evidence.status,
            "organization_status": applicant.status,
            "submitted_to_review": submitted_to_review,
        }

    return _run_as_organization_owner(organization, create_document)


@frappe.whitelist()
def portal_update_carrier_document_metadata(organization, requirement_code, document_number, identity_type=None):
    """Complete document metadata for an already-uploaded carrier document."""
    require_any_role("Naqil Administrator")

    def update_metadata():
        applicant = frappe.get_doc("Naqil Organization", organization)
        if applicant.organization_type != "Carrier":
            frappe.throw("The requested organization is not a carrier.")
        if requirement_code not in {"identity", "transport_license", "vehicle_registration"}:
            frappe.throw("Invalid carrier document requirement.")
        if not (document_number or "").strip():
            frappe.throw("Carrier document number is required.")
        if not frappe.db.exists("Naqil Document Evidence", {"organization": organization, "requirement_code": requirement_code}):
            frappe.throw("Upload the document before saving its number.")
        updates = {"identity": "identity_number", "transport_license": "transport_license_number", "vehicle_registration": "vehicle_registration_number"}
        setattr(applicant, updates[requirement_code], document_number.strip())
        if requirement_code == "identity":
            if identity_type not in {"National ID", "Iqama"}:
                frappe.throw("Carrier identity type must be National ID or Iqama.")
            applicant.identity_type = identity_type
        applicant.save()
        return {"organization": applicant.name, "requirement_code": requirement_code}

    return _run_as_organization_owner(organization, update_metadata)


@frappe.whitelist()
def list_carrier_applicants():
    """Return carrier organizations for ongoing administrative supervision."""
    require_any_role("Naqil Administrator", "Naqil Verification Reviewer")
    return frappe.get_all(
        "Naqil Organization",
        filters={"organization_type": "Carrier", "status": ["in", ["Pending Verification", "Active", "Suspended"]]},
        fields=["name", "organization_name", "contact_name", "contact_phone", "city", "status", "verification_case", "modified"],
        order_by="modified desc",
    )


@frappe.whitelist()
def list_customer_applicants():
    """Return customer organizations awaiting an administrative verification decision."""
    require_any_role("Naqil Administrator", "Naqil Verification Reviewer")
    return frappe.get_all(
        "Naqil Organization",
        filters={"organization_type": "Customer", "status": "Pending Verification"},
        fields=["name", "organization_name", "contact_name", "contact_phone", "verification_case", "modified"],
        order_by="modified desc",
    )


def _get_verification_applicant(organization, organization_type):
    applicant = frappe.get_doc("Naqil Organization", organization)
    if applicant.organization_type != organization_type:
        frappe.throw(f"The requested organization is not a {organization_type.lower()} applicant.")

    documents = frappe.get_all(
        "Naqil Document Evidence",
        filters={"organization": applicant.name},
        fields=["name", "requirement_code", "document_label", "document_file", "expiry_date", "status", "review_notes", "reviewed_by", "reviewed_on"],
        order_by="creation asc",
    )
    verification = None
    if applicant.verification_case:
        verification = frappe.get_doc("Naqil Verification Case", applicant.verification_case).as_dict()

    return {
        "organization": {
            "name": applicant.name,
            "organization_name": applicant.organization_name,
            "contact_name": applicant.contact_name,
            "contact_phone": applicant.contact_phone,
            "contact_email": applicant.contact_email,
            "city": applicant.city,
            "address": applicant.address,
            "identity_number": applicant.identity_number,
            "identity_type": applicant.identity_type,
            "identity_expiry_date": applicant.identity_expiry_date,
            "transport_license_number": applicant.transport_license_number,
            "transport_license_expiry_date": applicant.transport_license_expiry_date,
            "vehicle_registration_number": applicant.vehicle_registration_number,
            "vehicle_registration_expiry_date": applicant.vehicle_registration_expiry_date,
            "status": applicant.status,
            "status_reason": applicant.status_reason,
        },
        "verification": verification,
        "documents": documents,
    }


@frappe.whitelist()
def get_carrier_applicant(organization):
    """Return an applicant profile and its private verification documents for staff review."""
    require_any_role("Naqil Administrator", "Naqil Verification Reviewer")
    return _get_verification_applicant(organization, "Carrier")


@frappe.whitelist()
def get_customer_applicant(organization):
    """Return a customer applicant profile and its private verification documents for staff review."""
    require_any_role("Naqil Administrator", "Naqil Verification Reviewer")
    return _get_verification_applicant(organization, "Customer")


@frappe.whitelist()
def review_carrier_applicant(organization, decision, reason=None):
    """Approve or reject a carrier applicant after administrative document review."""
    require_any_role("Naqil Administrator", "Naqil Verification Reviewer")
    if decision not in {"approve", "reject"}:
        frappe.throw("Invalid review decision.")

    applicant = frappe.get_doc("Naqil Organization", organization)
    if applicant.organization_type != "Carrier":
        frappe.throw("The requested organization is not a carrier applicant.")
    if not applicant.verification_case:
        frappe.throw("The applicant has not submitted a verification case.")

    documents = frappe.get_all("Naqil Document Evidence", filters={"organization": applicant.name}, fields=["name"])
    if decision == "approve" and not documents:
        frappe.throw("The applicant cannot be approved before uploading verification documents.")
    if decision == "reject" and not (reason or "").strip():
        frappe.throw("A rejection reason is required.")

    verification = frappe.get_doc("Naqil Verification Case", applicant.verification_case)
    verification.set_decision("Verified" if decision == "approve" else "Rejected", (reason or "").strip())
    verification.save()

    applicant.status = "Active" if decision == "approve" else "Suspended"
    applicant.status_reason = "" if decision == "approve" else (reason or "").strip()
    applicant.save()
    return {"organization": applicant.name, "status": applicant.status, "verification_status": verification.status}


@frappe.whitelist()
def review_customer_applicant(organization, decision, reason=None):
    """Approve or reject a customer applicant after administrative document review."""
    require_any_role("Naqil Administrator", "Naqil Verification Reviewer")
    if decision not in {"approve", "reject"}:
        frappe.throw("Invalid review decision.")

    applicant = frappe.get_doc("Naqil Organization", organization)
    if applicant.organization_type != "Customer":
        frappe.throw("The requested organization is not a customer applicant.")
    if not applicant.verification_case:
        frappe.throw("The applicant has not submitted a verification case.")

    documents = frappe.get_all("Naqil Document Evidence", filters={"organization": applicant.name}, fields=["name"])
    if decision == "approve" and not documents:
        frappe.throw("The applicant cannot be approved before uploading verification documents.")
    if decision == "reject" and not (reason or "").strip():
        frappe.throw("A rejection reason is required.")

    verification = frappe.get_doc("Naqil Verification Case", applicant.verification_case)
    verification.set_decision("Verified" if decision == "approve" else "Rejected", (reason or "").strip())
    verification.save()

    applicant.status = "Active" if decision == "approve" else "Suspended"
    applicant.status_reason = "" if decision == "approve" else (reason or "").strip()
    applicant.save()
    return {"organization": applicant.name, "status": applicant.status, "verification_status": verification.status}


@frappe.whitelist()
def list_open_shipments(pickup_city=None, delivery_city=None, limit=20):
    filters = {"status": "Open for Bidding"}
    if pickup_city:
        filters["pickup_city"] = pickup_city.strip()
    if delivery_city:
        filters["delivery_city"] = delivery_city.strip()

    return frappe.get_all(
        "Naqil Shipment",
        filters=filters,
        fields=[
            "name", "shipment_title", "pickup_city", "delivery_city", "cargo_weight_kg",
            "vehicle_type", "auction_end", "offer_count", "lowest_offer_amount", "priority",
        ],
        order_by="auction_end asc",
        limit_page_length=_limit(limit),
    )


@frappe.whitelist()
def submit_carrier_offer(
    shipment, carrier_organization, amount, estimated_pickup, estimated_delivery,
    vehicle_type, vehicle_reference=None, offer_notes=None,
):
    require_organization_access(carrier_organization, {"Owner", "Operations", "Dispatcher"})
    offer = frappe.get_doc(
        {
            "doctype": "Naqil Carrier Offer",
            "shipment": shipment,
            "carrier_organization": carrier_organization,
            "amount": amount,
            "estimated_pickup": estimated_pickup,
            "estimated_delivery": estimated_delivery,
            "vehicle_type": vehicle_type,
            "vehicle_reference": vehicle_reference,
            "offer_notes": offer_notes,
        }
    )
    offer.insert()
    return {"name": offer.name, "status": offer.status}


@frappe.whitelist()
def close_auction(shipment):
    shipment_doc = frappe.get_doc("Naqil Shipment", shipment)
    require_organization_access(shipment_doc.customer_organization, {"Owner", "Operations", "Dispatcher"})
    if shipment_doc.auction_end > now_datetime() and not is_platform_staff():
        frappe.throw("The customer cannot close an auction before its planned end time.")
    close_due_auction(shipment_doc.name)
    return {"name": shipment_doc.name, "status": frappe.db.get_value("Naqil Shipment", shipment_doc.name, "status")}


@frappe.whitelist()
def select_winning_offer(shipment, offer, rationale):
    awarded = award_offer(shipment, offer, rationale)
    return {"shipment": awarded.name, "status": awarded.status, "awarded_offer": awarded.awarded_offer}


@frappe.whitelist()
def submit_delivery_evidence(shipment, carrier_organization, signed_document, recipient_name, delivered_at):
    require_organization_access(carrier_organization, {"Owner", "Operations", "Dispatcher"})
    evidence = frappe.get_doc(
        {
            "doctype": "Naqil Delivery Evidence",
            "shipment": shipment,
            "carrier_organization": carrier_organization,
            "signed_document": signed_document,
            "recipient_name": recipient_name,
            "delivered_at": delivered_at,
        }
    )
    evidence.insert()
    frappe.db.set_value("Naqil Shipment", shipment, {"status": "Delivery Evidence Submitted", "delivery_evidence": evidence.name})
    return {"name": evidence.name, "status": evidence.status}


@frappe.whitelist()
def confirm_delivery(evidence):
    evidence_doc = frappe.get_doc("Naqil Delivery Evidence", evidence)
    shipment = frappe.get_doc("Naqil Shipment", evidence_doc.shipment)
    require_organization_access(shipment.customer_organization, {"Owner", "Operations", "Dispatcher"})
    evidence_doc.status = "Customer Confirmed"
    evidence_doc.customer_confirmed_by = frappe.session.user
    evidence_doc.customer_confirmed_on = now_datetime()
    evidence_doc.save()
    frappe.db.set_value("Naqil Shipment", shipment.name, "status", "Delivered")
    return {"shipment": shipment.name, "status": "Delivered"}


@frappe.whitelist()
def create_invoice(shipment, due_date=None):
    require_any_role("Naqil Administrator", "Naqil Finance Officer")
    invoice = issue_invoice(shipment, due_date)
    return {"invoice": invoice.name, "status": invoice.status, "payment_expires_on": invoice.payment_expires_on}


@frappe.whitelist()
def get_operations_summary():
    require_any_role("Naqil Administrator", "Naqil Operations Manager", "Naqil Finance Officer")
    return {
        "open_auctions": frappe.db.count("Naqil Shipment", {"status": "Open for Bidding"}),
        "selection_due": frappe.db.count("Naqil Shipment", {"status": "Selection Due"}),
        "pending_verification": frappe.db.count("Naqil Verification Case", {"status": ["in", ["Open", "Under Review"]]}),
        "issued_invoices": frappe.db.count("Naqil Invoice", {"status": "Issued"}),
    }
