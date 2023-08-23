import json
from mimetypes import guess_type
import PIL
import frappe
from frappe.handler import upload_file
from frappe.model.workflow import apply_workflow
from frappe.utils.data import today
from frappe.utils.image import optimize_image
from dhananjaya.dhananjaya.utils import get_preachers

@frappe.whitelist()
def get_fields():
    metadata = frappe.get_meta("Donation Receipt")
    input_fields = []
    for field in metadata.fields:
        if not (field.hidden or field.read_only or not field.label):
            input_fields.append(field)

    return input_fields


@frappe.whitelist()
def create_receipt():
    donation = json.loads(frappe.form_dict.data)

    #### Update KYC ####

    if not donation["donor"]["is_new"]:
        donor_doc = frappe.get_doc("Donor", donation["donor"]["name"])
        donor_doc.pan_no = donation["donor"]["pan_no"]
        donor_doc.aadhar_no = donation["donor"]["aadhar_no"]
        donor_doc.save(ignore_permissions=True)

    ##### Create Receipt #####
    doc = frappe.new_doc("Donation Receipt")
    doc.company = donation["company"]
    if "receipt_date" in donation:
        doc.receipt_date = donation["receipt_date"]
    else:
        doc.receipt_date = today()
    doc.preacher = donation["donor"]["llp_preacher"]

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

    if donation["donor"]["is_new"]:
        doc.donor_creation_request = donation["donor"]["donor_creation_request"]
    else:
        doc.donor = donation["donor"]["name"]

    if "patron" in donation and donation["patron"]:
        doc.patron = donation["patron"]
    doc.sevak_name = donation["sevak_name"]

    cheque_image_name = ""
    if donation["payment_method"] == "Cheque":
        doc.cheque_date = donation["cheque_date"]
        doc.cheque_number = donation["cheque_number"]
        doc.ifsc_code = donation["ifsc_code"]
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
            # try:
            #     content = optimize_image(**args)
            # except PIL.UnidentifiedImageError as e:
            #     print("ERROR Image Optimisation"+str(e))
            #     print("filename "+fileref)

        filename = doc.name + "-" + donation["payment_method"] + cheque_image_name + "." + fileref.split(".")[-1]
        frappe.local.uploaded_file = content
        frappe.local.uploaded_filename = filename
        # file_url = frappe.form_dict.file_url
        frappe.get_doc(
            {
                "doctype": "File",
                "attached_to_doctype": doc.doctype,
                "attached_to_name": doc.name,
                "folder": "Home/Donation Reference",
                "file_name": filename,
                "is_private": 0,
                "content": content,
            }
        ).save(ignore_permissions=1)
    return doc


@frappe.whitelist()
def get_receipts(filters):
    filters = json.loads(filters)
    where_string = ""

    # name, mobile, address, email
    page = 0
    if filters.get("page"):
        page = filters.get("page")
    if filters.get("name"):
        where_string += f""" AND tdr.full_name LIKE '%{filters.get("name")}%' """
    if filters.get("fromDate"):
        where_string += f""" AND tdr.receipt_date >= '{filters.get("fromDate")}' """
    if filters.get("toDate"):
        where_string += f""" AND tdr.receipt_date <= '{filters.get("toDate")}' """
    if filters.get("company") and filters.get("company") != "All":
        where_string += f""" AND tdr.company = '{filters.get("company")}' """
    if filters.get("specific_month") and filters.get("specific_month") != "0":
        where_string += f""" AND MONTH(tdr.receipt_date) = {filters.get("specific_month")} """  # MONTH(create_date)

    sortOrder = filters.get("sortOrder") if filters.get("sortOrder") else "ASC"

    preachers = get_preachers()

    preachers = ", ".join(f"'{p}'" for p in preachers)

    receipts = {}

    offset = 50
    for i in frappe.db.sql(
        f"""
					select *
					from `tabDonation Receipt` tdr
					where tdr.docstatus != 2 AND preacher IN ({preachers})
					{where_string}
					ORDER BY creation {sortOrder}, receipt_date
					limit {page*offset}, {offset}
					""",
        as_dict=1,
    ):
        receipts.setdefault(i["name"], i)

    donors = {}

    # if len(receipts.keys()) > 0:
    # 	for i in frappe.db.sql(f"""
    # 				select td.name as donor_id,
    # 				GROUP_CONCAT(DISTINCT tda.address_line_1,tda.address_line_2,tda.city SEPARATOR' | ') as address,
    # 				GROUP_CONCAT(DISTINCT tdc.contact_no SEPARATOR' , ') as contact
    # 				from `tabDonor` td
    # 				left join `tabDonor Contact` tdc on tdc.parent = td.name
    # 				left join `tabDonor Address` tda on tda.parent = td.name
    # 				where td.name IN ({",".join([f"'{receipt['donor']}'" for receipt in receipts.values()])})
    # 				group by td.name
    # 				""",as_dict=1):
    # 		donors.setdefault(i['donor_id'],i)

    # for r in receipts:
    # 	receipts[r]['donor_data'] = donors[receipts[r]['donor']]

    data = list(receipts.values())

    # data['page'] = page
    frappe.response.where_string = [where_string, page, offset]
    frappe.response.page = page
    return data


@frappe.whitelist()
def cashier_approve_receipt(docname):
    doc = frappe.get_doc("Donation Receipt", docname)
    if doc.payment_method == "Cash":
        apply_workflow(doc, "Receive Cash")
        frappe.db.commit()
        frappe.response.done = True
    elif doc.payment_method == "Cheque":
        apply_workflow(doc, "Collect Cheque")
        frappe.db.commit()
        frappe.response.done = True
    else:
        frappe.response.done = False
        return "Wrong Action"
