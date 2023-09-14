# Copyright (c) 2023, Narahari Dasa and contributors
# For license information, please see license.txt

import json
from dhananjaya.dhananjaya.utils import get_default_bank_accounts
import frappe
from frappe.model.document import Document
from rapidfuzz import process, fuzz


class PGUploadBatch(Document):
    def before_insert(self):
        # set default donation account
        company_detail = get_default_bank_accounts(self.company)
        self.gateway_expense_account = company_detail.gateway_expense_account


@frappe.whitelist()
def count_donor_linked(batch):
    txs = frappe.db.get_all(
        "Payment Gateway Transaction",
        filters={"batch": batch, "receipt_created": 0},
        pluck=("donor"),
    )
    linked, total = 0, 0

    for tx in txs:
        if tx:
            linked += 1
        total += 1
    return linked, total


@frappe.whitelist()
def get_payment_entries(batch):
    txs = frappe.db.get_all(
        "Payment Gateway Transaction", filters={"batch": batch}, pluck="name"
    )
    return txs


@frappe.whitelist()
def set_seva_type_bulk(batch, seva_type):
    frappe.db.sql(
        f"""
					update `tabPayment Gateway Transaction`
					set seva_type = '{seva_type}'
					where batch = '{batch}' AND receipt_created = 0
					"""
    )
    frappe.db.commit()


@frappe.whitelist()
def try_razorpay_pattern(batch):
    txs = frappe.db.get_list(
        "Payment Gateway Transaction",
        filters={"batch": batch},
        fields=["name", "gateway", "extra_data"],
    )

    for tx in txs:
        notes = json.loads(tx["extra_data"])["notes"]
        notes = json.loads(notes)
        if not notes:
            frappe.throw("Extra Data in not Proper.")
        donor_found = razorpay_identify_and_update_donor(notes)
        if donor_found is None:
            doc = frappe.new_doc("Donor")
            doc.first_name = notes["legal_name"]
            doc.llp_preacher = "DCC"
            doc.append(
                "addresses",
                {
                    "preferred": 1,
                    "type": "Residential",
                    "address_line_1": notes["address"],
                },
            )
            doc.append(
                "contacts", {"contact_no": notes["whatsapp_number"], "is_whatsapp": 1}
            )
            doc.append(
                "emails",
                {
                    "email": notes["email"],
                },
            )
            doc.save()
            donor_found = doc.name
        frappe.db.set_value(
            "Payment Gateway Transaction", tx["name"], "donor", donor_found
        )


def razorpay_identify_and_update_donor(notes):
    mobile = notes["whatsapp_number"]
    pan_no = None
    if "pan_number" in notes:
        pan_no = notes["pan_number"]
    contacts = frappe.db.sql(
        f"""
				select contact_no,parent
				from `tabDonor Contact`
				where REGEXP_REPLACE(contact_no, '[^0-9]+', '') LIKE '%{mobile}%' and parenttype = 'Donor'
				""",
        as_dict=1,
    )
    donor_found = None
    token_ratio = 0
    for c in contacts:
        # Update Received data in all donors having same mobile number
        donor = frappe.get_doc("Donor", c["parent"])
        if pan_no and not donor.pan_no:
            donor.pan_no = pan_no
        if len(donor.addresses) == 0:
            donor.append(
                "addresses",
                {
                    "preferred": 1,
                    "type": "Residential",
                    "address_line_1": notes["address"],
                },
            )
        donor.save()

        # Exactly finding by similar name

        temp_token_ratio = fuzz.token_sort_ratio(donor.full_name, notes["legal_name"])
        if temp_token_ratio > token_ratio:
            donor_found = donor.name
    return donor_found


@frappe.whitelist()
def try_au_qr_pattern(batch):
    txs = frappe.db.get_list(
        "Payment Gateway Transaction",
        filters={"batch": batch},
        fields=["name", "gateway", "extra_data"],
    )

    for tx in txs:
        extra_data = json.loads(tx["extra_data"])
        if not extra_data:
            frappe.throw("Extra Data in not Proper.")

        donor_found = au_qr_identify_and_update_donor(extra_data)

        if donor_found is None:
            doc = frappe.new_doc("Donor")
            doc.first_name = extra_data["Customer Name"]
            doc.llp_preacher = "DCC"
            # doc.append('addresses', {
            # 		'preferred': 1,
            # 		'type':'Residential',
            # 		'address_line_1':notes['address']
            # 	})
            doc.append(
                "contacts", {"contact_no": extra_data["Mobile No"], "is_whatsapp": 1}
            )
            doc.save()
            donor_found = doc.name
        frappe.db.set_value(
            "Payment Gateway Transaction", tx["name"], "donor", donor_found
        )


def au_qr_identify_and_update_donor(extra_data):
    mobile = extra_data["Mobile No"]
    pan_no = None
    if "pan_number" in extra_data:
        pan_no = extra_data["pan_number"]
    contacts = frappe.db.sql(
        f"""
				select contact_no,parent
				from `tabDonor Contact`
				where REGEXP_REPLACE(contact_no, '[^0-9]+', '') LIKE '%{mobile}%' and parenttype = 'Donor'
				""",
        as_dict=1,
    )
    donor_found = None
    token_ratio = 0
    for c in contacts:
        donor = frappe.get_doc("Donor", c["parent"])

        # Exactly finding by similar name

        temp_token_ratio = fuzz.token_sort_ratio(
            donor.full_name, extra_data["Customer Name"]
        )
        if temp_token_ratio > token_ratio:
            donor_found = donor.name
    return donor_found
