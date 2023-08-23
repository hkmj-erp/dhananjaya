// Copyright (c) 2023, Narahari Dasa and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Cashier Report"] = {
	"filters": [
			{
			"fieldname": "company",
			"fieldtype": "Link",
			"label": "Company",
			"reqd": 1,
			"options": "Company",
		   },
		   {
			"fieldname": "from_date",
			"fieldtype": "Datetime",
			"label": "From Date",
			"reqd": 1,
		   },
		   {
			"fieldname": "to_date",
			"fieldtype": "Datetime",
			"label": "To Date",
			"reqd": 1,
		   },
		   {
			"fieldname": "payment_method",
			"fieldtype": "Select",
			"label": "Payment Mode",
			"options": ["Cash","Cheque"],
			"default":"Cash"
		   }
	]
};
