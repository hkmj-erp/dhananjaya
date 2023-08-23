frappe.ui.form.on("Bank Transaction", {
  onload(frm) {
    frm.add_custom_button(__("Create Journal Entry"), function () {
      // journal_entry_dict = {
      //     "voucher_type": entry_type,
      //     "company": company,
      //     "posting_date": posting_date,
      //     "cheque_date": reference_date,
      //     "cheque_no": reference_number,
      //     "mode_of_payment": mode_of_payment,
      // }
      // frappe.model.open_mapped_doc({
      //     method: "hkm.erpnext___custom.doctype.item_creation_request.item_creation_request.create_item",
      //     frm: frm
      // });
      frappe.call({
        method:
          "dhananjaya.dhananjaya.statement_utils.get_journal_entry_from_statement",
        args: {
          statement: frm.doc.name,
        },
        callback: (r) => {
          var doc = frappe.model.sync(r.message);
          frappe.set_route("Form", doc[0].doctype, doc[0].name);
        },
      });
    });
    frm.add_custom_button(__("Create Donation Receipt"), function () {
      frappe.call({
        method:
          "dhananjaya.dhananjaya.statement_utils.get_donation_receipt_from_statement",
        args: {
          statement: frm.doc.name,
        },
        callback: (r) => {
          var doc = frappe.model.sync(r.message);
          frappe.set_route("Form", doc[0].doctype, doc[0].name);
        },
      });
    });
  },
});
