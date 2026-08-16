import frappe
from frappe.model.document import Document

from naqil.permissions import require_organization_access
from naqil.policies import get_active_backhaul_policy


class NaqilBackhaulCapacity(Document):
    def before_insert(self):
        require_organization_access(self.carrier_organization, {"Owner", "Operations", "Dispatcher"})
        policy = get_active_backhaul_policy()
        full_policy = frappe.get_doc("Naqil Backhaul Policy", policy.name)
        if full_policy.requires_carrier_verification and frappe.db.get_value(
            "Naqil Organization", self.carrier_organization, "status"
        ) != "Active":
            frappe.throw("The active backhaul policy requires carrier verification.")
        if full_policy.requires_marketplace_opt_in and not self.marketplace_opt_in:
            frappe.throw("The active backhaul policy requires explicit marketplace opt-in.")
        self.policy = policy.name
        self.policy_version = policy.policy_version

    def validate(self):
        if self.available_until <= self.available_from:
            frappe.throw("Capacity availability end must be after the start.")
        if self.capacity_weight_kg <= 0:
            frappe.throw("Available weight must be greater than zero.")
        if self.origin_city.strip().lower() == self.destination_city.strip().lower():
            frappe.throw("Backhaul origin and destination must differ.")
