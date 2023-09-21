// Copyright (c) 2023, Narahari Dasa and contributors
// For license information, please see license.txt

frappe.ui.form.on('Donation Receipt', {
	refresh: function(frm) {
		frm.set_query('payment_gateway_document',()=> {
			return {
				filters: {
					company : frm.doc.company,
					receipt_created : 0,
					amount : frm.doc.amount
				}
			}
		});
		frm.set_query('seva_type',()=> {
			return {
				filters: {
					company : frm.doc.company,
					enabled : 1
				}
			}
		});
		frm.set_query('seva_subtype',()=> {
			return {
				filters: {
					enabled : 1,
					is_group : 0
				}
			}
		});
		frm.set_query('bank_transaction', () => {
			return {
				filters: {
					status: 'Unreconciled',
					deposit:frm.doc.amount,
					bank_account : frm.doc.bank_account
					// date: ['>=',frm.doc.receipt_date]
				}
			}
		});
		frm.set_query('bounce_transaction', () => {
			return {
				filters: {
					status: 'Unreconciled',
					withdrawal:frm.doc.amount,
					bank_account : frm.doc.bank_account
					// date: ['>=',frm.doc.receipt_date]
				}
			}
		});
		frm.set_query('donation_account', () => {
			return {
				filters: {
					company: frm.doc.company,
					is_group: 0
				}
			}
		});
		frm.set_query('donor', () => {
			return {
				query: "dhananjaya.dhananjaya.doctype.donation_receipt.donation_receipt.get_donor",
				filters: {
					// 'account': row.account
				}
			}
		});
		frm.set_query('cash_account', () => {
			return {
				filters: {
					company: frm.doc.company,
					account_type: "Cash",
					is_group: 0
				}
			}
		}); 
		frm.set_query('gateway_expense_account',() => {
			return {
				filters: {
					company: frm.doc.company,
					root_type: "Expense",
					is_group: 0
				}
			}
		});
		frm.add_custom_button(__('Create Benefit'), function(){
			frappe.call({
				freeze: true,
				method:
				  "dhananjaya.dhananjaya.doctype.donation_receipt.operations.get_festival_benefit",
				args: {
				  request: frm.doc.name,
				},
				callback: function (r) {
				  if (!r.exc) {
					var doc = frappe.model.sync(r.message);
					frappe.set_route("Form", doc[0].doctype, doc[0].name);
				  }
				},
			  });
			
		}, "Operations");
		if(frm.doc.docstatus == 1){
			frm.add_custom_button(__('Cancel'), function(){
				frappe.warn('Are you sure you want to proceed?',
				'This action will consequently cancel the Journal Entry and unreconcile the Bank Statement.',
				() => {
					frappe.call({
						freeze:true,
						freeze_message:"Cancelling Linked Documents",
						method: "dhananjaya.dhananjaya.doctype.donation_receipt.donation_receipt.receipt_cancel_operations",
						args:{
							receipt : frm.doc.name
						},
						callback: function(r) {
							if(!r.exc){
								frappe.msgprint("Successfully Cancelled.");
							}
						}
					});
				}, () => {
					
				});
				
			},"Operations");
			if(frm.doc.bounce_transaction){
				frm.add_custom_button(__('Bounce'), function(){
					frappe.warn('Are you sure you want to proceed to bounce this Cheque Donation?',
					'This action will consequently create a bounced Journal Entry and reconcile the Bank Statement as well.',
					() => {
						frappe.call({
							freeze:true,
							freeze_message:"Bouncing Cheque Donation",
							method: "dhananjaya.dhananjaya.doctype.donation_receipt.donation_receipt.receipt_bounce_operations",
							args:{
								receipt : frm.doc.name
							},
							callback: function(r) {
								if(!r.exc){
									frappe.msgprint("Successfully Bounced.");
								}
							}
						});
					}, () => {
						
					});
					
				}, "Operations");
			}
		}
		
		frm.add_custom_button(__('Send Receipt/Acknowledgement'), function(){
			frappe.call({
				freeze:true,
				freeze_message:"Sending...",
				method: "dhananjaya.dhananjaya.doctype.donation_receipt.donation_receipt.send_receipt",
				args:{
					dr : frm.doc.name
				},
				callback: function(r) {
					if(!r.exc){
						frappe.msgprint("Successfully Sent.");
					}
				}
			});
		},"Operations");

		frm.add_custom_button(__('PDF'), function(){
			let print_format = '80G Receipt';
			window.open(`/api/method/dhananjaya.dhananjaya.utils.download_pdf?doctype=Donation Receipt&name=${frm.doc.name}&format=${print_format}`);
		});


		
	},
	bank_transaction:function(frm){
		if(!frm.doc.bank_account){
			frappe.msgprint("Please select first the Bank Account for transactions.");
			frm.set_value('bank_transaction', null);
		}
	},
	payment_gateway_document:async function(frm){
		if(frm.doc.payment_gateway_document){
			var gateway_doc = await frappe.db.get_doc("Payment Gateway Transaction",frm.doc.payment_gateway_document);
			frm.set_value('additional_charges',gateway_doc.fee);
			console.log(gateway_doc);
			var bank_account_doc = await frappe.db.get_doc("PG Upload Batch", gateway_doc.batch);
			frm.set_value('bank_account', bank_account_doc.bank_account);
			frm.set_value('bank_transaction', bank_account_doc.bank_transaction);
			frm.set_value('gateway_expense_account', bank_account_doc.gateway_expense_account);
			frm.save();
		}else{
			frm.set_value('additional_charges',0);
			frm.set_value('bank_account', null);
			frm.set_value('bank_transaction', null);
			frm.save();
		}
	}
});
