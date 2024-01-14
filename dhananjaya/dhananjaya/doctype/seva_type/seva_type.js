// Copyright (c) 2023, Narahari Dasa and contributors
// For license information, please see license.txt

frappe.ui.form.on('Seva Type', {
	refresh: function(frm) {
		frm.set_query('account',()=> {
			return {
				filters: {
					company:frm.doc.company,
					is_group : 0,
					root_type:"Income"
				}
			}
		});
		frm.set_query('csr_account',()=> {
			return {
				filters: {
					company:frm.doc.company,
					is_group : 0,
					root_type:"Income"
				}
			}
		});
	}
});	
