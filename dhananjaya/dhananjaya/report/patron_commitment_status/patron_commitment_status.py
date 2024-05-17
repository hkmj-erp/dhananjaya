# Copyright (c) 2024, Narahari Dasa and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import add_to_date
from datetime import datetime
from dhananjaya.dhananjaya.utils import get_credit_values


def execute(filters=None):
    conditions = get_conditions(filters)
    patron_map = {
        p["id"]: {**p, "total_donated": 0, "last_month_donated": 0}
        for p in frappe.db.sql(
            f"""
						SELECT tp.name as id,
								tp.full_name,
								llp_preacher,
								committed_amount,
								seva_type,
								GROUP_CONCAT(tpdn.full_name ORDER BY tpdn.idx SEPARATOR '\n') as display_names
						FROM `tabPatron` tp
						LEFT JOIN `tabPatron Display Name` tpdn
							ON tp.name = tpdn.parent
						WHERE 1 {conditions}
						GROUP BY tp.name
						""",
            as_dict=1,
        )
    }

    ## Total Donated
    for p in frappe.db.sql(
        f"""
							select 
								tp.name as id,
								SUM(tdr.amount) as total_donated
							from `tabPatron` tp
							left join `tabDonation Receipt` tdr
								on tp.name = tdr.patron
							where 1 {conditions}
							AND tdr.docstatus = 1
							group by tp.name
							""",
        as_dict=1,
    ):
        patron_map[p["id"]]["total_donated"] = p["total_donated"]

    ## Last Month Donated
    for p in frappe.db.sql(
        f"""
							select 
								tp.name as id,
								SUM(tdr.amount) as last_month_donated
							from `tabPatron` tp
							join `tabDonation Receipt` tdr
								on tp.name = tdr.patron
							where 1 {conditions}
							AND tdr.receipt_date 
								BETWEEN
									DATE_FORMAT(DATE_SUB(CURDATE(), INTERVAL 1 MONTH), '%Y-%m-01') 
										AND 
									LAST_DAY(DATE_SUB(CURDATE(), INTERVAL 1 MONTH)) 
							AND tdr.docstatus = 1
							group by tp.name
							""",
        as_dict=1,
    ):
        patron_map[p["id"]]["last_month_donated"] = p["last_month_donated"]

    ## Total Credits
    credits = frappe.db.get_all(
        "Donation Credit",
        fields=["company", "patron", "credits", "posting_date"],
        filters={"patron": ("is", "set")},
    )
    unique_companies = list(set([c["company"] for c in credits]))
    credit_values_map = get_credit_values(unique_companies)

    last_month_date = add_to_date(datetime.now(), months=-1)
    last_month_m = last_month_date.month
    last_month_y = last_month_date.year
    frappe.errprint(patron_map)
    for c in credits:
        eqv_amount = credit_values_map[c["company"]] * c["credits"]
        if (
            c["posting_date"].month == last_month_m
            and c["posting_date"].year == last_month_y
        ):
            patron_map[c["patron"]]["last_month_donated"] += eqv_amount
        patron_map[c["patron"]]["total_donated"] += eqv_amount

    for d in patron_map.values():
        d["remaining_amount"] = d["committed_amount"] - d["total_donated"]
    data = list(patron_map.values())
    data = sorted(data, key=lambda x: (-x["committed_amount"], x["seva_type"]))

    return get_columns(), data


def get_conditions(filters: dict) -> str:
    conditions = ""
    if filters.get("level"):
        conditions += f""" AND tp.seva_type = '{filters.get("level")}'"""
    return conditions


def get_columns():
    columns = [
        {
            "fieldname": "id",
            "label": "Patron ID",
            "fieldtype": "Data",
            "width": 140,
        },
        {
            "fieldname": "full_name",
            "label": "Full Name",
            "fieldtype": "Data",
            "width": 200,
        },
        {
            "fieldname": "display_names",
            "label": "Display Names",
            "fieldtype": "Data",
            "width": 200,
        },
        {
            "fieldname": "seva_type",
            "label": "Level",
            "fieldtype": "Data",
            "width": 150,
        },
        {
            "fieldname": "committed_amount",
            "label": "Commitment",
            "fieldtype": "Currency",
            "width": 160,
        },
        {
            "fieldname": "total_donated",
            "label": "Total Donated",
            "fieldtype": "Currency",
            "width": 160,
        },
        {
            "fieldname": "remaining_amount",
            "label": "Remaining Amount",
            "fieldtype": "Currency",
            "width": 160,
        },
        {
            "fieldname": "last_month_donated",
            "label": "Last Month Donated",
            "fieldtype": "Currency",
            "width": 160,
        },
    ]
    return columns
