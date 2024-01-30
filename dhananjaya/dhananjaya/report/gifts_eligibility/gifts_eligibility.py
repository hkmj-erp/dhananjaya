# Copyright (c) 2024, Narahari Dasa and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
    if not filters:
        filters = {}

    columns = get_columns(filters)

    # if filters.get
    gifts_map = {}
    for g in frappe.get_all("Patron Gift", fields=["name", "threshold_amount"]):
        gifts_map.setdefault(g["name"], g["threshold_amount"])

    issued = []
    for issue in frappe.db.sql(
        """
				select tp.name as patron,tpgi.gift
				from `tabPatron` tp
				join `tabPatron Gift Issue` tpgi
				on tp.name = tpgi.parent
				where 1
					"""
    ):
        issued.append(issue)

    eligibles = []
    for eligible in frappe.db.sql(
        """
			select tp.name as patron,tp.llp_preacher,tp.full_name,tpg.name as gift
			from `tabPatron` tp
			join `tabPatron Gift` tpg
			on tp.total_donated >= tpg.threshold_amount
			where 1
				""",
        as_dict=1,
    ):
        if not (eligible["patron"], eligible["gift"]) in issued:
            eligibles.append(eligible)

    data = eligibles

    return columns, data


def get_columns(filters):
    columns = [
        {
            "fieldname": "patron",
            "label": "Patron ID",
            "fieldtype": "Link",
            "options": "Patron",
            "width": 140,
        },
        {
            "fieldname": "full_name",
            "label": "Patron Name",
            "fieldtype": "Data",
            "options": "Donor",
            "width": 300,
        },
        {
            "fieldname": "llp_preacher",
            "label": "Preacher",
            "fieldtype": "Data",
            "width": 140,
        },
        {
            "fieldname": "gift",
            "label": "Gift",
            "fieldtype": "Data",
            "width": 140,
        },
    ]
    return columns
