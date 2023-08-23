// Copyright (c) 2023, Narahari Dasa and contributors
// For license information, please see license.txt

frappe.ui.form.on("PG Upload Batch", {
  before_load: function (frm) {
    frm.events.recalculate_amounts(frm);
  },
  onload: function (frm) {
    frm.events.set_finalview(frm);
  },
  refresh: function (frm) {
    frm.set_query("gateway_expense_account", () => {
      return {
        filters: {
          company: frm.doc.company,
          root_type: "Expense",
          is_group: 0,
        },
      };
    });
    frm.set_query("bank_transaction", () => {
      return {
        filters: {
          status: "Unreconciled",
          deposit: frm.doc.final_amount,
          bank_account: frm.doc.bank_account,
          // date: ['>=',frm.doc.receipt_date]
        },
      };
    });
    frm.add_custom_button(__("Set Seva Type (BULK)"), function () {
      frappe.prompt(
        {
          label: "Seva Type",
          fieldname: "seva_type",
          fieldtype: "Link",
          options: "Seva Type",
        },
        (values) => {
          // console.log(values.seva_type);
          frappe.call({
            freeze: true,
            freeze_message: "Processing...",
            method:
              "dhananjaya.dhananjaya.doctype.pg_upload_batch.pg_upload_batch.set_seva_type_bulk",
            args: {
              batch: frm.doc.name,
              seva_type: values.seva_type,
            },
            callback: function (r) {
              if (!r.exc) {
                frappe.show_alert(
                  "Successfully set Seva Type in all connected payments",
                  5
                );
              }
            },
          });
        }
      );
    });
    frm.add_custom_button(__("Process Batch Payments"), function () {
      frappe.warn(
        "Are you sure you want to proceed?",
        "This will generate following:<br><br>1. Donation Entries<br>2. Journal Entries<br>3. Bank Reconcillation",
        () => {
          frappe.call({
            freeze: true,
            freeze_message: "Processing...",
            method:
              "dhananjaya.dhananjaya.doctype.donation_receipt.donation_receipt.process_batch_gateway_payments",
            args: {
              batch: frm.doc.name,
            },
            callback: function (r) {
              if (!r.exc) {
                frappe.msgprint("Successfully Created.");
              }
            },
          });
        },
        "Continue",
        true // Sets dialog as minimizable
      );
    });
    frm.add_custom_button(__("Generated Donation Receipts"), function () {
      frappe.call({
        method:
          "dhananjaya.dhananjaya.doctype.pg_upload_batch.pg_upload_batch.get_payment_entries",
        args: {
          batch: frm.doc.name,
        },
        callback: function (r) {
          if (!r.exc) {
            console.log(r.message);
            frappe.set_route("List", "Donation Receipt", {
              payment_gateway_document: ["in", r.message],
            });
          }
        },
      });
    });
    frm.add_custom_button(
      __("Try Razorpay Pattern"),
      function () {
        frappe.call({
          freeze: true,
          freeze_message: "Setting Up",
          method:
            "dhananjaya.dhananjaya.doctype.pg_upload_batch.pg_upload_batch.try_razorpay_pattern",
          args: {
            batch: frm.doc.name,
          },
          callback: function (r) {
            if (!r.exc) {
              console.log(r.message);
            }
          },
        });
      },
      "Setting Donors"
    );
    frm.add_custom_button(
      __("Try AU QR Pattern"),
      function () {
        frappe.call({
          freeze: true,
          freeze_message: "Setting Up",
          method:
            "dhananjaya.dhananjaya.doctype.pg_upload_batch.pg_upload_batch.try_au_qr_pattern",
          args: {
            batch: frm.doc.name,
          },
          callback: function (r) {
            if (!r.exc) {
              console.log(r.message);
            }
          },
        });
      },
      "Setting Donors"
    );
  },
  bank_transaction: function (frm) {
    frm.events.set_finalview(frm);
  },
  async recalculate_amounts(frm) {
    var total_amount = 0;
    var total_fee = 0;
    var txs = await frappe.db.get_list("Payment Gateway Transaction", {
      fields: ["name", "amount", "fee"],
      filters: [
        ["batch", "=", frm.doc.name],
        ["receipt_created", "=", 0],
      ],
      limit: 10000,
    });

    await txs.forEach((element) => {
      total_amount += element["amount"];
      total_fee += element["fee"];
    });
		// console.log(total_amount);
		// console.log(total_amount.toFixed(2));

    frm.set_value("total_amount", total_amount.toFixed(2));
    frm.set_value("total_fee", total_fee.toFixed(2));
    frm.set_value("final_amount", (total_amount - total_fee).toFixed(2));
    if (frm.doc.bank_transaction) {
      var amount = await frappe.db.get_value(
        "Bank Transaction",
        frm.doc.bank_transaction,
        "unallocated_amount"
      );
      console.log(amount["message"]["unallocated_amount"]);
      frm.set_value("bank_amount", amount["message"]["unallocated_amount"]);
    }

    if (frm.is_dirty()) {
      frm.save();
    }
  },
  async set_finalview(frm) {
    frappe.call({
      method:
        "dhananjaya.dhananjaya.doctype.pg_upload_batch.pg_upload_batch.count_donor_linked",
      args: {
        batch: frm.doc.name,
      },
      callback: function (r) {
        if (!r.exc) {
          console.log(r);
          var diff_amount = frm.doc.bank_amount - frm.doc.final_amount;
          var add_html = "";
          if (diff_amount == 0) {
            frm.se;
            add_html = '<h3 class="p-1" style = "color:green"> ELIGIBLE </h3>';
          } else {
            add_html =
              '<h3 class="p-1" style = "color:red"> NOT-ELIGIBLE </h3>';
          }

          var dataview = `
							<div style="margin:5px">
								<h2>Final Data</h2>
								<div class ="d-flex flex-row-reverse">
									<div class= "border rounded p-2 w-25" style="font-size:15px">
										Donors Linked : ${r.message[0]}/${r.message[1]}
									</div>
								</div>
								<div class="d-flex justify-content-between">
									<div class="p-2">Amount as Per Bank</div>
									<div class="p-2"> ₹ ${frm.doc.bank_amount}</div>
								</div>
								<div class="d-flex justify-content-between">
									<div class="p-2">Amount as Per Gateway</div>
									<div class="p-2"> ₹ ${frm.doc.final_amount}</div>
								</div>
								<hr>
								<div class="d-flex justify-content-between">
									<div class="p-2">Difference</div>
									<div class="p-2"> ₹ <b>${diff_amount}</b></div>
								</div>
								<div class ="d-flex justify-content-center">
									${add_html}
								</div>
							</div>
							`;
          frm.set_df_property("final_view", "options", dataview);
          frm.refresh_field("final_view");
        }
      },
    });
  },
});
