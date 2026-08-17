import frappe
from frappe.model.document import Document
from frappe.utils import get_datetime, now_datetime

from naqil.permissions import require_organization_access


class NaqilCarrierOffer(Document):
    def before_insert(self):
        require_organization_access(self.carrier_organization, {"Owner", "Operations", "Dispatcher"})
        self.submitted_by = frappe.session.user
        self.submitted_on = now_datetime()

    def validate(self):
        shipment = frappe.get_doc("Naqil Shipment", self.shipment)
        shipment_auction_end = get_datetime(shipment.auction_end)
        estimated_pickup = get_datetime(self.estimated_pickup)
        estimated_delivery = get_datetime(self.estimated_delivery)

        if shipment.status != "Open for Bidding" or shipment_auction_end <= now_datetime():
            frappe.throw("This shipment is not accepting offers.")
        if self.amount <= 0:
            frappe.throw("Offer amount must be greater than zero.")
        if estimated_delivery <= estimated_pickup:
            frappe.throw("Estimated delivery must be after estimated pickup.")
        if frappe.db.get_value("Naqil Organization", self.carrier_organization, "status") != "Active":
            frappe.throw("Only active verified carrier organizations can submit an offer.")
