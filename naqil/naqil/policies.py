"""Policy resolution helpers. Policies are versioned and never silently inferred."""

import frappe


def get_active_policy(doctype):
    policy = frappe.get_all(
        doctype,
        filters={"status": "Active"},
        fields=["name", "policy_version", "effective_from"],
        order_by="effective_from desc, modified desc",
        limit=1,
    )
    if not policy:
        frappe.throw(f"No active {doctype} is configured.")
    return policy[0]


def get_active_verification_policy():
    return get_active_policy("Naqil Verification Policy")


def get_active_backhaul_policy():
    return get_active_policy("Naqil Backhaul Policy")
