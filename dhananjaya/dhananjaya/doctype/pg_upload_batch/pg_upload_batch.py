# Copyright (c) 2023, Narahari Dasa and contributors
# For license information, please see license.txt

import json
from dhananjaya.dhananjaya.utils import get_company_defaults
import frappe
from frappe.model.document import Document
from rapidfuzz import process, fuzz


class PGUploadBatch(Document):
    def before_insert(self):
        # set default donation account
        company_detail = get_company_defaults(self.company)
        self.gateway_expense_account = company_detail.gateway_expense_account


@frappe.whitelist()
def count_donor_linked(batch):
    txs = frappe.db.get_all(
        "Payment Gateway Transaction",
        filters={"batch": batch, "receipt_created": 0},
        pluck=("donor"),
    )
    linked, total = 0, 0

    for tx in txs:
        if tx:
            linked += 1
        total += 1
    return linked, total


@frappe.whitelist()
def get_payment_entries(batch):
    txs = frappe.db.get_all(
        "Payment Gateway Transaction", filters={"batch": batch}, pluck="name"
    )
    return txs


@frappe.whitelist()
def set_seva_type_bulk(batch, seva_type):
    frappe.db.sql(
        f"""
					update `tabPayment Gateway Transaction`
					set seva_type = '{seva_type}'
					where batch = '{batch}' AND receipt_created = 0
					"""
    )
    frappe.db.commit()
