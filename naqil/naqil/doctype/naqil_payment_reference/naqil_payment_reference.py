import frappe
from frappe.model.document import Document


class NaqilPaymentReference(Document):
    def before_insert(self):
        self.recorded_by = frappe.session.user

    def validate(self):
        if self.amount <= 0:
            frappe.throw("Payment reference amount must be greater than zero.")
        if not self.provider_reference.strip():
            frappe.throw("A provider reference is required. Never store payment-card data in this record.")
