import frappe
from dhananjaya.dhananjaya.doctype.donation_receipt.constants import (
    CASH_PAYMENT_MODE,
    TDS_PAYMENT_MODE,
    PAYMENT_GATWEWAY_MODE,
    CHEQUE_MODE,
)


def validate_kind_donation(doc):
    is_kind_mode = doc.is_kind_donation()
    sevatype_kind = frappe.db.get_value("Seva Type", doc.seva_type, "kind")
    if is_kind_mode and (not sevatype_kind):
        frappe.throw(
            "Please select a Seva Type of In-Kind Donation, since the Mode is Kind Donation"
        )

    if is_kind_mode and (not doc.kind_type):
        frappe.throw("Please select a type of Kind Donation")
    return


def validate_donation_account(doc):
    ## Check if Donation Account is set where Credit will happend in JE
    if not doc.donation_account:
        frappe.throw(_("Income account for Donation is <b>NOT</b> set."))


def validate_modes_account(doc):
    ## CHECK WHETHER REQUIRED ACCOUNTS ARE SET
    if doc.is_kind_donation():
        return
    elif doc.payment_method == CASH_PAYMENT_MODE:
        if not doc.cash_account:
            frappe.throw(_("Cash Account is not provided."))
    elif doc.payment_method == TDS_PAYMENT_MODE:
        if not doc.tds_account:
            frappe.throw(_("TDS Account is not provided."))
    else:
        if not doc.bank_account:
            frappe.throw(_("Bank Account is not provided."))
        if not doc.bank_transaction:
            frappe.throw(
                _("Bank Transaction is required to be linked before realisation.")
            )
    return


def validate_atg_required(doc):
    if not (doc.atg_required and doc.donor):
        return
    pan, aadhar = frappe.db.get_value("Donor", doc.donor, ["pan_no", "aadhar_no"])
    if not (pan or aadhar):
        frappe.throw(
            "At least one of the KYC ( PAN Number or Aadhar Number) is required for 80G Donation."
        )
    return
