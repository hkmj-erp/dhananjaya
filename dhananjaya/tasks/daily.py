import frappe
from datetime import datetime, timedelta

from dhananjaya.dhananjaya.doctype.donor_suggestion.task import donor_suggestions_task

@frappe.whitelist()
def execute():
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
