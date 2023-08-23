import frappe
from frappe.utils.data import today


@frappe.whitelist()
def get_journal_entry_from_statement(statement):
    bank_transaction = frappe.get_doc("Bank Transaction", statement)
    company_account = frappe.get_value(
        "Bank Account", bank_transaction.bank_account, "account")

    accounts = []
    accounts.append(
        {
            # "account": "",
            "credit_in_account_currency": bank_transaction.deposit,
            "debit_in_account_currency": bank_transaction.withdrawal,
        }
    )

    accounts.append(
        {
            "account": company_account,
            "bank_account": bank_transaction.bank_account,
            "credit_in_account_currency": bank_transaction.withdrawal,
            "debit_in_account_currency": bank_transaction.deposit
        }
    )

    company = frappe.get_value("Account", company_account, "company")

    journal_entry_dict = {
        "voucher_type": "Bank Entry",
        "company": company,
        "bank_statement_name": bank_transaction.name,
        "posting_date": bank_transaction.date,
        "cheque_date": bank_transaction.date,
        "cheque_no": bank_transaction.description
    }
    journal_entry = frappe.new_doc("Journal Entry")
    journal_entry.update(journal_entry_dict)
    journal_entry.set("accounts", accounts)
    return journal_entry


def reconcile_bank_transaction_for_entries_from_statement(self, method=None):
    if not self.bank_statement_name:
        return

    bank_transaction = frappe.get_doc(
        "Bank Transaction", self.bank_statement_name)

    if self.total_debit > bank_transaction.unallocated_amount:
        frappe.throw(frappe._(
            f"Total Amount is more than Bank Transaction {bank_transaction.name}'s unallocated amount ({bank_transaction.unallocated_amount})."))

    pe = {
        "payment_document": self.doctype,
        "payment_entry": self.name,
        "allocated_amount": self.total_debit
    }
    bank_transaction.append("payment_entries", pe)
    bank_transaction.save(ignore_permissions=True)
    frappe.db.set_value("Journal Entry", self.name, 'clearance_date',
                        bank_transaction.date.strftime("%Y-%m-%d"))


@frappe.whitelist()
def get_donation_receipt_from_statement(statement):
    bank_transaction = frappe.get_doc("Bank Transaction", statement)
    payment_method = None

    if 'NEFT' in bank_transaction.description:
        payment_method = "NEFT/IMPS"
    elif 'UPI' in bank_transaction.description:
        payment_method = "UPI"

    dr_dict = {
        'company': bank_transaction.company,
        'receipt_date': today(),
        'payment_method': payment_method,
        'amount': bank_transaction.unallocated_amount,
        'bank_account': bank_transaction.bank_account,
        'bank_transaction': bank_transaction.name

    }

    donation_entry = frappe.new_doc("Donation Receipt")
    donation_entry.update(dr_dict)
    return donation_entry
