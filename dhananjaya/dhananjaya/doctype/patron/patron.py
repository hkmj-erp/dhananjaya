# Copyright (c) 2023, Narahari Dasa and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class Patron(Document):
	def before_save(self):
		self.full_name = self.first_name + ( "" if not self.last_name else f" {self.last_name}")
		return


@frappe.whitelist()
def get_patron_status(patron):
	doc = frappe.get_doc("Patron",patron)
	donations = frappe.db.get_all("Donation Receipt",filters = {'docstatus':1,'patron':patron}, fields= ['amount'])
	total_donations = 0
	for d in donations:
		total_donations += d['amount']
	total_donations_fr = frappe.utils.fmt_money(total_donations,currency = "₹")
	commited_donation = frappe.utils.fmt_money(doc.committed_amount,currency = "₹")
	remaining = frappe.utils.fmt_money(doc.committed_amount - total_donations, currency = "₹")
	return total_donations_fr, commited_donation, remaining
