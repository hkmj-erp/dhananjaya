# Copyright (c) 2023, Narahari Dasa and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

PREACHER_ROLE = "DCC Preacher"


class LLPPreacher(Document):
    def on_update(self):
        frappe.errprint("Preacher Updated2")
        for user_row in self.allowed_users:
            if PREACHER_ROLE not in frappe.get_roles(user_row.user):
                user = frappe.get_doc("User", user_row.user)
                user.add_roles([PREACHER_ROLE])
