"""Internal-only provisioning helpers for the Naqil server integration.

These functions are invoked through ``bench execute`` during deployment setup.
They are deliberately not Frappe RPC endpoints and must never be exposed to the
public web client.
"""

import json
from pathlib import Path

import frappe
from frappe.core.doctype.user.user import generate_keys


SERVICE_USER = "integration@naqil.internal"


def provision_service_user():
    """Create a dedicated system user and return a newly issued API key pair."""
    if not frappe.db.exists("User", SERVICE_USER):
        service_user = frappe.get_doc(
            {
                "doctype": "User",
                "email": SERVICE_USER,
                "first_name": "Naqil",
                "last_name": "Integration",
                "enabled": 1,
                "user_type": "System User",
                "send_welcome_email": 0,
                "roles": [{"role": "Naqil Administrator"}, {"role": "System Manager"}],
            }
        )
        service_user.flags.no_welcome_email = True
        service_user.insert()

    # The previous bridge credential was created against Administrator. Removing
    # its key invalidates that token pair before the dedicated credential is used.
    frappe.db.set_value("User", "Administrator", "api_key", None, update_modified=False)
    frappe.db.commit()

    service_user = frappe.get_doc("User", SERVICE_USER)
    existing_roles = {row.role for row in service_user.roles}
    if "System Manager" not in existing_roles:
        service_user.append("roles", {"role": "System Manager"})
        service_user.save()
    service_user.api_key = None
    service_user.save()
    frappe.db.commit()

    return generate_keys(SERVICE_USER)


def ensure_naqil_workspace():
    """Create or refresh the Naqil Desk workspace in the active Frappe site."""
    workspace_file = Path(__file__).parent / "naqil" / "workspace" / "naqil" / "naqil.json"
    with workspace_file.open(encoding="utf-8") as handle:
        data = json.load(handle)

    data["doctype"] = "Workspace"
    data.setdefault("title", data["label"])
    data["name"] = "Naqil Backend"
    data["route"] = "naqil-backend"
    data["public"] = 1
    if frappe.db.exists("Workspace", data["name"]):
        workspace = frappe.get_doc("Workspace", data["name"])
        workspace.update(data)
        workspace.save(ignore_permissions=True)
    else:
        legacy_workspace = frappe.db.get_value("Workspace", {"title": data["title"]}, "name")
        if legacy_workspace:
            frappe.delete_doc("Workspace", legacy_workspace, ignore_permissions=True, force=True)
        workspace = frappe.get_doc(data)
        workspace.insert(ignore_permissions=True)
    frappe.db.commit()
    return {"name": workspace.name, "label": workspace.label, "route": frappe.scrub(workspace.name)}
