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
def portal_submit_verification_document(organization, requirement_code, document_label, document_file, expiry_date=None):
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
        return {"name": evidence.name, "verification_case": case_name, "status": evidence.status}

    return _run_as_organization_owner(organization, create_document)


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
