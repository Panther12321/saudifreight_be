import frappe
from frappe.model.document import Document


class NaqilVerificationPolicy(Document):
    def validate(self):
        if self.grace_period_days < 0:
            frappe.throw("Grace period cannot be negative.")

        requirement_codes = [row.requirement_code for row in self.requirements]
        if len(requirement_codes) != len(set(requirement_codes)):
            frappe.throw("Each verification requirement code must be unique within a policy.")

        if self.status == "Active" and not self.effective_from:
            frappe.throw("An active verification policy requires an effective date.")
