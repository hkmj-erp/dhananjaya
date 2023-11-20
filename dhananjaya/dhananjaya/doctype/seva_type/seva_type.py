# Copyright (c) 2023, Narahari Dasa and contributors
# For license information, please see license.txt

from dhananjaya.dhananjaya.doctype.dhananjaya_notifier.dhananjaya_notifier import (
    generate_version,
)
import frappe
from frappe.model.document import Document


class SevaType(Document):
    def autoname(self):
        self.name = get_abbreviated_name(self.seva_name, self.company)

    def before_rename(self, old, new, merge=False):
        # renaming consistency with abbreviation
        if not frappe.get_cached_value("Company", self.company, "abbr") in new:
            new = get_abbreviated_name(new, self.company)
        return new

    def on_change(self):
        generate_version(self.doctype)


def get_abbreviated_name(name, company):
    abbr = frappe.get_cached_value("Company", company, "abbr")
    new_name = "{0} - {1}".format(name, abbr)
    return new_name
