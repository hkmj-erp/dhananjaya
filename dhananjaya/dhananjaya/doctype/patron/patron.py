# Copyright (c) 2023, Narahari Dasa and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Patron(Document):
    def before_save(self):
        self.full_name = self.first_name + ("" if not self.last_name else f" {self.last_name}")
        return

    @property
    def total_donation(self):
        donations = frappe.db.get_all("Donation Receipt", filters={"docstatus": 1, "patron": self.name}, pluck="amount")
        return sum(donations)

    @property
    def total_credits_donation(self):
        donations = frappe.db.get_all("Donation Credit", filters={"patron": self.name}, pluck="amount")
        return sum(donations)

    @property
    def commitment(self):
        if self.seva_type is None:
            return 0
        return frappe.db.get_value("Patron Seva Type", self.seva_type, "seva_amount")


@frappe.whitelist()
def get_patron_status(patron):
    doc = frappe.get_doc("Patron", patron)
    return frappe._dict(completed=doc.total_donation, commited=doc.commitment)
