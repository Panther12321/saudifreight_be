import frappe
from frappe.model.document import Document


class NaqilMembership(Document):
    def validate(self):
        if self.user == "Guest":
            frappe.throw("Guest cannot be granted an organization membership.")

        duplicate = frappe.db.exists(
            "Naqil Membership",
            {"organization": self.organization, "user": self.user, "name": ["!=", self.name]},
        )
        if duplicate:
            frappe.throw("This user already has a membership for the organization.")

    def before_insert(self):
        self.invited_by = frappe.session.user
