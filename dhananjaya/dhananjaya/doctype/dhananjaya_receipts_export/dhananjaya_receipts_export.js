// Copyright (c) 2023, Narahari Dasa and contributors
// For license information, please see license.txt

frappe.ui.form.on('Dhananjaya Receipts Export', {
	refresh: function(frm) {
		frm.add_custom_button(__('Prepare Zip'), function(){
			frappe.warn('Are you sure you want to proceed?',
			'This action will take sometime. If you already have requested, please wait for that to complete.',
			() => {
				frappe.call({
					method: 'dhananjaya.dhananjaya.doctype.dhananjaya_receipts_export.dhananjaya_receipts_export.generate_receipts',
					callback: function(r) {
						if (!r.exc) {
							frappe.msgprint("Queued. You will receive an email on completion.")
						}
					}
				});
			}, () => {});
			
		},);
	}
});
