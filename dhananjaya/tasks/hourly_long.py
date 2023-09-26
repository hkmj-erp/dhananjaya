import frappe
## Tasks which takes long time

def execute():
    update_donation_calculation()


def update_donation_calculation():
    ## Donor Data Update
    for d in frappe.db.sql(
        """
                    select donor, count(name) as times, sum(amount) as donation, max(receipt_date) as last_donation
                    from  `tabDonation Receipt` tdr
                    where (tdr.docstatus = 1) AND (tdr.donor IS NOT NULL)
                    group by tdr.donor
                    """,
        as_dict=1,
    ):
        frappe.db.set_value(
            "Donor",
            d["donor"],
            {"last_donation": d["last_donation"], "times_donated": d["times"], "total_donated": d["donation"]},
        )
    frappe.db.commit()

    ## Patron Data Update
    for d in frappe.db.sql(
        """
                    select patron, count(name) as times, sum(amount) as donation, max(receipt_date) as last_donation
                    from  `tabDonation Receipt` tdr
                    where (tdr.docstatus = 1) AND (tdr.patron IS NOT NULL)
                    group by tdr.patron
                    """,
        as_dict=1,
    ):
        frappe.db.set_value(
            "Patron",
            d["patron"],
            {"last_donation": d["last_donation"], "times_donated": d["times"], "total_donated": d["donation"]},
        )
    frappe.db.commit()
