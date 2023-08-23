# Copyright (c) 2023, Narahari Dasa and contributors
# For license information, please see license.txt

import gzip
import zipfile, io
import frappe, os
from frappe import conf, sendmail
from frappe.utils.file_manager import save_file
from frappe.model.document import Document
from frappe.utils import get_bench_path, cstr

from dhananjaya.dhananjaya.utils import get_pdf_dr


class DhananjayaReceiptsExport(Document):
    pass


@frappe.whitelist()
def generate_receipts():
    frappe.enqueue(process_receipts_pdf_bundle, queue="long")

def delete_old_backups(older_than=24):
    """
    Cleans up the backup_link_path directory by deleting older files
    """
    receipts_file_path = frappe.utils.get_site_path(f"public/receipts_backup")
    if os.path.exists(receipts_file_path):
        file_list = os.listdir(receipts_file_path)
        for this_file in file_list:
            this_file_path = os.path.join(receipts_file_path, this_file)
            os.remove(this_file_path)


def setup_backup_directory():
    receipts_folder = frappe.utils.get_site_path("public/receipts_backup")
    if not os.path.exists(receipts_folder):
        os.makedirs(receipts_folder, exist_ok=True)


def process_receipts_pdf_bundle():
    export_doc = frappe.get_doc("Dhananjaya Receipts Export")
    receipts = frappe.get_all(
        "Donation Receipt",
        fields="name",
        filters=[
            ["docstatus", "=", 1],
            ["company", "=", export_doc.company],
            ["receipt_date", "between", [export_doc.date_from, export_doc.date_to]],
        ],
    )

    setup_backup_directory()
    # delete_old_backups()

    pdf_bytes_list = []
    pdf_names = []

    for receipt in receipts:
        receipt_doc = frappe.get_doc("Donation Receipt", receipt["name"])
        receipt = get_pdf_dr(
            doctype="Donation Receipt", name=receipt_doc.name, doc=receipt_doc
        )
        pdf_bytes_list.append(receipt)
        pdf_names.append(receipt_doc.name)

    zip_data = io.BytesIO()
    with zipfile.ZipFile(zip_data, "w", zipfile.ZIP_DEFLATED) as zipf:
        for i, pdf_bytes in enumerate(pdf_bytes_list):
            filename = f"{pdf_names[i]}.pdf"
            zipf.writestr(filename, pdf_bytes)

    # Save and serve the ZIP file using Frappe
    file_name = f"{export_doc.company}.zip"
    receipts_file_path = frappe.utils.get_site_path(
        f"public/receipts_backup/{file_name}"
    )

    with open(receipts_file_path, "wb") as file:
        file.write(zip_data.getvalue())

    with open(receipts_file_path, "rb") as file:
        file_content = file.read()

    fileaddress = frappe.utils.get_url() + f"/receipts_backup/{file_name}"

    sendmail(
        recipients=frappe.session.user,
        subject=f"Receipts Bundle Prepared",
        message=f"Hare Krishna,<br>Please click below to download the file bundle of receipts.<br><a href = '{fileaddress}'>Link for downloading the Receipts</a>",
    )