# Copyright (c) 2023, Narahari Dasa and contributors
# For license information, please see license.txt
from dhananjaya.dhananjaya.api.utils import send_app_notification
from dhananjaya.dhananjaya.utils import (
    get_best_contact_address,
    get_default_bank_accounts,
    get_pdf_dr,
    get_preacher_users,
)
import frappe
from frappe import _, sendmail
from frappe.utils import money_in_words, today, unique

# from erpnext.controllers.accounts_controller import AccountsController
from datetime import datetime
from frappe.model.document import Document


CASH_PAYMENT_MODE = "Cash"
PAYMENT_GATWEWAY_MODE = "Gateway"
CHEQUE_MODE = "Cheque"
CUT_OFF_DATE = "2023-01-04"


class DonationReceipt(Document):
    ###### ON CHANGE TRIGGERS ON EVERY CHANGE ON SAVE, SUBMIT & AFTER SUBMIT ALSO ######
    ###### UPDATE JOURNAL ENTRY & GL ENTRIES ON SEVA TYPE CHANGE #######################
    ###### UPDATE PAYMENT GATEWAY TRANSACTION ALSO TO HAVE SAME DONOR & SEVA TYPE ######
    def on_change(self):
        if self.has_value_changed("workflow_state"):
            self.notify_mobile_app_users()
        if self.docstatus == 1:
            # Update the same Donor in Payment Gateway Transaction also, if changed.
            if self.has_value_changed("donor"):
                frappe.db.set_value(
                    "Payment Gateway Transaction",
                    self.payment_gateway_document,
                    "donor",
                    self.donor,
                )
            # self.update_account_based_on_seva_type() # Use Only in Emergency Cases.
        return

    #######################################################

    # Update Accounts in Journal Entry & General Ledger, if changed.

    def update_account_based_on_seva_type(self):
        if self.has_value_changed("seva_type"):
            frappe.db.set_value(
                "Payment Gateway Transaction",
                self.payment_gateway_document,
                "seva_type",
                self.seva_type,
            )

            company_detail = get_default_bank_accounts(self.company)
            if company_detail.auto_create_journal_entries:
                seva_doc = frappe.get_cached_doc("Seva Type", self.seva_type)
            if not seva_doc.account:
                frappe.throw(("No Account associated with this Seva Type."))

            frappe.db.set_value(
                "Donation Receipt",
                self.name,
                "donation_account",
                seva_doc.account,
                update_modified=False,
            )

            old_account = frappe.db.get_value("Donation Receipt", self.name, "donation_account")

            je = frappe.get_all(
                "Journal Entry",
                filters={"donation_receipt": self.name},
                fields=["name"],
            )

            je = frappe.get_doc("Journal Entry", je[0]["name"])

            for idx, acc in enumerate(je.accounts):
                if acc.credit == self.amount:
                    frappe.db.set_value(
                        "Journal Entry Account",
                        acc.name,
                        "account",
                        seva_doc.account,
                    )

            frappe.errprint(old_account)
            gl_entry = frappe.get_all(
                "GL Entry",
                filters={"voucher_no": je.name, "credit": [">", 0]},
                fields=["name"],
            )

            frappe.db.set_value("GL Entry", gl_entry[0]["name"], "account", seva_doc.account)

        frappe.db.commit()

    #######################################################

    def notify_mobile_app_users(self):
        message = title = None
        current_time = datetime.now().strftime("%d %B, %Y %I:%M %p")
        if self.workflow_state == "Received by Cashier" and self.payment_method == "Cash":
            title = f"{self.payment_method} Acknowledgement"
            message = f"This is to acknowledge that Cashier has received a cash of Rs. {self.amount} from you at {current_time}."

        elif self.workflow_state == "Cheque Collected" and self.payment_method == "Cheque":
            title = f"{self.payment_method} Acknowledgement"
            message = f"This is to acknowledge that Cashier has collected a cheque of Rs. {self.amount} from you at {current_time}."

        elif self.workflow_state == "Realized" and not self.is_ecs:
            title = f"{self.full_name} Receipt Realised!"
            message = f"This is to inform you that donation by {self.full_name} has been realized of Rs. {self.amount} from Bank Statement."
        elif self.workflow_state == "Realized" and self.is_ecs:
            title = f"{self.full_name} ECS Ready!"
            message = f"This is to inform you that ECS donation by {self.full_name} has been realized of Rs. {self.amount} from Bank Statement."

        # IF Message is Ready!
        if title is not None:
            erp_users = []
            if not self.preacher:
                erp_users = [self.owner]
            else:
                # erp_user = frappe.db.get_value(
                #     "LLP Preacher", self.preacher, "erp_user"
                # )
                erp_users = get_preacher_users(self.preacher)
            for erp_user in erp_users:
                doc = frappe.get_doc(
                    {
                        "doctype": "App Notification",
                        "user": erp_user,
                        "subject": title,
                        "message": message,
                        "is_route": 1,
                        "route": f"/donation_receipt/{self.name}",
                    }
                )
                doc.insert(ignore_permissions=True)
                # send_app_notification(erp_user, title, message, data)

    ############## BEFORE SAVE #############

    def before_save(self):
        self.amount_in_words = money_in_words(self.amount, main_currency="Rupees")

        # Check for Preacher Change
        if not self.is_new() and self.has_value_changed("preacher") and "DCC Manager" not in frappe.get_roles():
            frappe.throw("Only DCC Manager is allowed to change the Preacher of a Donor.")

        if not self.contact:
            address, contact, email = get_best_contact_address(self.donor)
            self.contact = "" if contact is None else contact
            self.address = "" if address is None else address

        company_detail = get_default_bank_accounts(self.company)
        account = frappe.db.get_value("Seva Type", self.seva_type, "account")
        if account is None:
            self.donation_account = company_detail.donation_account
        else:
            self.donation_account = account

        return

    ###### UPDATE WORKFLOW STATE FROM 'SUSPENSE' TO 'REALIZED' ON ENTERING THE RIGHT DONOR ######
    _saving_flag = False

    # def on_update_after_submit(self):
    #     if not self._saving_flag:
    #         self._saving_flag = True
    #         if self.donor:
    #             self.db_set("workflow_state", "Realized", update_modified=True)
    #         self.save()
    #         self._saving_flag = False

    ###### BEFORE SUBMIT : CHECK WHETHER REQUIRED ACCOUNTS ARE SET ######

    def before_submit(self):
        company_detail = get_default_bank_accounts(self.company)
        if not company_detail.auto_create_journal_entries:
            return

        if not self.donation_account:
            frappe.throw(_("Income account for Donation is <b>NOT</b> set."))

        if self.payment_method == CASH_PAYMENT_MODE:
            if not self.cash_account:
                frappe.throw(_("Cash Account is not provided."))
        else:
            if not self.bank_account:
                frappe.throw(_("Bank Account is not provided."))
            if not self.bank_transaction:
                frappe.throw(_("Bank Transaction is required to be linked before realisation."))

    ###### ON INSERT : AUTO CREATE JOURNAL ENTRY CHECK ######

    def on_submit(self):
        company_detail = get_default_bank_accounts(self.company)
        if company_detail.auto_create_journal_entries:
            je_doc = self.create_journal_entry()
            if self.payment_method != CASH_PAYMENT_MODE:
                self.reconcile_bank_transaction(je_doc)
            if self.payment_method == PAYMENT_GATWEWAY_MODE and self.payment_gateway_document:
                self.reconcile_gateway_transaction()

    ########################################
    ###### BEFORE INSERT : SETTINGS DEFAULT ACCOUNTS OF COMPANY ######

    def before_insert(self):
        # set default donation account
        company_detail = get_default_bank_accounts(self.company)
        if not company_detail:
            frappe.throw("There are no settings available for this Company. Please check Dhananjaya Settings")
        # if not self.donation_account:
        #     account = frappe.db.get_value("Seva Type", self.seva_type, "account")
        #     if account is None:
        #         self.donation_account = company_detail.donation_account
        #     else:
        #         self.donation_account = account
        if not self.bank_account:
            self.bank_account = company_detail.bank_account
        if not self.cash_account:
            self.cash_account = company_detail.cash_account
        if not self.gateway_expense_account:
            self.gateway_expense_account = company_detail.gateway_expense_account

    # def after_insert(self):
    #     if self.donor:
    #         self.preacher = frappe.db.get_value(
    #             "Donor", self.donor, "llp_preacher")
    #         self.save()

    ###### JOURNAL ENTRY AUTOMATION ######

    def create_journal_entry(self):
        seva_type_doc = frappe.get_cached_doc("Seva Type", self.seva_type)
        if (not seva_type_doc) or (not seva_type_doc.account):
            frappe.throw(_("Either Seva Type not set or Account is not connected. It is required."))

        je = {
            "doctype": "Journal Entry",
            "voucher_type": "Cash Entry" if self.payment_method == CASH_PAYMENT_MODE else "Bank Entry",
            "company": self.company,
            "donation_receipt": self.name,
            "docstatus": 1,
        }

        ##### In Case of New Donor Request #####

        if not self.donor:
            if not self.donor_creation_request:
                frappe.throw("At least one of Donor or Donation Creation Request document is must to process.")
            donor_name = frappe.get_value("Donor Creation Request", self.donor_creation_request, "full_name")
        else:
            donor_name = self.full_name

        ########################################

        je.setdefault(
            "user_remark",
            f"BEING AMOUNT RECEIVED FOR {self.seva_type} FROM {donor_name} AS PER R.NO.{self.name} DT:{self.receipt_date} {self.preacher} ",
        )

        accounts_details = frappe.get_all(
            "Company",
            fields=["cost_center"],
            filters={"name": self.company},
        )[0]

        if self.payment_method == CASH_PAYMENT_MODE:
            # Jounrnal Entry date should be the day Cashier received the amount because it has to tally with Cashbook.
            cash_date = self.cash_received_date if self.cash_received_date is not None else today()
            je.setdefault("posting_date", cash_date)
            je.setdefault(
                "accounts",
                [
                    {
                        "account": self.donation_account,
                        "credit_in_account_currency": self.amount,
                        # This is needed for cost center analysis.
                        "cost_center": accounts_details.cost_center,
                    },
                    {
                        "account": self.cash_account,
                        "debit_in_account_currency": self.amount,
                        # As it not compulsory. It will pick up the default.
                        # 'cost_center': 'Main - HKMJ'
                    },
                ],
            )
        else:
            bank_account_ledger = frappe.get_cached_doc("Bank Account", self.bank_account)
            transaction = frappe.get_doc("Bank Transaction", self.bank_transaction)

            if self.payment_method == CHEQUE_MODE:
                # Transaction Date should be posting date.
                je.setdefault("posting_date", transaction.date)
                je.setdefault("cheque_no", self.cheque_number)
                je.setdefault("cheque_date", self.cheque_date)
            else:
                je.setdefault("posting_date", transaction.date)
                je.setdefault("cheque_no", transaction.description)
                je.setdefault("cheque_date", self.receipt_date)
                # je.setdefault('clearance_date',transaction.date)
            # frappe.throw(transaction.date.strftime('%m/%d/%Y'))
            je.setdefault(
                "accounts",
                [
                    {
                        "account": self.donation_account,
                        "credit_in_account_currency": self.amount,
                        "cost_center": accounts_details.cost_center,
                    },
                    {
                        "account": bank_account_ledger.account,
                        "bank_account": self.bank_account,
                        "debit_in_account_currency": self.amount
                        - (0 if not self.additional_charges else self.additional_charges),
                        # 'cost_center': 'Main - HKMJ'
                    },
                ],
            )
            if self.payment_method == PAYMENT_GATWEWAY_MODE and self.additional_charges > 0:
                je["accounts"].append(
                    {
                        "account": self.gateway_expense_account,
                        "debit_in_account_currency": self.additional_charges,
                        "cost_center": accounts_details.cost_center,
                    }
                )
        je_doc = frappe.get_doc(je)
        je_doc.insert()
        return je_doc

    ###### BANK RECONCILLATION AUTOMATION ######

    # Reconciles Bank Transaction with Journal Entry and also updates the Clearance Date in Journal Entry
    def reconcile_bank_transaction(self, je_doc):
        voucher = {
            "payment_doctype": je_doc.doctype,
            "payment_name": je_doc.name,
            "amount": self.amount - (0 if not self.additional_charges else self.additional_charges),
        }
        tx_doc = frappe.get_doc("Bank Transaction", self.bank_transaction)
        add_payment_entry(tx_doc, voucher)
        frappe.db.set_value(
            "Journal Entry",
            je_doc.name,
            "clearance_date",
            tx_doc.date.strftime("%Y-%m-%d"),
        )

    ###### BANK RECONCILLATION AUTOMATION ######

    # Reconciles Bank Transaction with Journal Entry and also updates the Clearance Date in Journal Entry
    def reconcile_gateway_transaction(self):
        gateway_doc = frappe.get_doc("Payment Gateway Transaction", self.payment_gateway_document)
        gateway_doc.donor = self.donor
        gateway_doc.seva_type = self.seva_type
        gateway_doc.receipt_created = 1
        gateway_doc.save()


