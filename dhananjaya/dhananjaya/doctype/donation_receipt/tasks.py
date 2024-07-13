import frappe
from datetime import datetime, timedelta


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
            {
                "last_donation": d["last_donation"],
                "times_donated": d["times"],
                "total_donated": d["donation"],
            },
            update_modified=False,
        )
    frappe.db.commit()

    ## Patron Data Update
    for d in frappe.db.sql(
        """
                    SELECT tp.name as patron, count(tdr.name) as times, sum(tdr.amount) as donation, max(tdr.receipt_date) as last_donation
                    FROM `tabPatron` tp
                    LEFT JOIN `tabDonation Receipt` tdr
                        ON tp.name = tdr.patron AND tdr.docstatus = 1
                    GROUP BY tp.name
                    """,
        as_dict=1,
    ):
        frappe.db.set_value(
            "Patron",
            d["patron"],
            {
                "last_donation": d["last_donation"],
                "times_donated": d["times"],
                "total_donated": 0 if d["donation"] is None else d["donation"],
            },
            update_modified=False,
        )
    frappe.db.commit()


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


def clean_dhananjaya_data():
    ## Donor Names Cleaning
    frappe.db.sql(
        """
                    UPDATE `tabDonor`
                    SET 
                        first_name = TRIM(BOTH ' ' FROM REGEXP_REPLACE(first_name, ' {2,}', ' ')),
                        last_name = TRIM(BOTH ' ' FROM REGEXP_REPLACE(last_name, ' {2,}', ' ')),
                        full_name = TRIM(BOTH ' ' FROM REGEXP_REPLACE(full_name, ' {2,}', ' '))
                    WHERE 1
                    """
    )
    frappe.db.commit()
    # Patron Names Cleaning
    frappe.db.sql(
        """
                    UPDATE `tabPatron`
                    SET
                        first_name = TRIM(BOTH ' ' FROM REGEXP_REPLACE(first_name, ' {2,}', ' ')),
                        last_name = TRIM(BOTH ' ' FROM REGEXP_REPLACE(last_name, ' {2,}', ' ')),
                        full_name = TRIM(BOTH ' ' FROM REGEXP_REPLACE(full_name, ' {2,}', ' '))
                    WHERE 1
                    """
    )


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
        frappe.db.set_value(
            "Donation Receipt",
            r["receipt_id"],
            "realization_date",
            r["real_date"],
            update_modified=False,
        )
