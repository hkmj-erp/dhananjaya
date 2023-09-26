import frappe
from dhananjaya.dhananjaya.notification_tags import DJNotificationTags
from dhananjaya.dhananjaya.utils import check_user_notify

@frappe.whitelist()
def execute():
    show_reminders()


def show_reminders():
    settings_doc = frappe.get_cached_doc("Dhananjaya Settings")
    for i in frappe.db.sql(
        """
                    select *
                    from `tabDJ Reminder`
                    where DATE_FORMAT(remind_at, '%Y-%m-%d %H:%i') = DATE_FORMAT(NOW(), '%Y-%m-%d %H:%i')
                    """,
        as_dict=1,
    ):
        doc = frappe.get_doc(
            {
                "doctype": "App Notification",
                "app": settings_doc.firebase_admin_app,
                "tag": DJNotificationTags.DONOR_REMINDER_TAG,
                "notify": check_user_notify(i["user"], DJNotificationTags.DONOR_REMINDER_TAG),
                "user": i["user"],
                "subject": "Reminder",
                "message": i["message"],
                "is_route": 1 if i["donor"] else 0,
                "route": f"/donor/{i['donor']}",
            }
        )
        doc.insert(ignore_permissions=True)
    frappe.db.commit()



