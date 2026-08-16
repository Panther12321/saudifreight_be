import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime

from naqil.permissions import require_any_role, require_organization_access


class NaqilDocumentEvidence(Document):
    def before_insert(self):
        require_organization_access(self.organization, {"Owner", "Operations"})
        case = frappe.get_doc("Naqil Verification Case", self.verification_case)
        if case.organization != self.organization:
            frappe.throw("Document evidence must belong to the same organization as its verification case.")

    def validate(self):
        if not self.document_file.startswith("/private/files/"):
            frappe.throw("Verification documents must be uploaded as private files.")

    def set_review(self, status, notes=""):
        require_any_role("Naqil Administrator", "Naqil Verification Reviewer")
        if status not in {"Accepted", "Rejected"}:
            frappe.throw("Invalid evidence review status.")

        self.status = status
        self.review_notes = notes
        self.reviewed_by = frappe.session.user
        self.reviewed_on = now_datetime()
