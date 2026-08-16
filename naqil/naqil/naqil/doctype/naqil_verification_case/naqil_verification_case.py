import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime

from naqil.permissions import is_platform_staff, require_any_role, require_organization_access
from naqil.policies import get_active_verification_policy


class NaqilVerificationCase(Document):
    def before_insert(self):
        require_organization_access(self.organization, {"Owner", "Operations"})
        policy = get_active_verification_policy()
        self.verification_policy = policy.name
        self.policy_version = policy.policy_version
        self.opened_on = now_datetime()
        self.status = "Open"

    def validate(self):
        if self.status in {"Verified", "Rejected"} and not is_platform_staff():
            frappe.throw("Only Naqil staff can finalise a verification case.", frappe.PermissionError)

    def set_decision(self, status, reason):
        require_any_role("Naqil Administrator", "Naqil Verification Reviewer")
        if status not in {"Verified", "Rejected", "Action Required"}:
            frappe.throw("Invalid verification decision.")

        self.status = status
        self.reviewed_by = frappe.session.user
        self.reviewed_on = now_datetime()
        self.decision_reason = reason
