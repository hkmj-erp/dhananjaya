from datetime import datetime, timedelta
import re
import frappe, json
from dhananjaya.dhananjaya.utils import get_credits_equivalent, get_preachers
from dhananjaya.dhananjaya.report.upcoming_special_pujas.puja_calculator import (
    get_puja_dates,
)


@frappe.whitelist()
def get_user_profile():
    user = frappe.session.user
    doc = frappe.get_doc("User", user)
    return {"user": doc.name, "full_name": doc.full_name}


def get_include_in_analysis_conditions():
    conditions = ""
    seva_types = frappe.get_all(
        "Seva Type",
        filters={
            "include_in_analysis": 1,
        },
        pluck="name",
    )
    seva_subtypes = frappe.get_all(
        "Seva Subtype",
        filters={
            "include_in_analysis": 1,
        },
        pluck="name",
    )
    preachers = frappe.get_all("LLP Preacher", filters=[["include_in_analysis", "=", 1]], pluck="name")

    seva_types_str = ",".join([f"'{s}'" for s in seva_types])
    seva_subtypes_str = ",".join([f"'{s}'" for s in seva_subtypes])
    preachers_str = ",".join([f"'{p}'" for p in preachers])

    conditions += f" AND seva_type IN ({seva_types_str}) "
    conditions += f" AND seva_subtype IN ({seva_subtypes_str}) "
    conditions += f" AND preacher IN ({preachers_str}) "
    return conditions


@frappe.whitelist()
def user_stats(based_on="receipt_date"):
    include_conditions = get_include_in_analysis_conditions()
    preachers = get_preachers()
    preachers_string = ",".join([f"'{p}'" for p in preachers])
    total_donations = {}
    for i in frappe.db.sql(
        f"""
                    select  company_abbreviation as company, DATE_FORMAT({based_on}, '%b-%y') as month, SUM(amount) as amount
                    from `tabDonation Receipt` dr
                    where {based_on} >= DATE_FORMAT(DATE_SUB(NOW(), INTERVAL 6 MONTH), '%Y-%m-01')
                    and docstatus = 1
                    and dr.preacher IN ({preachers_string})
                    {include_conditions}
                    group by company_abbreviation, DATE_FORMAT({based_on}, '%b-%y')
                    order by company,YEAR({based_on}) asc,MONTH({based_on}) asc   
                    """,
        as_dict=1,
    ):
        key = i["company"] + "|" + i["month"]
        total_donations.setdefault(key, i)

    for i in frappe.db.sql(
        f"""
                    select  company_abbreviation as company, company as company_full, DATE_FORMAT(posting_date, '%b-%y') as month, SUM(credits) as credits
                    from `tabDonation Credit` dc
                    where posting_date >= DATE_FORMAT(DATE_SUB(NOW(), INTERVAL 6 MONTH), '%Y-%m-01')
                    and dc.preacher IN ({preachers_string})
                    group by company_abbreviation, DATE_FORMAT(posting_date, '%b-%y')
                    order by company,YEAR(posting_date) asc,MONTH(posting_date) asc   
                    """,
        as_dict=1,
    ):
        credits_amount = get_credits_equivalent(i["company_full"], i["credits"])
        key = i["company"] + "|" + i["month"]
        if key not in total_donations:
            total_donations.setdefault(key, {"company": i["company"], "month": i["month"], "amount": 0})
        total_donations[key]["amount"] += credits_amount

    return total_donations.values()


@frappe.whitelist()
def send_message():
    from redis import Redis

    redis_server = Redis.from_url("redis://test.hkmjerp.in:12311")
    redis_server.publish("events", frappe.as_json({"event": "sas", "message": "demo", "room": "perso"}))


@frappe.whitelist()
def is_the_user_cashier():
    if "DCC Cashier" in frappe.get_roles():
        return True
    return False


@frappe.whitelist()
def get_upcoming_pujas():
    current_date = datetime.now().date()
    after_seven_days = current_date + timedelta(days=8)
    preachers = get_preachers()
    return get_puja_dates(current_date, after_seven_days, preachers)


@frappe.whitelist()
def fetch_donor_by_contact(contact):
    if contact and contact != "":
        clean_contact = re.sub(r"\D", "", contact)[-10:]
        if len(clean_contact) == 10:
            contacts = frappe.db.sql(
                f"""
                    select contact_no,parent
                    from `tabDonor Contact`
                    where REGEXP_REPLACE(contact_no, '[^0-9]+', '') LIKE '%{clean_contact}%' and parenttype = 'Donor'
                    """,
                as_dict=1,
            )
            if len(contacts) > 0:
                donor = contacts[0]["parent"]
                donor_dict = frappe.get_doc("Donor", donor).as_dict()
                donations = frappe.get_all(
                    "Donation Receipt",
                    fields=[
                        "sum(amount) as total_donation",
                        "count(amount) as times",
                    ],
                    filters={"donor": donor},
                    group_by="donor",
                )
                donor_dict["total_donation"] = donor_dict["times"] = 0

                if len(donations) > 0:
                    donor_dict["total_donation"] = donations[0]["total_donation"]
                    donor_dict["times"] = donations[0]["times"]

                return donor_dict
    return None


@frappe.whitelist(allow_guest=True)
def get_oauth_client_id(app_name):
    clients = frappe.get_all("OAuth Client", filters=[["app_name", "=", app_name]], fields=["name", "client_id"])
    if len(clients) == 0:
        frappe.throw("There is no OAuth Setup associated with this App.")
    else:
        return clients[0]["client_id"]


@frappe.whitelist(allow_guest=True)
def get_erp_domains():
    return frappe.get_all(
        "ERP Domain", filters=[["active", "=", 1]], fields=["name", "erp_title", "erp_address"], order_by="name asc"
    )
