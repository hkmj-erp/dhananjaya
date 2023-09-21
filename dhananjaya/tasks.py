from datetime import datetime, timedelta
from dhananjaya.dhananjaya.notification_tags import DJNotificationTags
from dhananjaya.dhananjaya.doctype.donor_suggestion.task import donor_suggestions_task
from dhananjaya.dhananjaya.report.upcoming_special_pujas.puja_calculator import (
    get_puja_dates,
)
from dhananjaya.dhananjaya.utils import check_user_notify, get_preachers, get_preachers
import frappe


@frappe.whitelist()
def daily():
    update_last_donation()
    donor_suggestions_task()
    delete_old_receipts_links()
    delete_old_notifications()


def update_last_donation():
    donor_map = frappe.db.sql(
        """
                    select d.name as donor, max(receipt_date) as last_donation
                    from `tabDonor` d
                    join `tabDonation Receipt` dr
                    on dr.donor = d.name
                    where dr.docstatus = 1
                    group by d.name
                    """,
        as_dict=1,
    )
    for map in donor_map:
        frappe.db.sql(
            f"""
                        update `tabDonor` donor
                        set donor.last_donation = '{map['last_donation']}'
                        where donor.name = '{map['donor']}'
                        """
        )
    frappe.db.commit()


@frappe.whitelist()
def hourly():
    update_realization_date()


def update_realization_date():
    receipts = frappe.db.sql(
        """
                    select je.posting_date as real_date,dr.name as receipt_id
                    from `tabDonation Receipt` dr
                    join `tabJournal Entry` je
                    on je.donation_receipt = dr.name
                    where dr.realization_date IS NULL
                    """,
        as_dict=1,
    )
    for r in receipts:
        frappe.db.set_value("Donation Receipt", r["receipt_id"], "realization_date", r["real_date"])

    frappe.db.commit()


@frappe.whitelist()
def every_day_daytime():
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
                    "tag": DJNotificationTags.SPECIAL_PUJA_TAG,
                    "notify": check_user_notify(u, DJNotificationTags.SPECIAL_PUJA_TAG),
                    "user": u,
                    "subject": puja["occasion"],
                    "message": f"Special Puja Tomorrow for {puja['donor_name']}",
                    "is_route": 1,
                    "route": f"/donor/{puja['donor_id']}",
                }
            )
            doc.insert(ignore_permissions=True)
    frappe.db.commit()


@frappe.whitelist()
def every_minute():
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


def delete_old_receipts_links():
    three_days_ago = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
    eligible_links = frappe.get_all(
        "DCC Redirect",
        filters=[["creation", "<", three_days_ago]],
        page_length=300,
        order_by="creation",
        pluck="name",
    )
    for link in eligible_links:
        frappe.delete_doc("DCC Redirect", link)
    frappe.db.commit()


def delete_old_notifications():
    one_month_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    eligible_notiifcations = frappe.get_all(
        "App Notification",
        filters=[["creation", "<", one_month_ago]],
        page_length=300,
        order_by="creation",
        pluck="name",
    )
    for n in eligible_notiifcations:
        frappe.delete_doc("App Notification", n)
    frappe.db.commit()


# for i in frappe.db.sql("""
#                     select *
#                     from `tabDJ Reminder`
#                     where DATE_FORMAT(remind_at, '%Y-%m-%d %H:%i') = DATE_FORMAT(NOW(), '%Y-%m-%d %H:%i')
#                     """,as_dict=1):
#         print(i)
#         doc = frappe.get_doc({
#                 'doctype': 'App Notification',
#                 'user': i['user'],
#                 'subject': "Processing Actual...",
#                 'message':"Processing Actual...",
#                 'is_route': 1 if i['donor'] else 0,
#                 'route':f"/donor/{i['donor']}"
#             })
#         doc.insert(ignore_permissions=True)
# frappe.db.commit()
