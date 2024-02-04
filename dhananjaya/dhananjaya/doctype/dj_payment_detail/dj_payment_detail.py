# Copyright (c) 2023, Narahari Dasa and contributors
# For license information, please see license.txt

import frappe
from dhananjaya.dhananjaya.doctype.dhananjaya_notifier.dhananjaya_notifier import (
    generate_version,
)
from frappe.model.document import Document


class DJPaymentDetail(Document):
    def on_change(self):
        generate_version(self.doctype)

    def on_update(self):
        self.delete_box_key()

    def on_trash(self):
        self.delete_box_key()

    def delete_box_key(self):
        frappe.cache().hdel("dhananjaya_box", "dj_payment_detail")


@frappe.whitelist()
def get_cached_documents():
    payment_details = (
        frappe.cache().hget("dhananjaya_box", "dj_payment_detail") or frappe._dict()
    )
    if not payment_details:
        payment_details = frappe.get_all("DJ Payment Detail", fields=["*"])
        frappe.cache().hset("dhananjaya_box", "dj_payment_detail", payment_details)
    return payment_details