def add_payment_entry(tx_doc, voucher):
    "Add the vouchers with zero allocation. Save() will perform the allocations and clearance"
    if voucher["amount"] > tx_doc.unallocated_amount:
        frappe.throw(
            frappe._(
                f"Donation amount is more than Bank Transaction {tx_doc.name}'s unallocated amount ({tx_doc.unallocated_amount})."
            )
        )

    found = False
    for pe in tx_doc.payment_entries:
        if pe.payment_document == voucher["payment_doctype"] and pe.payment_entry == voucher["payment_name"]:
            found = True

    if not found:
        pe = {
            "payment_document": voucher["payment_doctype"],
            "payment_entry": voucher["payment_name"],
            "allocated_amount": voucher["amount"],
        }
        tx_doc.append("payment_entries", pe)
    tx_doc.save()


# DONOR SEARCH IN DONATION RECEIPT #
############# BEGIN ################


def get_fields(doctype, fields=None):
    if fields is None:
        fields = []
    meta = frappe.get_meta(doctype)
    fields.extend(meta.get_search_fields())

    if meta.title_field and not meta.title_field.strip() in fields:
        fields.insert(1, meta.title_field.strip())

    return unique(fields)


# To Search the Donors based on their name and contact numbers.
@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_donor(doctype, txt, searchfield, start, page_len, filters):
    fields = ["name", "full_name", "last_donation"]
    join_stmt = ""
    cond = ""
    if txt.isdigit():
        join_stmt = " left join `tabDonor Contact` dc on dc.parent = donor.name"
        fields.append("dc.contact_no as contact")
        cond += " or dc.contact_no LIKE %(txt)s"
    fields = get_fields(doctype, fields)
    fields[0] = "donor." + fields[0]
    # fields[1] = "CONCAT(IF(donor.is_patron=1,'🅿','')," + fields[1] + ")"
    return frappe.db.sql(
        """
        select {fields} 
        from `tabDonor` donor
        {join_stmt}
        where full_name LIKE %(txt)s
        {cond}
        order by last_donation desc,full_name limit %(page_len)s offset %(start)s
        """.format(
            **{"fields": ", ".join(fields), "cond": cond, "join_stmt": join_stmt}
        ),
        {"txt": "%" + txt + "%", "start": start, "page_len": 40},
    )


