import frappe
from frappe import _
import re
from frappe.utils.csvutils import get_csv_content_from_google_sheets, read_csv_content

from frappe.utils.pdf import get_pdf
from frappe.www.printview import validate_print_permission
from frappe import local
from cryptography.fernet import Fernet

from dhananjaya.dhananjaya.notification_tags import DJNotificationTags


def check_user_notify(user, tag):
    user_doc = frappe.get_doc("User", user)
    if tag == DJNotificationTags.DONOR_CREATION_TAG and user_doc.donor_creation_notification:
        return True
    if tag == DJNotificationTags.SPECIAL_PUJA_TAG and user_doc.special_puja_notification:
        return True
    if tag == DJNotificationTags.DONOR_CLAIM_TAG and user_doc.donor_claim_notification:
        return True
    if tag == DJNotificationTags.DONATION_RECEIPT_TAG and user_doc.donation_receipt_notification:
        return True
    if tag == DJNotificationTags.DONOR_REMINDER_TAG and user_doc.donor_reminder_notification:
        return True
    if tag in [DJNotificationTags.ECS_CREATION_TAG]:
        return True
    return False


# def get_dhananjaya_firebase_app():
#     settings_doc = frappe.get_cached_doc("Dhananjaya Settings")
#     fa_doc = frappe.get_doc("Firebase Admin App", settings_doc.firebase_admin_app)
#     return fa_doc.instance


@frappe.whitelist()
def get_short_url(long_url):
    doc = frappe.get_doc({"doctype": "DCC Redirect", "redirect_to": long_url})
    doc.insert()
    frappe.db.commit()
    short_url = local.request.host_url + "sl/" + doc.name
    return short_url


receiptIDkey = "wiuhi12nr89evi328721ih32kj"


@frappe.whitelist()
def encode_donation_id(receiptId):
    # donation_doc = frappe.get_doc("Donation Receipt", receiptId)
    settings = frappe.get_doc("Dhananjaya Settings")

    if not settings.public_fernet_key:
        key = Fernet.generate_key()
        frappe.db.set_value("Dhananjaya Settings", "Dhananjaya Settings", "public_fernet_key", key.decode())
        frappe.db.commit()
    else:
        key = settings.public_fernet_key.encode()

    f = Fernet(key)

    token = f.encrypt(receiptId.encode())
    return token.decode()


@frappe.whitelist(allow_guest=True)
def download_pdf_public(
    receiptToken,
    doctype="Donation Receipt",
):
    settings = frappe.get_doc("Dhananjaya Settings")
    key = settings.public_fernet_key.encode()
    f = Fernet(key)
    decryptReceiptId = f.decrypt(receiptToken.encode())
    receiptId = decryptReceiptId.decode()
    doc = frappe.get_doc(doctype, receiptId)
    if doc.docstatus == 2:
        return "This document is cancelled."
    # validate_print_permission(doc)
    content = frappe.render_template("dhananjaya/templates/80g_receipt.html", is_path=True, context={"doc": doc})
    # options={"password":"krishna"} if password required
    pdf_file = get_pdf(content)

    frappe.local.response.filename = "{name}.pdf".format(name=receiptId.replace(" ", "-").replace("/", "-"))
    frappe.local.response.filecontent = pdf_file
    frappe.local.response.type = "pdf"


## This returns the preachers assigned to a User
@frappe.whitelist()
def get_preachers():
    preachers = []
    for i in frappe.db.sql(
        f"""
                    select p.name
                    from `tabLLP Preacher` p
                    join `tabLLP Preacher User` pu
                    on p.name = pu.parent
                    where pu.user = '{frappe.session.user}'
                    group by p.name
                    """,
        as_dict=1,
    ):
        preachers.append(i["name"])
    return preachers


