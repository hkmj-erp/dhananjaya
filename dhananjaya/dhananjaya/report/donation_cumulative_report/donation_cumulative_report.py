# Copyright (c) 2023, Narahari Dasa and contributors
# For license information, please see license.txt

import frappe
from dhananjaya.dhananjaya.utils import get_credits_equivalent, get_donation_companies


def execute(filters=None):
    companies = get_donation_companies()

    columns = get_columns(companies)
    conditions = get_conditions(filters)

    donations = []

    for p in frappe.get_all("LLP Preacher", filters={"include_in_analysis": 1}, pluck="name"):
        donation_row = {"preacher": p}
        for c in companies:
            donation_row.setdefault(c, 0)
        # donation_row.extend([0]*len(com))

        ### Regular Donations
        preacher_total_donation = 0
        for i in frappe.db.sql(
            f"""
                            select company, SUM(amount) as total
                            from `tabDonation Receipt` tdr
                            where tdr.preacher = '{p}'
                            {conditions}
                            group by tdr.company
                            """,
            as_dict=1,
        ):
            donation_row[i["company"]] = i["total"]
            preacher_total_donation += i["total"]

        ### Credit Donations
        for i in frappe.db.sql(
            f"""
                            select company, SUM(credits) as credits
                            from `tabDonation Credit` tdc
                            where tdc.preacher = '{p}'
                            AND posting_date BETWEEN "{filters.get("from_date")}" AND "{filters.get("to_date")}"
                            group by tdc.company
                            """,
            as_dict=1,
        ):
            credits_amount = get_credits_equivalent(i["company"], i["credits"])
            donation_row[i["company"]] += credits_amount  ## Add this to regular
            preacher_total_donation += credits_amount

        donation_row.setdefault("total_preacher", preacher_total_donation)

        if preacher_total_donation > 0:
            donations.append(donation_row)

    data = donations

    data = sorted(data, key=lambda x: x["total_preacher"], reverse=True)

    return columns, data


def get_conditions(filters):
    conditions = ""
    if filters.get("based_on") == "Receipt Date":
        conditions += f' AND tdr.receipt_date BETWEEN "{filters.get("from_date")}" AND "{filters.get("to_date")}"'
    else:
        conditions += f' AND tdr.realization_date BETWEEN "{filters.get("from_date")}" AND "{filters.get("to_date")}"'

    seva_types = frappe.get_all(
        "Seva Type",
        filters={
            "include_in_analysis": 1,
        },
        pluck="name",
    )
    seva_subtypes = frappe.get_all(
        "Seva Subtype",
        filters={"include_in_analysis": 1, "is_group": 0},
        pluck="name",
    )
    # preachers = frappe.get_all("LLP Preacher", filters=[["include_in_analysis", "=", 1]], pluck="name")

    seva_types_str = ",".join([f"'{s}'" for s in seva_types])
    seva_subtypes_str = ",".join([f"'{s}'" for s in seva_subtypes])
    # preachers_str = ",".join([f"'{p}'" for p in preachers])

    conditions += f" AND seva_type IN ({seva_types_str}) "
    conditions += f" AND seva_subtype IN ({seva_subtypes_str}) "
    if filters.get("only_realized"):
        conditions += f" AND docstatus = 1 "

    return conditions


def get_columns(companies):
    columns = [
        {
            "fieldname": "preacher",
            "label": "Preacher",
            "fieldtype": "Link",
            "options": "LLP Preacher",
            "width": 120,
        }
    ]
    for c in companies:
        columns.append(
            {
                "fieldname": c,
                "label": c,
                "fieldtype": "Currency",
                "width": 120,
            }
        )
    columns.append(
        {
            "fieldname": "total_preacher",
            "label": "Total",
            "fieldtype": "Currency",
            "width": 120,
        }
    )
    return columns
