import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime

from naqil.permissions import require_organization_access


class NaqilShipment(Document):
    def before_insert(self):
        require_organization_access(self.customer_organization, {"Owner", "Operations", "Dispatcher"})
        self.created_by_customer = frappe.session.user

    def validate(self):
        if self.pickup_window_end <= self.pickup_window_start:
            frappe.throw("Pickup window end must be after pickup window start.")
        if self.delivery_window_end <= self.pickup_window_start:
            frappe.throw("Delivery deadline must be after pickup begins.")
        if self.cargo_weight_kg <= 0:
            frappe.throw("Cargo weight must be greater than zero.")
        if self.status == "Open for Bidding" and self.auction_end <= now_datetime():
            frappe.throw("Auction end must be in the future when opening a shipment.")