## This returns the Users, the preacher is assigned to.
@frappe.whitelist()
def get_preacher_users(preacher):
    ## PRCH_REMAP
    users = []

    for i in frappe.db.sql(
        f"""
                    select pu.user
                    from `tabLLP Preacher` p
                    join `tabLLP Preacher User` pu
                    on p.name = pu.parent
                    where p.name = '{preacher}'
                    group by pu.user
                    """,
        as_dict=1,
    ):
        users.append(i["user"])
    return users


# @frappe.whitelist()
# def get_preachers_by_user(user):
#     preachers = []
#     for i in frappe.db.sql(
#         f"""
#                     select p.name
#                     from `tabLLP Preacher` p
#                     join `tabLLP Preacher User` pu
#                     on p.name = pu.parent
#                     where pu.user = '{user}'
#                     group by p.name
#                     """,
#         as_dict=1,
#     ):
#         preachers.append(i["name"])
#     return preachers


@frappe.whitelist()
def get_default_bank_account(company):
    doc = frappe.get_cached_doc("Dhananjaya Settings")
    for d in doc.defaults:
        if d.company == company:
            return d.bank_account
    return None


@frappe.whitelist()
def get_default_income_account(company):
    doc = frappe.get_cached_doc("Dhananjaya Settings")
    for d in doc.defaults:
        if d.company == company:
            return d.donation_account
    return None


@frappe.whitelist()
def get_default_bank_accounts(company):
    doc = frappe.get_cached_doc("Dhananjaya Settings")
    for d in doc.company_details:
        if d.company == company:
            return d
    return None


def extract_longest_digits(string):
    digits = re.findall(r"\d+", string)
    longest_digits = max(digits, key=len)
    return longest_digits


def is_valid_pan_number(pan):
    pan_pattern = re.compile("[A-Z]{5}[0-9]{4}[A-Z]{1}")
    if pan_pattern.fullmatch(pan):
        return True
    return False


def is_valid_aadhar_number(aadhar_number):
    # regex pattern for aadhar number
    aadhar_pattern = re.compile(r"^\d{12}$")

    # check if aadhar number matches the pattern
    if aadhar_pattern.match(aadhar_number):
        return True
    return False


def get_pdf_dr(doctype, name, doc=None):
    doc = doc or frappe.get_doc(doctype, name)

    if doc.docstatus == 2:
        return "This document is cancelled."
    validate_print_permission(doc)
    content = frappe.render_template("dhananjaya/templates/80g_receipt.html", is_path=True, context={"doc": doc})
    # options={"password":"krishna"} if password required
    pdf_file = get_pdf(content)
    return pdf_file


@frappe.whitelist()
def download_pdf(
    name,
    doctype="Donation Receipt",
    format=None,
    doc=None,
    no_letterhead=0,
    language=None,
    letterhead=None,
):
    frappe.local.response.filename = "{name}.pdf".format(name=name.replace(" ", "-").replace("/", "-"))
    frappe.local.response.filecontent = get_pdf_dr(doctype, name, doc=None)
    frappe.local.response.type = "pdf"


def get_data_from_google_sheets(url):
    content = None
    extension = None

    if url:
        content = get_csv_content_from_google_sheets(url)
        extension = "csv"
    else:
        frappe.throw("Please put the link of Google Sheets First.")

    if not content:
        frappe.throw(_("Invalid or corrupted content for import"))

    if content:
        return read_content(content, extension)


def read_content(content, extension):
    error_title = _("Template Error")
    if extension not in ("csv", "xlsx", "xls"):
        frappe.throw(
            _("Import template should be of type .csv, .xlsx or .xls"),
            title=error_title,
        )

    if extension == "csv":
        data = read_csv_content(content)
    return data


