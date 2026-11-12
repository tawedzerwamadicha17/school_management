import frappe

ROLES = ["Academics User"]


def ensure_roles():
    """Roles the app's permissions rely on (previously supplied by the Education app)."""
    for role in ROLES:
        if not frappe.db.exists("Role", role):
            frappe.get_doc({"doctype": "Role", "role_name": role, "desk_access": 1}).insert(ignore_permissions=True)


def has_app_permission():
    """Who sees the School Management icon on the apps screen."""
    return bool({"System Manager", "Academics User"} & set(frappe.get_roles()))
