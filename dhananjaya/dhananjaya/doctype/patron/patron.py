# Copyright (c) 2023, Narahari Dasa and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils.data import cint

from dhananjaya.dhananjaya.utils import (
    get_credit_values,
    get_credits_equivalent,
    sanitise_str,
)


class Patron(Document):
    def validate(self):
        self.validate_display_names()
        self.validate_commitment_amount()

    def validate_display_names(self):
        allowed = frappe.get_value(
            "Dhananjaya Settings", "Dhananjaya Settings", "display_names_allowed"
        )
        if len(self.display_names) > cint(allowed):
            frappe.throw(f"Only {allowed} names are allowed.")

    def validate_commitment_amount(self):
        seva_amount = frappe.db.get_value(
            "Patron Seva Type", self.seva_type, "seva_amount"
        )
        if self.committed_amount < seva_amount:
            frappe.throw(
                "Commitment Amount of Patron can not be less than Seva Amount defined in Patronship Level."
            )
        return

    def before_save(self):
        # Preacher Change
        if (
            not self.is_new()
            and self.has_value_changed("llp_preacher")
            and "DCC Manager" not in frappe.get_roles()
        ):
            frappe.throw(
                "Only DCC Manager is allowed to change the Preacher of a Donor."
            )

        ####
        self.first_name = sanitise_str(self.first_name)
        self.full_name = self.first_name
        if self.last_name is not None:
            self.last_name = sanitise_str(self.last_name)
            self.full_name += " " + self.last_name
        return

    @property
    def total_donation(self):
        donations = frappe.db.get_all(
            "Donation Receipt",
            filters={"docstatus": 1, "patron": self.name},
            pluck="amount",
        )
        return sum(donations)

    @property
    def total_credits_donation(self):
        total_donation = 0
        credits = frappe.db.get_all(
            "Donation Credit",
            filters={"patron": self.name},
            fields=["company", "credits"],
        )
        unique_companies = list(set([c["company"] for c in credits]))
        credit_values_map = get_credit_values(unique_companies)
        for credit_doc in credits:
            total_donation += (
                credit_values_map[credit_doc["company"]] * credit_doc["credits"]
            )
        return total_donation

    @property
    def commitment(self):
        if self.seva_type is None:
            return 0
        return frappe.db.get_value("Patron Seva Type", self.seva_type, "seva_amount")


@frappe.whitelist()
def get_patron_status(patron):
    doc = frappe.get_doc("Patron", patron)
    credits = doc.total_credits_donation
    return frappe._dict(
        completed=doc.total_donation + credits, commited=doc.commitment, credits=credits
    )
