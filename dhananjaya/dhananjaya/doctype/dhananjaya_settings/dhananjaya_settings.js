// Copyright (c) 2023, Narahari Dasa and contributors
// For license information, please see license.txt

frappe.ui.form.on('Dhananjaya Settings', {
	refresh: function(frm) {
		frm.set_query('donation_account', 'defaults', (doc,cdt,cdn) => {
			var d = locals[cdt][cdn];
			return {
				filters: {
					company: d.company,
					root_type: "Income",
					is_group: 0
				}
			}
		});
		frm.set_query('cash_account', 'defaults', (doc,cdt,cdn) => {
			var d = locals[cdt][cdn];
			return {
				filters: {
					company: d.company,
					account_type: "Cash",
					is_group: 0
				}
			}
		}); 
		frm.set_query('gateway_expense_account', 'defaults', (doc,cdt,cdn) => {
			var d = locals[cdt][cdn];
			return {
				filters: {
					company: d.company,
					root_type: "Expense",
					is_group: 0
				}
			}
		});
		frm.set_query('default_cost_center', 'defaults', (doc,cdt,cdn) => {
			var d = locals[cdt][cdn];
			return {
				filters: {
					company: d.company
				}
			}
		});
	},
	upload_gateway:function(frm){
		frappe.call({
			freeze:true,
			freeze_message:"Uploading Trasactions.",
			method: "dhananjaya.dhananjaya.doctype.dhananjaya_settings.dhananjaya_settings.upload_gateway_transactions",
			callback: function(r) {
				if(!r.exc){
					frappe.msgprint("Uploaded. Please Check Once.");
				}
			}
		});
	}
});