############# CLOSE ################
# DONOR SEARCH IN DONATION RECEIPT #


########################################
####### Cheque Bounce Procedure#########
########################################
@frappe.whitelist()
def receipt_bounce_operations(receipt):
    # Check for Permissions

    if "DCC Executive" not in frappe.get_roles():
        frappe.throw("You are not allowed to bounce until you are a DCC Executive.")

    #########################

    receipt_doc = frappe.get_doc("Donation Receipt", receipt)

    if not receipt_doc.bounce_transaction:
        frappe.throw("Bounced Transaction is Required.")

    je = frappe.get_all(
        "Journal Entry",
        fields="name",
        filters={"donation_receipt": receipt_doc.name, "docstatus": 1},
    )

    if len(je) != 1:
        frappe.throw("There is no JE associated or are more than one entry.")
    je = je[0]
    je_dict = frappe.get_doc("Journal Entry", je["name"]).as_dict()
    bank_tx_doc = frappe.get_doc("Bank Transaction", receipt_doc.bounce_transaction)

    transaction_amount = je_dict["total_debit"]

    for a in je_dict["accounts"]:
        if a["debit"] == 0:
            a["debit"] = transaction_amount
            a["debit_in_account_currency"] = transaction_amount
            a["credit"] = 0
            a["credit_in_account_currency"] = 0
        elif a["credit"] == 0:
            a["credit"] = transaction_amount
            a["credit_in_account_currency"] = transaction_amount
            a["debit"] = 0
            a["debit_in_account_currency"] = 0

    del je_dict["clearance_date"]
    del je_dict["bank_statement_name"]
    del je_dict["name"]

    je_dict["posting_date"] = bank_tx_doc.date
    je_dict["user_remark"] = je_dict["user_remark"].replace("BEING AMOUNT RECEIVED", "BEING CHEQUE RETURNED")

    reverse_je = frappe.get_doc(je_dict)
    reverse_je.submit()
    voucher = {
        "payment_doctype": reverse_je.doctype,
        "payment_name": reverse_je.name,
        "amount": reverse_je.total_debit,
    }
    add_payment_entry(bank_tx_doc, voucher)
    ## Add Clearance Date
    frappe.db.set_value(
        "Journal Entry",
        reverse_je.name,
        "clearance_date",
        bank_tx_doc.date.strftime("%Y-%m-%d"),
    )

    # Finally Bounce Donation Receipt
    frappe.db.set_value(
        "Donation Receipt",
        receipt,
        {"docstatus": 2, "workflow_state": "Bounced"},
    )


