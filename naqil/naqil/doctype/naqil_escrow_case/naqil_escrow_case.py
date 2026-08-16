import frappe
from frappe.model.document import Document


class NaqilEscrowCase(Document):
    def validate(self):
        if self.amount <= 0:
            frappe.throw("Escrow amount must be greater than zero.")
        if self.status in {"Reserved", "Held", "Released", "Refunded"} and not self.provider_case_reference:
            frappe.throw("A provider case reference is required for provider-managed escrow states.")
