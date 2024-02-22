# Copyright (c) 2023, Narahari Dasa and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class DJReminder(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF

        donor: DF.Link | None
        donor_name: DF.Data | None
        message: DF.Text
        remind_at: DF.Datetime
        user: DF.Link
    # end: auto-generated types
    pass
