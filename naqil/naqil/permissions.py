"""Authorization helpers shared by Naqil document controllers and RPC methods."""

import frappe


PLATFORM_ROLES = {
    "Naqil Administrator",
    "Naqil Operations Manager",
    "Naqil Verification Reviewer",
    "Naqil Finance Officer",
    "Naqil Support Agent",
    "System Manager",
}


def current_user_roles():
    return set(frappe.get_roles(frappe.session.user))


def is_platform_staff(user=None):
    return bool(PLATFORM_ROLES.intersection(frappe.get_roles(user or frappe.session.user)))


def require_any_role(*roles):
    if not set(roles).intersection(current_user_roles()):
        frappe.throw("You are not permitted to perform this action.", frappe.PermissionError)


def membership_for_user(organization, user=None):
    user = user or frappe.session.user
    return frappe.db.get_value(
        "Naqil Membership",
        {"organization": organization, "user": user, "status": "Active"},
        ["name", "membership_role"],
        as_dict=True,
    )


def require_organization_access(organization, allowed_membership_roles=None):
    if is_platform_staff():
        return None

    membership = membership_for_user(organization)
    if not membership:
        frappe.throw("You do not have access to this organization.", frappe.PermissionError)

    if allowed_membership_roles and membership.membership_role not in allowed_membership_roles:
        frappe.throw("Your organization role does not allow this action.", frappe.PermissionError)

    return membership
