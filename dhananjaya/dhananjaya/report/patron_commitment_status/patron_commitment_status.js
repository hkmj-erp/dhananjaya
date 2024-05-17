// Copyright (c) 2024, Narahari Dasa and contributors
// For license information, please see license.txt

frappe.query_reports["Patron Commitment Status"] = {
	"filters": [
		{
			fieldname: "level",
			label: __("Patron Level"),
			fieldtype: "Link",
			options: "Patron Seva Type",
			width: 100,
		  },
		//   {
		// 	fieldname: "last_month",
		// 	fieldtype: "Select",
		// 	label: "Last Month",
		// 	options: 
		// 	default:,
		// 	reqd: 1
		//    },
	]
};