##### CANCELLATION PROCEDURE #####
############# BEGIN ##############


# To cancel connected Journal Entry & detach Journal Entry from Bank Trasaction
@frappe.whitelist()
def receipt_cancel_operations(receipt):
    # Check for Permissions

    if "DCC Manager" not in frappe.get_roles():
        frappe.throw("You are not allowed to cancel. Contact DCC Manager.")

    #########################

    receipt_doc = frappe.get_doc("Donation Receipt", receipt)

    if receipt_doc.payment_method == CASH_PAYMENT_MODE and "System Manager" not in frappe.get_roles():
        frappe.throw("Cash Receipts are strictly not allowed to cancel.")

    je = frappe.db.get_list(
        "Journal Entry",
        filters={"donation_receipt": receipt, "docstatus": 1},
        pluck="name",
    )
    if len(je) > 1:
        frappe.throw(
            "There are multiple Journal Entries against this. This seems to be incoherent. Please contact Administrator."
        )
    elif len(je) == 1:
        je = je[0]

        # Cancel JE
        frappe.db.set_value("Journal Entry", je, "docstatus", 2)
        je_doc = frappe.get_doc("Journal Entry", je)
        je_doc.make_gl_entries(cancel=1)

        # Detach Bank Statement
        if je_doc.voucher_type != "Cash Entry":
            detach_bank_transaction(je)

    # Payment Gateway Unset
    if receipt_doc.payment_gateway_document:
        frappe.db.set_value(
            "Payment Gateway Transaction",
            receipt_doc.payment_gateway_document,
            "receipt_created",
            0,
        )
        frappe.db.set_value(
            "Payment Gateway Transaction",
            receipt_doc.payment_gateway_document,
            "donor",
            None,
        )
        frappe.db.set_value(
            "Payment Gateway Transaction",
            receipt_doc.payment_gateway_document,
            "seva_type",
            None,
        )

    # Finally Cancel Donation Receipt
    frappe.db.set_value(
        "Donation Receipt",
        receipt,
        {
            "docstatus": 2,
            "workflow_state": "Cancelled",
            "payment_gateway_document": None,
        },
    )


