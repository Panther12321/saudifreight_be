"""Document-level and list-level authorization for organization-owned Naqil records."""

import frappe

from naqil.permissions import is_platform_staff, membership_for_user


def _organization_condition(doctype, user):
    if is_platform_staff(user):
        return None

    organizations = frappe.get_all(
        "Naqil Membership",
        filters={"user": user, "status": "Active"},
        pluck="organization",
    )
    if not organizations:
        return "1=0"

    escaped = ", ".join(frappe.db.escape(name) for name in organizations)
    return f"`tab{doctype}`.`organization` IN ({escaped})"


def _membership_organizations(user):
    return frappe.get_all(
        "Naqil Membership",
        filters={"user": user, "status": "Active"},
        pluck="organization",
    )


def _escaped_organizations(user):
    organizations = _membership_organizations(user)
    return ", ".join(frappe.db.escape(name) for name in organizations) if organizations else None


def verification_case_query_condition(user=None):
    return _organization_condition("Naqil Verification Case", user or frappe.session.user)


def document_evidence_query_condition(user=None):
    user = user or frappe.session.user
    if is_platform_staff(user):
        return None
    escaped = _escaped_organizations(user)
    if not escaped:
        return "1=0"
    return (
        f"`tabNaqil Document Evidence`.`organization` IN ({escaped}) "
        "OR `tabNaqil Document Evidence`.`verification_case` IN ("
        "SELECT name FROM `tabNaqil Verification Case` "
        f"WHERE organization IN ({escaped}))"
    )


def shipment_query_condition(user=None):
    user = user or frappe.session.user
    if is_platform_staff(user):
        return None
    escaped = _escaped_organizations(user)
    roles = set(frappe.get_roles(user))
    public_market_access = bool({"Naqil Carrier", "Naqil Fleet Manager"}.intersection(roles))
    if not escaped:
        return "`tabNaqil Shipment`.`status` = 'Open for Bidding'" if public_market_access else "1=0"

    organization_access = (
        f"`tabNaqil Shipment`.`customer_organization` IN ({escaped}) "
        f"OR `tabNaqil Shipment`.`carrier_organization` IN ({escaped})"
    )
    if public_market_access:
        return f"({organization_access}) OR `tabNaqil Shipment`.`status` = 'Open for Bidding'"
    return f"({organization_access})"


def carrier_offer_query_condition(user=None):
    user = user or frappe.session.user
    if is_platform_staff(user):
        return None
    escaped = _escaped_organizations(user)
    if not escaped:
        return "1=0"
    return (
        f"`tabNaqil Carrier Offer`.`carrier_organization` IN ({escaped}) "
        "OR `tabNaqil Carrier Offer`.`shipment` IN ("
        "SELECT name FROM `tabNaqil Shipment` "
        f"WHERE customer_organization IN ({escaped}))"
    )


def delivery_evidence_query_condition(user=None):
    user = user or frappe.session.user
    if is_platform_staff(user):
        return None
    escaped = _escaped_organizations(user)
    if not escaped:
        return "1=0"
    return (
        "`tabNaqil Delivery Evidence`.`shipment` IN ("
        "SELECT name FROM `tabNaqil Shipment` "
        f"WHERE customer_organization IN ({escaped}) OR carrier_organization IN ({escaped}))"
    )


def finance_query_condition(doctype, user=None):
    user = user or frappe.session.user
    if is_platform_staff(user):
        return None
    escaped = _escaped_organizations(user)
    if not escaped:
        return "1=0"
    if doctype == "Naqil Invoice":
        return f"`tabNaqil Invoice`.`bill_to_organization` IN ({escaped}) OR `tabNaqil Invoice`.`carrier_organization` IN ({escaped})"
    if doctype == "Naqil Settlement":
        return f"`tabNaqil Settlement`.`carrier_organization` IN ({escaped})"
    return "1=0"


def invoice_query_condition(user=None):
    return finance_query_condition("Naqil Invoice", user)


def settlement_query_condition(user=None):
    return finance_query_condition("Naqil Settlement", user)


def verification_case_has_permission(doc, user=None, permission_type=None):
    user = user or frappe.session.user
    return bool(is_platform_staff(user) or membership_for_user(doc.organization, user))


def document_evidence_has_permission(doc, user=None, permission_type=None):
    user = user or frappe.session.user
    return bool(is_platform_staff(user) or membership_for_user(doc.organization, user))


def shipment_has_permission(doc, user=None, permission_type=None):
    user = user or frappe.session.user
    if is_platform_staff(user):
        return True
    if membership_for_user(doc.customer_organization, user) or (
        doc.carrier_organization and membership_for_user(doc.carrier_organization, user)
    ):
        return True
    return bool(doc.status == "Open for Bidding" and {"Naqil Carrier", "Naqil Fleet Manager"}.intersection(frappe.get_roles(user)))


def carrier_offer_has_permission(doc, user=None, permission_type=None):
    user = user or frappe.session.user
    if is_platform_staff(user) or membership_for_user(doc.carrier_organization, user):
        return True
    shipment = frappe.get_doc("Naqil Shipment", doc.shipment)
    return bool(membership_for_user(shipment.customer_organization, user))


def delivery_evidence_has_permission(doc, user=None, permission_type=None):
    user = user or frappe.session.user
    if is_platform_staff(user):
        return True
    shipment = frappe.get_doc("Naqil Shipment", doc.shipment)
    return bool(
        membership_for_user(shipment.customer_organization, user)
        or membership_for_user(shipment.carrier_organization, user)
    )


def invoice_has_permission(doc, user=None, permission_type=None):
    user = user or frappe.session.user
    return bool(
        is_platform_staff(user)
        or membership_for_user(doc.bill_to_organization, user)
        or membership_for_user(doc.carrier_organization, user)
    )


def settlement_has_permission(doc, user=None, permission_type=None):
    user = user or frappe.session.user
    return bool(is_platform_staff(user) or membership_for_user(doc.carrier_organization, user))


def organization_has_permission(doc, user=None, permission_type=None):
    user = user or frappe.session.user
    return bool(
        is_platform_staff(user)
        or doc.owner_user == user
        or membership_for_user(doc.name, user)
    )


def membership_has_permission(doc, user=None, permission_type=None):
    user = user or frappe.session.user
    if is_platform_staff(user) or doc.user == user:
        return True

    organization = frappe.get_doc("Naqil Organization", doc.organization)
    return organization.owner_user == user
