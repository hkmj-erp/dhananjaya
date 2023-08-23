import frappe

from dhananjaya.dhananjaya.utils import get_preachers

DCC_ADMIN_ROLES = ["DCC Manager", "DCC Executive", "DCC Cashier"]


def query(user):
    if not user:
        user = frappe.session.user

    user_roles = frappe.get_roles(user)

    full_access = any(role in DCC_ADMIN_ROLES for role in user_roles)

    if full_access:
        return "( 1 )"

    # return "( 1 )"

    preachers = get_preachers()

    if len(preachers) == 0:
        return "( 0 )"
    else:
        preachers_str = ",".join([f"'{p}'" for p in preachers])
        return f" ( `preacher` in ( {preachers_str} ) ) "
