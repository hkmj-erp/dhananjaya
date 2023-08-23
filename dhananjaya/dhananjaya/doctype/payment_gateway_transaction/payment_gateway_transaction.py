# Copyright (c) 2023, Narahari Dasa and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class PaymentGatewayTransaction(Document):
	
	def on_update(self):
		docs = frappe.db.get_all("Donation Receipt",filters={'payment_gateway_document':self.name},pluck='name')
		for d in docs:
			doc = frappe.get_doc("Donation Receipt",d)
			doc.donor = self.donor
			doc.save()

	def on_trash(self):
		self.update_batch_details()

	def update_batch_details(self):
		batch_doc = frappe.get_doc("PG Upload Batch",self.batch)
		txs = frappe.db.get_all("Payment Gateway Transaction", filters={'batch':self.batch}, fields ={'name','amount','fee'})
		t_amount, t_fee = 0,0
		for tx in txs:
			t_amount += tx['amount']
			t_fee += tx['fee']
		batch_doc.total_amount = t_amount
		batch_doc.total_fee = t_fee
		batch_doc.final_amount = t_amount-t_fee
		batch_doc.save()