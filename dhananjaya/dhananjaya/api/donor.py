import json
import frappe
from dhananjaya.dhananjaya.utils import get_preachers, get_donor_details

# @frappe.whitelist()
# def donor_stats(donor):
# 	user  = frappe.session.user
# 	query_string = """
# 					select  company_abbreviation as company, SUM(amount) as amount
# 					from `tabDonation Receipt` dr
# 					where {}
# 					and workflow_state = 'Realized'
# 					and donor = '{}'
# 					group by company_abbreviation
# 					order by company,YEAR(receipt_date) desc,MONTH(receipt_date) desc
# 					"""
# 	last_year_query_string = query_string.format(' receipt_date > (NOW() - INTERVAL 12 MONTH)',donor)
# 	total_query_string = query_string.format(' 1 ',donor)
# 	return {
# 				'last_year':frappe.db.sql(last_year_query_string,as_dict=1),
# 				'total':frappe.db.sql(total_query_string,as_dict=1)
# 			}


@frappe.whitelist()
def memebers_search(filters):
    # preachers = frappe.get_all(
    #     "LLP Preacher", filters={"erp_user": frappe.session.user}, pluck="name"
    # )
    preachers = get_preachers()
    preachers_string = ",".join([f"'{p}'" for p in preachers])

    filters = json.loads(filters)
    # join_string = ""
    where_string = ""
    having_string = ""

    # name, mobile, address, email

    if filters.get("name"):
        where_string += f""" AND td.full_name LIKE '%{filters.get("name")}%' """

    # frappe.errprint(where_string)
    # if filters.get("preacher"):
    # 	where_string += f""" AND td.llp_preacher = '{filters.get("preacher")}' """

    if filters.get("mobile"):
        # where_string += f" and tdc.contact_no LIKE '%{filters.get("contact_no")}%'"
        having_string += f""" AND contact LIKE '%{filters.get("mobile")}%' """

    if filters.get("address"):
        # select_string += "group"
        having_string += f""" AND address LIKE '%{filters.get("address")}%' """

    members = {}

    if not filters.get("search_type"):
        search_doctype = "Donor"
    else:
        if filters.get("search_type") == "donor":
            search_doctype = "Donor"
        elif filters.get("search_type") == "patron":
            search_doctype = "Patron"

    ## As Ashraya Level is applicable to only Donor Data

    ashraya_level_select = ""
    if search_doctype == "Donor":
        ashraya_level_select = " td.ashraya_level, "
        if filters.get("ashraya_level") and filters.get("ashraya_level") != "All":
            where_string += f""" AND td.ashraya_level = '{filters.get("ashraya_level")}' """

    for i in frappe.db.sql(
        f"""
					select td.name as {search_doctype.lower()}_id,td.full_name as {search_doctype.lower()}_name, td.llp_preacher,
                    {ashraya_level_select}
					TRIM(BOTH ',' 
                        FROM CONCAT_WS(",",
                            IF(td.pan_no is not null and TRIM(td.pan_no) != '','✅ PAN',''), 
                            IF(td.aadhar_no is not null and TRIM(td.aadhar_no) != '','✅ Aadhar','')
                            )
                        ) as kyc,
					GROUP_CONCAT(DISTINCT tda.address_line_1,tda.address_line_2,tda.city SEPARATOR' | ') as address,
					GROUP_CONCAT(DISTINCT tdc.contact_no SEPARATOR' , ') as contact,
					td.pan_no,td.aadhar_no
					from `tab{search_doctype}` td
					left join `tabDonor Contact` tdc on tdc.parent = td.name
					left join `tabDonor Address` tda on tda.parent = td.name
					where 1
					{where_string}
					group by td.name
					having 1 {having_string}
					order by FIELD(td.llp_preacher,{preachers_string}) desc
					limit 100
					""",
        as_dict=1,
    ):
        members.setdefault(i[f"{search_doctype.lower()}_id"], i)
    donation_details = {}
    if len(members.keys()) > 0:
        for i in frappe.db.sql(
            f"""
						select tdr.{search_doctype.lower()}, count(*) as times, sum(tdr.amount) as total_donation, MAX(tdr.receipt_date) as last_donation,
						IF(MAX(tdr.receipt_date) > NOW() - INTERVAL 2 year,"active","non_active") as status
						from `tabDonation Receipt` tdr
						where tdr.docstatus = 1 and tdr.{search_doctype.lower()} IN ({",".join([f"'{name}'" for name in members.keys()])})
						group by {search_doctype.lower()}
						""",
            as_dict=1,
        ):
            donation_details.setdefault(i[search_doctype.lower()], i)

    for d in members:
        not_related = False
        donation = {"times": 0, "total_donation": 0, "last_donation": None}
        if d in donation_details:
            donation = donation_details[d]
        members[d].update(donation)
        if members[d]["llp_preacher"] not in preachers:
            members[d]["contact"] = "***********"
            not_related = True

        members[d]["not_related"] = not_related

    data = list(members.values())

    data.sort(key=lambda x: (x["llp_preacher"] in preachers, x["times"]), reverse=True)  #

    return data


