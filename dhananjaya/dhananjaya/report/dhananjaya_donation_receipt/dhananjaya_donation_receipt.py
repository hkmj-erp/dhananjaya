# Copyright (c) 2023, Narahari Dasa and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):

	conditions = get_conditions(filters)
	receipts = {}
	for i in frappe.db.sql(f"""
					select *
					from `tabDonation Receipt` tdr
					where docstatus = 1 {conditions}
					order by receipt_date
					""",as_dict=1):
		receipts.setdefault(i['name'],i)
	
	donors = {}

	if len(receipts.keys()) > 0:
		for i in frappe.db.sql(f"""
					select td.name as donor_id,
					GROUP_CONCAT(DISTINCT tda.address_line_1,tda.address_line_2,tda.city SEPARATOR' | ') as address,
					GROUP_CONCAT(DISTINCT tdc.contact_no SEPARATOR' , ') as contact
					from `tabDonor` td
					left join `tabDonor Contact` tdc on tdc.parent = td.name
					left join `tabDonor Address` tda on tda.parent = td.name
					where td.name IN ({",".join([f"'{receipt['donor']}'" for receipt in receipts.values()])})
					group by td.name
					""",as_dict=1):
			donors.setdefault(i['donor_id'],i)
	
		for r in receipts:
			if receipts[r]['donor'] is not None and receipts[r]['donor'] != "":
				receipts[r]['contact'] = donors[receipts[r]['donor']]['contact']
				receipts[r]['address'] = donors[receipts[r]['donor']]['address']
	
	# data = list(receipts.values())
	
	# data = receipts
	columns = get_columns(filters)

	data = list(receipts.values())
	data.sort(key=lambda x: (x['company'],x['receipt_date']), reverse=True)

	# columns, data = [], []
	return columns, data


def get_conditions(filters):
	conditions = ""
	conditions += f' AND tdr.receipt_date BETWEEN "{filters.get("from_date")}" AND "{filters.get("to_date")}"'
	
	if filters.get("company"):
		conditions += f' AND tdr.company = {filters.get("company")}'
	
	if filters.get("preacher"):
		conditions += f' AND tdr.preacher = "{filters.get("preacher")}"'

	if filters.get("donor"):
		conditions += f' AND tdr.donor = "{filters.get("donor")}"'

	if filters.get("seva_type"):
		conditions += f' AND tdr.seva_type = "{filters.get("seva_type")}"'

	if filters.get("seva_subtype"):
		conditions += f' AND tdr.seva_subtype = "{filters.get("seva_subtype")}"'

	return conditions



def get_columns(filters):
	columns =[
		{
			"fieldname": "name",
			"label": "ID",
			"fieldtype": "Link",
			"options":"Donation Receipt",
			"width": 120
		},
		{
			"fieldname": "receipt_date",
			"label": "Receipt Date",
			"fieldtype": "Date",
			"width":100
		},
		{
			"fieldname": "company_abbreviation",
			"label": "Company",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "donor",
			"label": "Donor",
			"fieldtype": "Link",
			"options":"Donor",
			"width":120
		},
		{
			"fieldname": "full_name",
			"label": "Full Name",
			"fieldtype": "Data",
			"width":200
		},
		{
			"fieldname": "preacher",
			"label": "Preacher",
			"fieldtype": "Data",
			"width":80 
		},
		{
			"fieldname": "amount",
			"label": "Amount",
			"fieldtype": "Currency",
			"width":120 
		},
		{
			"fieldname": "seva_type",
			"label": "Seva Type",
			"fieldtype": "Data",
			"width":150
		},
		# {
		# 	"fieldname": "kyc",
		# 	"label": "KYC",
		# 	"fieldtype": "Data",
		# 	"width": 200,
		# },
		{
			"fieldname": "contact",
			"label": "Donor Contact",
			"fieldtype": "Data",
			"width": 200,
		},
		{
			"fieldname": "address",
			"label": "Donor Address",
			"fieldtype": "Data",
			"width":500
		},
		
	]
	return columns