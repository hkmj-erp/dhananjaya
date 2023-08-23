# Copyright (c) 2023, Narahari Dasa and contributors
# For license information, please see license.txt

import os
import re
from dhananjaya.dhananjaya.utils import get_best_contact_address, get_formatted_address
from frappe import _
import frappe
from frappe.model.document import Document
from frappe.utils.csvutils import get_csv_content_from_google_sheets, read_csv_content
from frappe.utils.data import money_in_words
from frappe.utils.xlsxutils import (
    read_xls_file_from_attached_file,
    read_xlsx_file_from_attached_file,
)

STANDARD_FIELDS = ["transaction_id", "amount", "fee"]


class DhananjayaSettings(Document):
    def get_data_from_template_file(self):
        content = None
        extension = None

        if self.gateway_file:
            content, extension = self.read_file(self.gateway_file)

        elif self.google_sheets_url:
            content = get_csv_content_from_google_sheets(self.google_sheets_url)
            extension = "csv"

        if not content:
            frappe.throw(_("Invalid or corrupted content for import"))

        if not extension:
            extension = "csv"

        if content:
            return self.read_content(content, extension)

    def read_content(self, content, extension):
        error_title = _("Template Error")
        if extension not in ("csv", "xlsx", "xls"):
            frappe.throw(
                _("Import template should be of type .csv, .xlsx or .xls"),
                title=error_title,
            )

        if extension == "csv":
            data = read_csv_content(content)
        elif extension == "xlsx":
            data = read_xlsx_file_from_attached_file(fcontent=content)
        elif extension == "xls":
            data = read_xls_file_from_attached_file(content)

        return data

    def read_file(self, file_path: str):
        extn = os.path.splitext(file_path)[1][1:]

        file_content = None

        file_name = frappe.db.get_value("File", {"file_url": file_path})
        if file_name:
            file = frappe.get_doc("File", file_name)
            file_content = file.get_content()

        return file_content, extn


def get_standard_indices(headers):
    std_indices_pos = {}
    for field in STANDARD_FIELDS:
        if field in headers:
            std_indices_pos.setdefault(field, headers.index(field))
        else:
            frappe.throw("Standard Fields are not in Uploaded File.")
    return std_indices_pos


@frappe.whitelist()
def upload_gateway_transactions(*args, **kwargs):
    from frappe.utils.csvutils import read_csv_content

    settings = frappe.get_cached_doc("Dhananjaya Settings")
    rows = settings.get_data_from_template_file()
    count = 0

    # Get Index of Transaction ID
    headers = rows[0]
    std_indices = get_standard_indices(rows[0])

    # Batch Details Capture
    batch_doc = frappe.new_doc("PG Upload Batch")
    batch_doc.company = settings.pg_company
    batch_doc.gateway = settings.gateway
    batch_doc.insert()

    total_amount, total_fee = 0, 0

    for row in rows[1:]:
        data = {
            "doctype": "Payment Gateway Transaction",
            "gateway": settings.gateway,
            "company": settings.pg_company,
        }
        for field in STANDARD_FIELDS:
            data.setdefault(field, row[std_indices[field]])
        extra_data = {}
        for idx, header in enumerate(headers):
            if header not in STANDARD_FIELDS:
                extra_data[header] = row[idx]
        data.setdefault("extra_data", extra_data)
        if data["transaction_id"] is not None:
            doc = frappe.get_doc(data)
            doc.batch = batch_doc.name
            doc.insert()
            total_amount += float(doc.amount)
            total_fee += float(doc.fee)

    batch_doc.total_amount = total_amount
    batch_doc.total_fee = total_fee
    batch_doc.final_amount = total_amount - total_fee
    batch_doc.save()
    frappe.db.commit()


@frappe.whitelist()
def get_print_donation(dr):
    dr_doc = frappe.get_doc("Donation Receipt", dr)

    settings_doc = frappe.get_cached_doc("Dhananjaya Settings")
    company_detail = None
    for d in settings_doc.company_details:
        if d.company == dr_doc.company:
            company_detail = d

    sevak_name = None

    if dr_doc.patron:
        sevak_name = frappe.db.get_value("Patron", dr_doc.patron, "full_name") + "(P)"
    elif dr_doc.sevak_name:
        sevak_name = dr_doc.sevak_name

    if dr_doc.donor:
        donor_doc = frappe.get_doc("Donor", dr_doc.donor)

        address, contact, email = get_best_contact_address(donor_doc.name)

        dr_data = {
            "full_name": donor_doc.full_name,
            "pan_no": donor_doc.pan_no,
            "aadhar_no": donor_doc.aadhar_no,
            # "address": get_formatted_address(address),
            "address": dr_doc.address,
            "contact": "" if dr_doc.contact is None else dr_doc.contact,
            "email": "" if email is None else email,
            "money_in_words": money_in_words(dr_doc.amount, main_currency="Rupees"),
        }
        if sevak_name:
            dr_data.update({"sevak_name": sevak_name})
    else:
        donor_creation_request_doc = frappe.get_doc(
            "Donor Creation Request", dr_doc.donor_creation_request
        )

        address_values = [
            donor_creation_request_doc.address_line_1,
            donor_creation_request_doc.address_line_2,
            donor_creation_request_doc.city,
            donor_creation_request_doc.state,
            donor_creation_request_doc.pin_code,
        ]
        non_null_values = [
            i.strip(",") for i in address_values if (i is not None and len(i) > 0)
        ]
        address = ",".join(non_null_values)

        dr_data = {
            "full_name": donor_creation_request_doc.full_name,
            "pan_no": donor_creation_request_doc.pan_number,
            "aadhar_no": donor_creation_request_doc.aadhar_number,
            "address": address,
            "contact": donor_creation_request_doc.contact_number,
            "email": None,
            "money_in_words": money_in_words(dr_doc.amount, main_currency="Rupees"),
        }

    ### Get Reference Number also if Realised.
    dr_data.update({"reference_number": ""})
    if dr_doc.bank_transaction:
        tx_doc = frappe.get_doc("Bank Transaction", dr_doc.bank_transaction)
        dr_data.update({"reference_number": tx_doc.description})

    return company_detail.as_dict(), dr_data