def get_donor_details(donors):
    if donors is None or len(donors) == 0:
        return {}

    if not isinstance(donors, list):
        donors = [donors]

    donors = list(set(donors))

    donors_string = ",".join([f"'{d}'" for d in donors])

    donor_details = {}

    for i in frappe.db.sql(
        f"""
					select td.name as donor_id,td.full_name as donor_name, td.llp_preacher,
					TRIM(BOTH ',' FROM CONCAT_WS(",",IF(td.pan_no is not null,'✅ PAN',''), IF(td.aadhar_no is not null,'✅ Aadhar',''))) as kyc,
					GROUP_CONCAT(DISTINCT tda.address_line_1,tda.address_line_2,tda.city SEPARATOR' | ') as address,
					GROUP_CONCAT(DISTINCT tdc.contact_no SEPARATOR' , ') as contact,
					td.pan_no,td.aadhar_no
					from `tabDonor` td
					left join `tabDonor Contact` tdc on tdc.parent = td.name
					left join `tabDonor Address` tda on tda.parent = td.name
					where 1
					and td.name IN ({donors_string})
					group by td.name
					""",
        as_dict=1,
    ):
        donor_details.setdefault(i["donor_id"], i)

    donation_details = {}
    if len(donor_details.keys()) > 0:
        for i in frappe.db.sql(
            f"""
						select tdr.donor, count(*) as times, sum(tdr.amount) as total_donation, MAX(tdr.receipt_date) as last_donation,
						IF(MAX(tdr.receipt_date) > NOW() - INTERVAL 2 year,"active","non_active") as status
						from `tabDonation Receipt` tdr
						where tdr.docstatus = 1 and tdr.donor IN ({",".join([f"'{name}'" for name in donor_details.keys()])})
						group by donor
						""",
            as_dict=1,
        ):
            donation_details.setdefault(i["donor"], i)
    for d in donor_details:
        donation = {"times": 0, "total_donation": 0, "last_donation": None}
        if d in donation_details:
            donation = donation_details[d]
        donor_details[d].update(donation)

    return donor_details


@frappe.whitelist()
def get_best_contact_address(docname):
    try:
        donor_doc = frappe.get_doc("Donor", docname)
    except:
        return None, None, None
    address = None
    for add in donor_doc.addresses:
        if add.preferred:
            address = add
    if address is None and len(donor_doc.addresses) > 0:
        address = donor_doc.addresses[0]

    contact = None
    for ct in donor_doc.contacts:
        cleaned_ct = re.sub("\D", "", ct.contact_no)
        if len(cleaned_ct) >= 10:
            contact = cleaned_ct
            break
    if contact is None and len(donor_doc.contacts) > 0:
        contact = donor_doc.contacts[0].contact_no

    email = None
    if len(donor_doc.emails) > 0:
        email = donor_doc.emails[0].email

    return get_formatted_address(address), contact, email


def get_formatted_address(address):
    if address is None:
        return ""
    else:
        values = [
            address.address_line_1,
            address.address_line_2,
            address.city,
            address.state,
            address.pin_code,
        ]
        non_null_values = [i.strip(",") for i in values if (i is not None and len(i) > 0)]
        return ", ".join(non_null_values)


def get_donation_companies():
    settings = frappe.get_doc("Dhananjaya Settings")
    companies = []
    for c in settings.company_details:
        companies.append(c.company)
    return companies


def get_credits_equivalent(company: str, credits: float):
    settings = frappe.get_cached_doc("Dhananjaya Settings")
    for s in settings.company_details:
        if s.company == company:
            return credits * s.credit_value
    return credits


def get_credit_values(companies: list):
    values = {}
    settings = frappe.get_cached_doc("Dhananjaya Settings")
    for s in settings.company_details:
        if s.company in companies:
            values.setdefault(s.company, s.credit_value)
    if len(values) == len(companies):
        return values
    frappe.throw("One of the Companies' configuration is missing in Dhananjaya Settings.")


def is_null_or_blank(value):
    """
    Check if a string is either None, empty, or consists only of whitespace characters.

    Args:
        value (str): The string to check.

    Returns:
        bool: True if the string is None, empty, or blank; otherwise, False.
    """
    return value is None or (isinstance(value, str) and value.strip() == "")


def sanitise_str(val: str):
    return re.sub(r"\s+", " ", val).strip()
