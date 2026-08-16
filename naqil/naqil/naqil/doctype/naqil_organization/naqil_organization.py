import frappe
from frappe.model.document import Document


class NaqilOrganization(Document):
    def validate(self):
        if self.owner_user == "Guest":
            frappe.throw("A registered user must own an organization.")

        if self.contact_email:
            self.contact_email = self.contact_email.strip().lower()

        if self.contact_phone:
            self.contact_phone = self.contact_phone.strip()
