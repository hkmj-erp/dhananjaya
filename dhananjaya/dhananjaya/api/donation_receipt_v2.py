from mimetypes import guess_type
import frappe, json

from frappe.utils.data import today
from frappe.utils.image import optimize_image
from dhananjaya.dhananjaya.utils import get_preachers


@frappe.whitelist()
def create_receipt():
    donation = json.loads(frappe.form_dict.data)

    #### Update KYC ####

    if donation["mode"] == "exisitingDonor":
        donor_doc = frappe.get_doc("Donor", donation["donor"])
        donor_doc.pan_no = donation["pan_no"]
        donor_doc.aadhar_no = donation["aadhar_no"]
        donor_doc.save(ignore_permissions=True)
        preacher = donor_doc.llp_preacher
    else:
        donor_request_doc = frappe.get_doc("Donor Creation Request", donation["donorCreation"])
        preacher = donor_request_doc.llp_preacher

    ##### Create Receipt #####
    doc = frappe.new_doc("Donation Receipt")
    doc.company = donation["company"]
    if "receipt_date" in donation:
        doc.receipt_date = donation["receipt_date"]
    else:
        doc.receipt_date = today()

    doc.preacher = preacher

    ## Print Reference ID
    if "print_remarks_on_receipt" in donation:
        doc.print_remarks_on_receipt = donation["print_remarks_on_receipt"]

    doc.payment_method = donation["payment_method"]
    doc.amount = donation["amount"]
    if "remarks" in donation:
        doc.remarks = donation["remarks"]
    doc.seva_type = donation["seva_type"]
    if "atg_required" in donation:
        doc.atg_required = donation["atg_required"]
    doc.seva_subtype = donation["seva_subtype"]

    ## Selected Address & Contact
    doc.contact = donation["contact"]
    doc.address = donation["address"]

    if donation["mode"] == "exisitingDonor":
        doc.donor = donation["donor"]
    else:
        doc.donor_creation_request = donation["donorCreation"]

    if "patron" in donation and donation["patron"]:
        doc.patron = donation["patron"]
    doc.sevak_name = donation["sevak_name"]

    cheque_image_name = ""
    if donation["payment_method"] == "Cheque":
        doc.cheque_date = donation["cheque_date"]
        doc.cheque_number = donation["cheque_number"]
        # doc.ifsc_code = donation["ifsc_code"] //TODO: sddd
        doc.bank_name = donation["bank_name"]
        cheque_image_name = "_" + donation["cheque_date"] + "_" + donation["cheque_number"]

    doc.insert()

    doc.db_set("workflow_state", "Acknowledged")

    files = frappe.request.files
    fileref = frappe.form_dict.file_name

    if "image" in files:
        file = files["image"]
        content = file.stream.read()
        fileref = file.filename

        content_type = guess_type(fileref)[0]
        if content_type.startswith("image/"):
            args = {"content": content, "content_type": content_type}
            args["max_width"] = 1200
            content = optimize_image(**args)

        filename = doc.name + "-" + donation["payment_method"] + cheque_image_name + "." + fileref.split(".")[-1]
        frappe.local.uploaded_file = content
        frappe.local.uploaded_filename = filename
        # file_url = frappe.form_dict.file_url
        image_doc = frappe.get_doc(
            {
                "doctype": "File",
                "attached_to_doctype": doc.doctype,
                "attached_to_name": doc.name,
                "attached_to_field": "payment_screenshot",
                "folder": "Home/Donation Reference",
                "file_name": filename,
                "is_private": 0,
                "content": content,
            }
        ).save(ignore_permissions=1)
        doc.payment_screenshot = image_doc.file_url
    doc.save()
    return doc


## This feature is created to bypass permissions issue while fetching the receipts.
@frappe.whitelist()
def get_receipts_of_donor(donor):
    preachers = get_preachers()
    preacher = frappe.db.get_value("Donor", donor, "llp_preacher")
    if preacher not in preachers:
        frappe.throw("Not Allowed")
    return frappe.get_all("Donation Receipt", fields=["*"], filters=[["docstatus", "!=", "2"], ["donor", "=", donor]])


## This feature is created to bypass permissions issue while fetching the receipts.
@frappe.whitelist()
def get_receipts_of_patron(patron):
    preachers = get_preachers()
    preacher = frappe.db.get_value("Patron", patron, "llp_preacher")
    if preacher not in preachers:
        frappe.throw("Not Allowed")
    return frappe.get_all("Donation Receipt", fields=["*"], filters=[["docstatus", "!=", "2"], ["patron", "=", patron]])


@frappe.whitelist()
def get_receipts_of_a_month(filters, order_by, limit_start, limit):
    filters = json.loads(filters)

    where_string = ""

    order_by_string = " ORDER BY receipt_date desc"

    if order_by:
        order_by_string = f""" ORDER BY {order_by} """

    limit_string = " LIMIT 1000"
    if limit_start:
        limit_string = f" LIMIT {limit_start}, {limit}"

    for ftr in filters:
        if "full_name" in ftr:
            where_string += f""" AND tdr.full_name LIKE '%{ftr[2]}%' """
        if "specific_month" in ftr and ftr[2] != "":
            where_string += f""" AND MONTH(tdr.receipt_date) = {ftr[2]} """

    # if filters.get("company") and filters.get("company") != "All":
    #     where_string += f""" AND tdr.company = '{filters.get("company")}' """

    preachers = get_preachers()

    preachers = ", ".join(f"'{p}'" for p in preachers)

    receipts = []

    for i in frappe.db.sql(
        f"""
					select *
					from `tabDonation Receipt` tdr
					where tdr.docstatus != 2 AND preacher IN ({preachers})
					{where_string}
                    {order_by_string}
                    {limit_string}
					""",
        as_dict=1,
    ):
        receipts.append(i)
    return receipts
