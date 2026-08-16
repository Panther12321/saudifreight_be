import frappe
from frappe.model.document import Document


class NaqilBackhaulPolicy(Document):
    def validate(self):
        if self.minimum_price_ratio < 0 or self.maximum_price_ratio > 100:
            frappe.throw("Backhaul price ratios must be between 0 and 100 percent.")
        if self.minimum_price_ratio > self.maximum_price_ratio:
            frappe.throw("Minimum price ratio cannot exceed the maximum price ratio.")
        if self.max_detour_km < 0 or self.max_matches_per_trip < 1:
            frappe.throw("Backhaul limits must be positive.")
        if self.status == "Active" and not self.effective_from:
            frappe.throw("An active backhaul policy requires an effective date.")
