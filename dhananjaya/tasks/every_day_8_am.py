from datetime import datetime, timedelta
import frappe
from dhananjaya.dhananjaya.utils import get_preachers
from dhananjaya.dhananjaya.report.upcoming_special_pujas.puja_calculator import (
    get_puja_dates,
)

@frappe.whitelist()
def execute():
    special_puja_notify()


def special_puja_notify():
    current_date = datetime.now().date()
    tomorrow = current_date + timedelta(days=1)
    users = []
    for i in frappe.db.sql(
        """
                    select user
                    from `tabLLP Preacher User`
                    where 1
                    group by user
                    """,
        as_dict=1,
    ):
        users.append(i["user"])
    for u in users:
        preachers = get_preachers(u)
        for puja in get_puja_dates(tomorrow, tomorrow, preachers):
            settings_doc = frappe.get_cached_doc("Dhananjaya Settings")
            doc = frappe.get_doc(
                {
                    "doctype": "App Notification",
                    "app": settings_doc.firebase_admin_app,
                    "user": u,
                    "subject": puja["occasion"],
                    "message": f"Special Puja Tomorrow for {puja['donor_name']}",
                    "is_route": 1,
                    "route": f"/donor/{puja['donor_id']}",
                }
            )
            doc.insert(ignore_permissions=True)
    frappe.db.commit()
