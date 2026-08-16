import frappe


def on_bid_created(doc, method=None):
    frappe.publish_realtime(
        "naqil_offer_submitted",
        {"shipment": doc.shipment, "offer": doc.name},
        after_commit=True,
    )
