import frappe


def on_shipment_update(doc, method=None):
    frappe.publish_realtime(
        "naqil_shipment_updated",
        {"shipment": doc.name, "status": doc.status},
        after_commit=True,
    )