def detach_bank_transaction(je):
    tx = frappe.db.get_list(
        "Bank Transaction",
        filters={"payment_document": "Journal Entry", "payment_entry": je},
    )
    if len(tx) != 1:
        frappe.throw("There is not a SINGLE Bank Transaction Entry. Either 0 or more than 1. Contact Administrator.")
    tx = tx[0]
    tx_doc = frappe.get_doc("Bank Transaction", tx)
    row = next(r for r in tx_doc.payment_entries if r.payment_entry == je)
    tx_doc.remove(row)
    tx_doc.save()


############# CLOSE ##############
##### CANCELLATION PROCEDURE #####


##### PAYMENT GATEWAY PROCESS ####
############ BEGIN ###############


# Process all gateway payments received in a Batch.
@frappe.whitelist()
def process_batch_gateway_payments(batch):
    batch_doc = frappe.get_doc("PG Upload Batch", batch)
    if not (batch_doc.final_amount == batch_doc.bank_amount):
        frappe.throw("This Batch processing is not eligible due to amount mismatch.")
    bank_tx_doc = frappe.get_doc("Bank Transaction", batch_doc.bank_transaction)
    settings = frappe.get_cached_doc("Dhananjaya Settings")
    payment_txs = frappe.db.get_all(
        "Payment Gateway Transaction",
        filters={"batch": batch, "receipt_created": 0},
        fields=("*"),
    )
    # Check if Seva Types are set!
    for tx in payment_txs:
        if not tx["seva_type"]:
            frappe.throw("Set Seva Types in all the batch gateway payments.")

    # Check if Donors & Seva Types are set!
    if settings.pg_donor_reqd:
        for tx in payment_txs:
            if not tx["donor"]:
                frappe.throw("Set Donor compulsorily in all batch gateway payments.")

    seva_account = frappe.db.get_value("Seva Type", tx["seva_type"], "account")
    ## Best Address Contact 
    address, contact, email = get_best_contact_address(tx["donor"])
    for tx in payment_txs:
        dr = {
            "doctype": "Donation Receipt",
            "company": batch_doc.company,
            "payment_gateway_document": tx["name"],
            # States as per Donor
            "docstatus": 0,
            "workflow_state": "Draft",
            "donor": tx["donor"],
            # Rest of Data
            "contact":contact,
            "address":address,
            "seva_type": tx["seva_type"],
            "donation_account": seva_account,
            "receipt_date": bank_tx_doc.date,
            "payment_method": PAYMENT_GATWEWAY_MODE,
            "amount": tx["amount"],
            "additional_charges": tx["fee"],
            "gateway_expense_account": batch_doc.gateway_expense_account,
            "bank_account": batch_doc.bank_account,
            "bank_transaction": batch_doc.bank_transaction,
        }
        dr_doc = frappe.get_doc(dr)
        dr_doc.submit()
        # If Suspense
        if tx["donor"]:
            dr_doc.db_set("workflow_state", "Realized")
        else:
            dr_doc.db_set("workflow_state", "Suspense")
        frappe.db.set_value("Payment Gateway Transaction", tx["name"], "receipt_created", 1)


