import frappe

@frappe.whitelist()
def execute():
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