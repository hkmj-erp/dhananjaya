# Copyright (c) 2023, Narahari Dasa and contributors
# For license information, please see license.txt

import json
import frappe


def execute(filters=None):

	
	conditions = get_conditions(filters)

	receipts = frappe.db.sql(f"""
					select DATE_FORMAT(tv.creation, "%%a, %%D %%b,%%y | %%I:%%i %%p") as date,tv.data,tv.owner as cashier, 
					tdr.receipt_date,
					tdr.name as donation_receipt, tdr.old_dr_no,
							tdr.preacher, tdr.full_name as donor_name, tdr.cheque_number, tdr.amount
					from `tabDonation Receipt` tdr
					join `tabVersion` tv
						on tv.docname = tdr.name
					where 1 {conditions}
					order by tv.creation
					""",values = filters, as_dict = 1)
	final_data = []
	for r in receipts:
		data = json.loads(r['data'])
		
		changed = data['changed']
		for ch in changed:
			if (
				filters['payment_method'] == 'Cash' 
				and ch[0] == 'workflow_state' 
				and ch[1] == 'Acknowledged' 
				and ch[2] == 'Received by Cashier'):
				final_data.append(r)
				break
			elif (
				filters['payment_method'] == 'Cheque' 
				and ch[0] == 'workflow_state' 
				and ch[1] == 'Acknowledged' 
				and ch[2] == 'Cheque Collected'):
				final_data.append(r)
				break

	columns = get_columns()
	# columns, data = [], []
	return columns, final_data

def get_conditions(filters):
	conditions = ""

	conditions += " and tdr.company = %(company)s"

	if filters['payment_method'] == 'Cash':
		conditions += " and tdr.docstatus = 1"
	elif filters['payment_method'] == 'Cheque':
		conditions += " and tdr.docstatus = 0"
	
	conditions += " and tdr.payment_method =  %(payment_method)s"
	# if filters['payment_method'] == 'Cash':
		# pass
		# conditions += ' and tv.data LIKE \'%%\"workflow_state\",\"Acknowledged\",\"Received by Cashier\"%%\' '
	# elif filters['payment_method'] == 'Cheque':
	# 	conditions += ' and tv.data LIKE \'%%\"workflow_state\"\,\"Acknowledged\"\,\"Cheque Collected\"%%\' '
	
	conditions += " and tv.creation between %(from_date)s and %(to_date)s"

	
	return conditions

def get_columns():
	columns = [
				{
				"fieldname": "date",
				"fieldtype": "Data",
				"label": "Cashier Date & Time",
				"width": 200
				},
				{
				"fieldname": "receipt_date",
				"fieldtype": "Date",
				"label": "Receipt Date",
				"width": 150
				},
				{
				"fieldname": "preacher",
				"fieldtype": "Data",
				"label": "Preacher",
				"width": 150
				},
				{
				"fieldname": "donation_receipt",
				"fieldtype": "Link",
				"label": "Donation Receipt",
				"options": "Donation Receipt",
				"width": 200
				},
				{
				"fieldname": "donor_name",
				"fieldtype": "Data",
				"label": "Donor Name",
				"width": 200
				},
				{
				"fieldname": "amount",
				"fieldtype": "Currency",
				"label": "Amount",
				"width": 100
				},
				{
				"fieldname": "cheque_number",
				"fieldtype": "Data",
				"label": "Cheque No",
				"width": 100
				},
				{
				"fieldname": "old_dr_no",
				"fieldtype": "Data",
				"label": "Old DR ID",
				"width": 100
				},
				{
				"fieldname": "cashier",
				"fieldtype": "Data",
				"label": "Cashier",
				"width": 200
				}
				]
	return columns