@frappe.whitelist()
def member_stats(member, type="donor"):
    user = frappe.session.user
    query_string = """
					select  company_abbreviation as company, SUM(amount) as amount
					from `tabDonation Receipt` dr
					where {}
					and docstatus = 1
					and {} = '{}'
					group by company_abbreviation
					order by company,YEAR(receipt_date) desc,MONTH(receipt_date) desc
					"""
    last_year_query_string = query_string.format(" receipt_date > (NOW() - INTERVAL 12 MONTH)", type, member)
    total_query_string = query_string.format(" 1 ", type, member)
    return {
        "last_year": frappe.db.sql(last_year_query_string, as_dict=1),
        "total": frappe.db.sql(total_query_string, as_dict=1),
    }


@frappe.whitelist()
def update_donor_contact_address():
    # return frappe.request.data
    data = json.loads(frappe.request.data)
    if data["to_update"] == "Contact":
        frappe.db.set_value("Donor Contact", data["name"], "contact_no", data["contact_no"])
    elif data["to_update"] == "Address":
        ## So that we can directly put full address data as it is in Donor Address
        del data["to_update"]
        if "contact_no" in data:
            del data["contact_no"]
        frappe.db.set_value("Donor Address", data["name"], data)
    return


@frappe.whitelist()
def add_donor_contact_address():
    data = json.loads(frappe.request.data)

    donor = frappe.get_doc("Donor", data["parent"])

    if data["to_add"] == "Contact":
        donor.append(
            "contacts",
            {
                "contact_no": data["contact_no"],
            },
        )
    elif data["to_add"] == "Address":
        del data["to_add"]
        if "contact_no" in data:
            del data["contact_no"]
        donor.append("addresses", data)

    donor.save(ignore_permissions=True)
    return


@frappe.whitelist()
def get_donor_suggestions(filters):
    preachers = get_preachers()
    if len(preachers) == 0:
        return []
    else:
        filters = json.loads(filters)
        page = 0
        if filters.get("page"):
            page = filters.get("page")
        offset = 50
        where_string = ""
        # priority =
        preachers = ", ".join(f"'{p}'" for p in preachers)
        suggestions = {}
        for i in frappe.db.sql(
            f"""
                                        select *
                                        from `tabDonor Suggestion` tds
                                        where tds.disabled != 1 AND preacher IN ({preachers})
                                        {where_string}
                                        ORDER BY priority DESC
                                        limit {page*offset}, {offset}
                                        """,
            as_dict=1,
        ):
            suggestions.setdefault(i["name"], i)

        donor_details = get_donor_details([suggestions[s]["donor"] for s in suggestions])

        for s in suggestions:
            suggestions[s].update(donor_details[suggestions[s]["donor"]])

        data = list(suggestions.values())
        frappe.response.page = page
        return data


@frappe.whitelist()
def last_patron(donorId):
    latest_patron = None

    latest = frappe.db.sql(
        f"""
                    SELECT patron 
                    FROM `tabDonation Receipt`
                    WHERE patron IS NOT NULL
                    AND donor = '{donorId}'
                    ORDER BY receipt_date DESC
                    LIMIT 1;
                    """,
        as_dict=1,
    )

    if len(latest) > 0:
        latest_patron = latest[0]["patron"]
        doc = frappe.get_doc("Patron", latest_patron)
        return {"patron_name": doc.full_name, "patron_id": doc.name}
    return latest_patron


@frappe.whitelist()
def get_donor_lnglats():
    preachers = get_preachers()
    if len(preachers) == 0:
        return []
    preachers_str = ",".join([f"'{p}'" for p in preachers])
    # donors = frappe.get_list("Donor", filters=[["llp_preacher", "in", get_preachers()]], fields=["name", "full_name","llp_preacher"])

    # donor_ids =

    # frappe.get_all("Donor Address", filters={"parent"})

    addresses = frappe.db.sql(
        f"""
                select tda.name as address_id,tda.address_line_1,tda.address_line_2,tda.longitude, tda.latitude, td.name as donor_id, td.full_name
                  from `tabDonor Address` tda
                    join `tabDonor` td
                  on td.name = tda.parent
                where td.llp_preacher in ({preachers_str})
                and tda.longitude != 0
                    """,
        as_dict=1,
    )

    return addresses
