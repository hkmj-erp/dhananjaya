// Copyright (c) 2024, Narahari Dasa and contributors
// For license information, please see license.txt

frappe.query_reports["Patron Commitment Status"] = {
  filters: [
    {
      fieldname: "level",
      label: __("Patron Level"),
      fieldtype: "Link",
      options: "Patron Seva Type",
      width: 100,
    },
    {
      fieldname: "from_date",
      label: __("From Date"),
      fieldtype: "Date",
      width: 100,
      reqd: 1,
    },
    {
      fieldname: "to_date",
      label: __("To Date"),
      fieldtype: "Date",
      width: 100,
      reqd: 1,
    },
    {
      fieldname: "include_credits",
      label: __("Include Credits"),
      fieldtype: "Check",
      default: 1,
      width: 100,
      // on_change: function () {
      //   // frappe.query_report.set_filter_value("summary", 1);
      //   // frappe.query_report.refresh();
      // },
    },
    {
      fieldname: "summary",
      label: __("Show Summary"),
      fieldtype: "Check",
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
  ],
};
