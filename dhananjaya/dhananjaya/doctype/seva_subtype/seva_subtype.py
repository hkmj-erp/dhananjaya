# Copyright (c) 2023, Narahari Dasa and contributors
# For license information, please see license.txt

# import frappe
from dhananjaya.dhananjaya.doctype.dhananjaya_notifier.dhananjaya_notifier import (
    generate_version,
)
from frappe.utils.nestedset import NestedSet

# from frappe.model.document import Document


class SevaSubtype(NestedSet):
    nsm_parent_field = "parent_seva_subtype"

    def on_change(self):
        generate_version(self.doctype)