############ CLOSE ###############
##### PAYMENT GATEWAY PROCESS ####


########## Send Receipt ##########


@frappe.whitelist()
def send_receipt(dr):
    from frappe.core.doctype.communication.email import make

    dr_doc = frappe.get_doc("Donation Receipt", dr)
    # recipient = frappe.db.get_value("LLP Preacher", dr_doc.preacher, "erp_user")
    recipients = get_preacher_users(dr_doc.preacher)
    if len(recipients) == 0:
        frappe.throw(_(f"There is no ERP User set in LLP Preacher Profile of {dr_doc.preacher}"))

    ext = ".pdf"
    content = get_pdf_dr(doctype=dr_doc.doctype, name=dr_doc.name, doc=dr_doc)
    out = {"fname": f"{dr_doc.name}" + ext, "fcontent": content}
    attachments = [out]

    sendmail(
        recipients=recipients,
        sender="DCC Jaipur <donorcare@harekrishnajaipur.org>",
        reference_doctype=dr_doc.doctype,
        reference_name=dr_doc.name,
        subject=f"Receipt : {dr_doc.full_name}",
        message=f"Hare Krishna,<br>Please find attached the Donation Receipt/Acknowledgement for Donor : {dr_doc.full_name} ({dr_doc.donor}) <br><br> Receipt ID : {dr_doc.name}",
        attachments=attachments,
    )
