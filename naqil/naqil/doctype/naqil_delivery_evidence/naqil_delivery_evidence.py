import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime

from naqil.permissions import require_organization_access


class NaqilDeliveryEvidence(Document):
    def before_insert(self):
        require_organization_access(self.carrier_organization, {"Owner", "Operations", "Dispatcher"})
        shipment = frappe.get_doc("Naqil Shipment", self.shipment)
        if shipment.carrier_organization != self.carrier_organization:
            frappe.throw("Only the awarded carrier can submit delivery evidence.")

    def validate(self):
        if not self.signed_document.startswith("/private/files/"):
            frappe.throw("The signed delivery document must be stored as a private file.")
        if self.delivered_at > now_datetime():
            frappe.throw("Delivery time cannot be in the future.")
