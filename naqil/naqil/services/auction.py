"""Race-safe marketplace actions. An auction close never selects a winner automatically."""

import frappe
from frappe.utils import add_to_date, cint, flt, getdate, now_datetime

from naqil.permissions import require_any_role, require_organization_access


def _shipment(name, for_update=False):
    if for_update:
        rows = frappe.db.sql(
            """
            SELECT name FROM `tabNaqil Shipment`
            WHERE name = %s FOR UPDATE
            """,
            name,
            as_dict=True,
        )
        if not rows:
            frappe.throw("Shipment not found.")
    return frappe.get_doc("Naqil Shipment", name)


def close_due_auction(shipment_name):
    shipment = _shipment(shipment_name, for_update=True)
    if shipment.status != "Open for Bidding" or shipment.auction_end > now_datetime():
        return False

    new_status = "Selection Due" if shipment.offer_count else "Cancelled"
    frappe.db.set_value("Naqil Shipment", shipment.name, "status", new_status, update_modified=False)
    if new_status == "Selection Due":
        frappe.db.sql(
            """
            UPDATE `tabNaqil Carrier Offer`
            SET status = 'Expired'
            WHERE shipment = %s AND status = 'Submitted'
            """,
            shipment.name,
        )
    frappe.publish_realtime(
        "naqil_auction_closed",
        {"shipment": shipment.name, "status": new_status},
        after_commit=True,
    )
    return True


def award_offer(shipment_name, offer_name, rationale):
    shipment = _shipment(shipment_name, for_update=True)
    require_organization_access(shipment.customer_organization, {"Owner", "Operations", "Dispatcher"})

    if shipment.status != "Selection Due":
        frappe.throw("The auction must be closed before the customer selects an offer.")

    offer = frappe.get_doc("Naqil Carrier Offer", offer_name)
    if offer.shipment != shipment.name or offer.status not in {"Submitted", "Expired"}:
        frappe.throw("The selected offer is not eligible for this shipment.")
    if frappe.db.get_value("Naqil Organization", offer.carrier_organization, "status") != "Active":
        frappe.throw("The carrier organization is no longer active.")

    if not rationale or len(rationale.strip()) < 3:
        frappe.throw("The customer must provide an award rationale.")

    frappe.db.set_value(
        "Naqil Shipment",
        shipment.name,
        {
            "status": "Awarded",
            "awarded_offer": offer.name,
            "carrier_organization": offer.carrier_organization,
            "award_reason": rationale.strip(),
            "awarded_on": now_datetime(),
        },
        update_modified=False,
    )
    frappe.db.set_value(
        "Naqil Carrier Offer",
        offer.name,
        {"status": "Awarded", "awarded_on": now_datetime()},
        update_modified=False,
    )
    frappe.db.sql(
        """
        UPDATE `tabNaqil Carrier Offer`
        SET status = 'Not Selected'
        WHERE shipment = %s AND name != %s AND status IN ('Submitted', 'Expired')
        """,
        (shipment.name, offer.name),
    )
    frappe.publish_realtime(
        "naqil_offer_awarded",
        {"shipment": shipment.name, "offer": offer.name},
        after_commit=True,
    )
    return frappe.get_doc("Naqil Shipment", shipment.name)


def issue_invoice(shipment_name, due_date=None):
    require_any_role("Naqil Administrator", "Naqil Finance Officer")
    shipment = _shipment(shipment_name, for_update=True)
    if shipment.status not in {"Awarded", "Assigned", "Picked Up", "Delivery Evidence Submitted", "Delivered"}:
        frappe.throw("An invoice can be issued only after an offer is awarded.")
    if not shipment.awarded_offer or not shipment.carrier_organization:
        frappe.throw("Shipment award details are incomplete.")

    existing = frappe.db.exists("Naqil Invoice", {"shipment": shipment.name, "status": ["!=", "Cancelled"]})
    if existing:
        return frappe.get_doc("Naqil Invoice", existing)

    offer = frappe.get_doc("Naqil Carrier Offer", shipment.awarded_offer)
    settings = frappe.get_single("Naqil Platform Settings")
    expiry = add_to_date(now_datetime(), hours=cint(settings.payment_validity_hours))
    invoice = frappe.get_doc(
        {
            "doctype": "Naqil Invoice",
            "shipment": shipment.name,
            "bill_to_organization": shipment.customer_organization,
            "carrier_organization": shipment.carrier_organization,
            "subtotal_amount": flt(offer.amount),
            "commission_rate": flt(settings.default_commission_rate),
            "due_date": due_date or getdate(expiry),
            "payment_expires_on": expiry,
            "status": "Issued",
            "issued_on": now_datetime(),
        }
    )
    invoice.insert()
    return invoice
