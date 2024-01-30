# Copyright (c) 2023, Narahari Dasa and contributors
# For license information, please see license.txt

# import frappe
from dhananjaya.dhananjaya.doctype.dhananjaya_notifier.dhananjaya_notifier import (
    generate_version,
)
from frappe.utils.nestedset import NestedSet

# from frappe.model.document import Document


class SevaSubtype(NestedSet):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF

        amount: DF.Currency
        enabled: DF.Check
        include_in_analysis: DF.Check
        is_group: DF.Check
        lft: DF.Int
        old_parent: DF.Link | None
        parent_seva_subtype: DF.Link | None
        patronship_allowed: DF.Check
        rgt: DF.Int
        seva_name: DF.Data
    # end: auto-generated types
    nsm_parent_field = "parent_seva_subtype"

    def on_change(self):
        generate_version(self.doctype)
