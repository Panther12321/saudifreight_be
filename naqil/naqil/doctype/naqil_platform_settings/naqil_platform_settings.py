import frappe
from frappe.model.document import Document


class NaqilPlatformSettings(Document):
    def validate(self):
        if self.default_commission_rate < 0 or self.default_commission_rate > 100:
            frappe.throw("Commission rate must be between 0 and 100 percent.")
        if self.payment_validity_hours < 1 or self.settlement_hold_hours < 0:
            frappe.throw("Payment validity and settlement hold controls must be valid durations.")
