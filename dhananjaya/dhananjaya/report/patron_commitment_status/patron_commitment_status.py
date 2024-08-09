# Copyright (c) 2024, Narahari Dasa and contributors
# For license information, please see license.txt

import calendar
from dhananjaya.dhananjaya.report.patron_commitment_status.utils import GroupConcat
import frappe
from frappe.model.document import Document
from frappe.query_builder.utils import DocType
from frappe.utils import add_to_date
from datetime import datetime
from dhananjaya.dhananjaya.utils import get_credit_values
from frappe import _
from frappe.utils.data import date_diff
from datetime import datetime
from dateutil.relativedelta import relativedelta


def test():
    PatronCommitmentStatus({"from_date": "2024-04-03", "to_date": "2024-06-28"})


def execute(filters=None):
    return PatronCommitmentStatus(filters).get_data()
    # return [], []


class PatronCommitmentStatus(object):
    def __init__(self, filters):
        self.filters = frappe._dict(filters)
        self.columns = []
        self.patrons = frappe._dict()
        self.patron_string = ""
        self.dhananjaya_settings = Document
        self.months = []
        self.message = ""
        self.set_flags()
        self.validate_filters()
        self.load_data()
        self.set_message()

    def set_flags(self):
        self.include_credits = True if self.filters.get("include_credits") else False
        self.summary = True if self.filters.get("summary") else False
        if self.summary or not self.include_credits:
            self.detailed = False
        else:
            self.detailed = True

    def set_message(self):
        patrons_block = f"""
                <div class="summary-label bold">Patron Donations</div>
                <div class="row section-break bold">
                    <div class="col-xs-6 column-break border-bottom" >
                        <div class="text-right"> Account </div>
                    </div>
                    <div class="col-xs-3 column-break border-bottom" >
                        <div class="text-right">Total Debit</div>
                    </div>	
                    <div class="col-xs-3 column-break border-bottom" >
                        <div class="text-right">Total Credit</div>
                    </div>					
                </div>		
            """
        for account in self.patron_accounts:
            patrons_block += f"""
                <div class="row section-break bold">
                    <div class="col-xs-6 column-break" >
                        <div class="text-right">{account.account}</div>
                    </div>
                    <div class="col-xs-3 column-break" >
                        <div class="text-right">{frappe.utils.fmt_money(account.total_debit,currency="₹") }</div>
                    </div>	
                    <div class="col-xs-3 column-break" >
                        <div class="text-right">{frappe.utils.fmt_money(account.total_credit,currency="₹")}</div>
                    </div>					
                </div>		
            """
        sum_debit = sum(a["total_debit"] for a in self.patron_accounts)
        sum_credit = sum(a["total_credit"] for a in self.patron_accounts)

        patrons_block += f"""
                <div class="row section-break bold">
                    <div class="col-xs-6 column-break border-top" >
                        <div class="text-right"> Total: </div>
                    </div>
                    <div class="col-xs-3 column-break border-top">
                        <div class="text-right">{frappe.utils.fmt_money(sum_debit,currency="₹")}</div>
                    </div>	
                    <div class="col-xs-3 column-break border-top">
                        <div class="text-right">{frappe.utils.fmt_money(sum_credit,currency="₹")}</div>
                    </div>						
                </div>		
            """
        ## Non Patrons Donations
        non_patrons_block = f"""
                <div class="summary-label bold">Non-Patron Donations</div>
                <div class="row section-break bold">
                    <div class="col-xs-6 column-break border-bottom" >
                        <div class="text-right"> Account </div>
                    </div>
                    <div class="col-xs-3 column-break border-bottom" >
                        <div class="text-right">Total Debit</div>
                    </div>	
                    <div class="col-xs-3 column-break border-bottom" >
                        <div class="text-right">Total Credit</div>
                    </div>					
                </div>		
            """
        for account in self.non_patron_accounts:
            non_patrons_block += f"""
                <div class="row section-break bold">
                    <div class="col-xs-6 column-break" >
                        <div class="text-right">{account.account}</div>
                    </div>
                    <div class="col-xs-3 column-break" >
                        <div class="text-right">{frappe.utils.fmt_money(account.total_debit,currency="₹") }</div>
                    </div>	
                    <div class="col-xs-3 column-break" >
                        <div class="text-right">{frappe.utils.fmt_money(account.total_credit,currency="₹")}</div>
                    </div>							
                </div>		
            """
        np_sum_debit = sum(a["total_debit"] for a in self.non_patron_accounts)
        np_sum_credit = sum(a["total_credit"] for a in self.non_patron_accounts)

        non_patrons_block += f"""
                <div class="row section-break bold">
                    <div class="col-xs-6 column-break border-top" >
                        <div class="text-right"> Total: </div>
                    </div>
                    <div class="col-xs-3 column-break border-top">
                        <div class="text-right">{frappe.utils.fmt_money(np_sum_debit,currency="₹")}</div>
                    </div>	
                    <div class="col-xs-3 column-break border-top">
                        <div class="text-right">{frappe.utils.fmt_money(np_sum_credit,currency="₹")}</div>
                    </div>					
                </div>		
            """
        sum_credits = sum(self.patrons[p]["range_credits"] for p in self.patrons)
        credits_block = f"""
                <div class="summary-label bold">Credits Donations</div>
                <div class="row section-break bold">
                    <div class="col-xs-6 column-break border-top" >
                        <div class="text-right"> Credits Total: </div>
                    </div>
                    <div class="col-xs-3 column-break border-top">
                        <div class="text-right">{frappe.utils.fmt_money(sum_credits,currency="₹")}</div>
                    </div>	
                    <div class="col-xs-3 column-break border-top">
                    </div>					
                </div>		
                """
        self.message = f"""
                <div class="row section-break bold">
                    <div class="col-xs-6 column-break" >{patrons_block}</div>
                    <div class="col-xs-6 column-break" >{non_patrons_block}</div>						
                </div>	
                <div class="row section-break bold">
                    <div class="col-xs-6 column-break" >{credits_block}</div>
                    <div class="col-xs-6 column-break" ></div>
                </div>	
        """

    def load_data(self):
        self.dhananjaya_settings = frappe.get_cached_doc("Dhananjaya Settings")
        self.get_month_year_dates_range()
        self.get_patrons()
        self.set_patron_monthwise_donations()
        self.set_patron_monthwise_credits()
        self.set_patron_totals()
        self.set_columns()
        self.set_accounts()

    def get_data(self):
        return self.columns, list(self.patrons.values()), self.message

    def set_accounts(self):
        self.patron_accounts = self.get_donation_accounts_calculation()
        self.patron_accounts = sorted(
            self.patron_accounts,
            key=lambda x: (
                -x.total_debit,
                -x.total_credit,
            ),
        )
        self.non_patron_accounts = self.get_donation_accounts_calculation(patron=False)
        self.non_patron_accounts = sorted(
            self.non_patron_accounts,
            key=lambda x: (
                -x.total_debit,
                -x.total_credit,
            ),
        )

    def get_donation_accounts_calculation(self, patron=True):
        if not patron:
            seva_types = frappe.get_all(
                "Seva Type", filters={"patronship_allowed": 1, "kind": 0}, pluck="name"
            )
            seva_types_str = ",".join([f"'{s}'" for s in seva_types])
            patron_acc_str = f" AND (patron IS NULL OR patron = '') AND tdr.seva_type IN ({seva_types_str})"
        else:
            patron_acc_str = f" AND patron IN ( {self.patron_string} )"

        jes = [
            e
            for l in frappe.db.sql(
                f"""
            SELECT tje.name
            FROM `tabDonation Receipt` tdr
            JOIN `tabJournal Entry` tje
                ON tje.donation_receipt = tdr.name
            WHERE tdr.docstatus = 1
                # AND tje.clearance_date IS NOT NULL
                AND tdr.realization_date BETWEEN '{self.filters.from_date}' AND '{self.filters.to_date}'
                {patron_acc_str}
                """
            )
            for e in l
        ]

        jes_str = ",".join([f"'{j}'" for j in jes])

        return frappe.db.sql(
            f"""
            SELECT account, SUM(debit) as total_debit, SUM(credit) as total_credit
            FROM `tabGL Entry`
            WHERE voucher_type = 'Journal Entry'
                AND voucher_no IN ({jes_str}) 
                AND is_cancelled = 0
            GROUP BY account
                """,
            as_dict=1,
        )

    def set_patron_monthwise_donations(self):
        for m in self.months:
            for d in frappe.db.sql(
                f"""
					SELECT patron, SUM(amount) as donation
					FROM `tabDonation Receipt`
					WHERE realization_date BETWEEN '{m.start_date}' AND '{m.end_date}'
						AND patron IN ( {self.patron_string} )
						AND docstatus = 1
					GROUP BY patron
							""",
                as_dict=1,
            ):
                self.patrons[d["patron"]][m.key] = d["donation"]

        ## Set Openings

        for d in frappe.db.sql(
            f"""
					SELECT patron, SUM(amount) as donation
					FROM `tabDonation Receipt`
					WHERE realization_date < '{self.filters.get("from_date")}'
						AND patron IN ( {self.patron_string} )
						AND docstatus = 1
					GROUP BY patron
							""",
            as_dict=1,
        ):
            self.patrons[d["patron"]]["opening_donation"] = d["donation"]

    def set_patron_monthwise_credits(self):
        if not self.filters.get("include_credits"):
            return
        company_credits = {}
        for c in self.dhananjaya_settings.company_details:
            company_credits[c.company] = c.credit_value

        for m in self.months:
            for d in frappe.db.sql(
                f"""
					SELECT company, patron, credits
					FROM `tabDonation Credit`
					WHERE posting_date BETWEEN '{m.start_date}' AND '{m.end_date}'
						AND patron IN ( {self.patron_string} )
							""",
                as_dict=1,
            ):
                credits_key = m.key + "_credits"
                if credits_key not in self.patrons[d["patron"]]:
                    self.patrons[d["patron"]].setdefault(credits_key, 0)

                self.patrons[d["patron"]][credits_key] += (
                    d["credits"] * company_credits[d["company"]]
                )

        ## Set Openings

        for d in frappe.db.sql(
            f"""
					SELECT company, patron, credits
					FROM `tabDonation Credit`
					WHERE posting_date < '{self.filters.get("from_date")}'
						AND patron IN ( {self.patron_string} )
							""",
            as_dict=1,
        ):
            if "opening_credits" not in self.patrons[d["patron"]]:
                self.patrons[d["patron"]].setdefault("opening_credits", 0)
            self.patrons[d["patron"]]["opening_credits"] += (
                d["credits"] * company_credits[d["company"]]
            )

    def set_patron_totals(self):

        for m in self.months:
            for p in self.patrons:
                monthly_donation = self.patrons[p].get(m.key, 0)
                monthly_credits = self.patrons[p].get(m.key + "_credits", 0)

                self.patrons[p][m.key + "_total"] = monthly_donation + monthly_credits

                if "range_donation" not in self.patrons[p]:
                    self.patrons[p].setdefault("range_donation", 0)

                if "range_credits" not in self.patrons[p]:
                    self.patrons[p].setdefault("range_credits", 0)

                self.patrons[p]["range_donation"] += monthly_donation
                self.patrons[p]["range_credits"] += monthly_credits

        for p in self.patrons:
            opening_donation = self.patrons[p].get("opening_donation", 0)
            opening_credits = self.patrons[p].get("opening_credits", 0)
            range_donation = self.patrons[p]["range_donation"]
            range_credits = self.patrons[p]["range_credits"]

            self.patrons[p]["opening"] = opening_donation + opening_credits

            self.patrons[p]["total_range"] = range_donation + range_credits

            self.patrons[p]["total_donation"] = opening_donation + range_donation
            self.patrons[p]["total_credits"] = range_credits + opening_credits

            self.patrons[p]["closing"] = (
                self.patrons[p]["total_donation"] + self.patrons[p]["total_credits"]
            )

    def get_patrons(self):
        conditions = ""
        if self.filters.get("level"):
            conditions += f" AND tp.seva_type == '{self.filters.get('level')}' "
        self.patrons = {
            p["id"]: p
            for p in frappe.db.sql(
                f"""
							SELECT tp.name as id,
									tp.full_name,
									llp_preacher,
									committed_amount,
									seva_type,
									GROUP_CONCAT(tpdn.full_name ORDER BY tpdn.idx SEPARATOR '\n') as display_names
							FROM `tabPatron` tp
							LEFT JOIN `tabPatron Display Name` tpdn
								ON tp.name = tpdn.parent
							JOIN `tabPatron Seva Type` tpst
								ON tpst.name = tp.seva_type
							WHERE 1 {conditions} AND tpst.included_in_commitment_status = 1
							GROUP BY tp.name
							ORDER BY committed_amount desc
							""",
                as_dict=1,
            )
        }
        self.patron_string = ",".join([f"'{p}'" for p in self.patrons])

    def validate_filters(self):
        if not self.filters.get("from_date") and self.filters.get("to_date"):
            frappe.throw(_("From and To Dates are required."))
        elif date_diff(self.filters.to_date, self.filters.from_date) < 0:
            frappe.throw(_("To Date cannot be before From Date."))

    def get_month_year_dates_range(self):
        start = datetime.strptime(self.filters.get("from_date"), "%Y-%m-%d")
        end = datetime.strptime(self.filters.get("to_date"), "%Y-%m-%d")

        current = start
        date_ranges = []

        while current <= end:
            # Start date of the current month
            month_start = current.strftime("%Y-%m-%d")
            # Total days in the month
            days = calendar.monthrange(current.year, current.month)[1]
            last_day = datetime(year=current.year, month=current.month, day=days)
            month_end = min(end, last_day).strftime("%Y-%m-%d")
            unique_key = current.strftime("%Y%m")

            # Format the output
            formatted_range = frappe._dict(
                key=unique_key,
                label=current.strftime("%B - %y"),
                start_date=month_start,
                end_date=month_end,
            )
            date_ranges.append(formatted_range)

            current = add_to_date(last_day, days=1)

        self.months = date_ranges

    def set_columns(self):
        columns = [
            {
                "fieldname": "id",
                "label": "Patron ID",
                "fieldtype": "Data",
                "width": 140,
            },
            {
                "fieldname": "full_name",
                "label": "Full Name",
                "fieldtype": "Data",
                "width": 200,
            },
            {
                "fieldname": "display_names",
                "label": "Display Names",
                "fieldtype": "Data",
                "width": 200,
            },
            {
                "fieldname": "seva_type",
                "label": "Level",
                "fieldtype": "Data",
                "width": 150,
            },
            {
                "fieldname": "committed_amount",
                "label": "Commitment",
                "fieldtype": "Currency",
                "width": 160,
            },
        ]
        if self.detailed:
            columns.extend(
                [
                    {
                        "fieldname": "opening_donation",
                        "label": "Opening(P)",
                        "fieldtype": "Currency",
                        "width": 160,
                    },
                    {
                        "fieldname": "opening_credits",
                        "label": "Opening(CR)",
                        "fieldtype": "Currency",
                        "width": 160,
                    },
                ]
            )
        # summary
        columns.append(
            {
                "fieldname": "opening",
                "label": "Opening(T)",
                "fieldtype": "Currency",
                "width": 160,
            },
        )

        for month in self.months:
            if self.detailed:
                columns.extend(
                    [
                        {
                            "fieldname": month.key,
                            "label": month.label + "(P)",
                            "fieldtype": "Currency",
                            "width": 130,
                        },
                        {
                            "fieldname": month.key + "_credits",
                            "label": month.label + "(CR)",
                            "fieldtype": "Currency",
                            "width": 150,
                        },
                    ]
                )
            else:
                columns.extend(
                    [
                        {
                            "fieldname": month.key + "_total",
                            "label": month.label + "(T)",
                            "fieldtype": "Currency",
                            "width": 130,
                        }
                    ]
                )

        if self.detailed:
            columns.extend(
                [
                    {
                        "fieldname": "range_donation",
                        "label": "Growth(P)",
                        "fieldtype": "Currency",
                        "width": 130,
                    },
                    {
                        "fieldname": "range_credits",
                        "label": "Growth(CR)",
                        "fieldtype": "Currency",
                        "width": 130,
                    },
                ]
            )
        columns.append(
            {
                "fieldname": "total_range",
                "label": "Growth(Total)",
                "fieldtype": "Currency",
                "width": 130,
            },
        )
        if self.detailed:
            columns.extend(
                [
                    {
                        "fieldname": "total_donation",
                        "label": "Closing(P)",
                        "fieldtype": "Currency",
                        "width": 130,
                    },
                    {
                        "fieldname": "total_credits",
                        "label": "Closing(CR)",
                        "fieldtype": "Currency",
                        "width": 130,
                    },
                ]
            )
        columns.append(
            {
                "fieldname": "closing",
                "label": "Closing",
                "fieldtype": "Currency",
                "width": 130,
            },
        )
        self.columns = columns


#     get_patrons(filters)

#     patron_map = {
#         p["id"]: {**p, "total_donated": 0, "last_month_donated": 0}
#         for p in frappe.db.sql(
#             f"""
# 						SELECT tp.name as id,
# 								tp.full_name,
# 								llp_preacher,
# 								committed_amount,
# 								seva_type,
# 								GROUP_CONCAT(tpdn.full_name ORDER BY tpdn.idx SEPARATOR '\n') as display_names
# 						FROM `tabPatron` tp
# 						LEFT JOIN `tabPatron Display Name` tpdn
# 							ON tp.name = tpdn.parent
# 						WHERE 1 {conditions}
# 						GROUP BY tp.name
# 						""",
#             as_dict=1,
#         )
#     }

#     ## Total Donated
#     for p in frappe.db.sql(
#         f"""
# 							select
# 								tp.name as id,
# 								SUM(tdr.amount) as total_donated
# 							from `tabPatron` tp
# 							left join `tabDonation Receipt` tdr
# 								on tp.name = tdr.patron
# 							where 1 {conditions}
# 							AND tdr.docstatus = 1
# 							group by tp.name
# 							""",
#         as_dict=1,
#     ):
#         patron_map[p["id"]]["total_donated"] = p["total_donated"]

#     # ## Last Month Donated
#     # for p in frappe.db.sql(
#     #     f"""
# 	# 						select
# 	# 							tp.name as id,
# 	# 							SUM(tdr.amount) as last_month_donated
# 	# 						from `tabPatron` tp
# 	# 						join `tabDonation Receipt` tdr
# 	# 							on tp.name = tdr.patron
# 	# 						where 1 {conditions}
# 	# 						AND tdr.receipt_date
# 	# 							BETWEEN
# 	# 								DATE_FORMAT(DATE_SUB(CURDATE(), INTERVAL 1 MONTH), '%Y-%m-01')
# 	# 									AND
# 	# 								LAST_DAY(DATE_SUB(CURDATE(), INTERVAL 1 MONTH))
# 	# 						AND tdr.docstatus = 1
# 	# 						group by tp.name
# 	# 						""",
#     #     as_dict=1,
#     # ):
#     #     patron_map[p["id"]]["last_month_donated"] = p["last_month_donated"]

#     ## Total Credits
#     credits = frappe.db.get_all(
#         "Donation Credit",
#         fields=["company", "patron", "credits", "posting_date"],
#         filters={"patron": ("is", "set")},
#     )
#     unique_companies = list(set([c["company"] for c in credits]))
#     credit_values_map = get_credit_values(unique_companies)

#     last_month_date = add_to_date(datetime.now(), months=-1)
#     last_month_m = last_month_date.month
#     last_month_y = last_month_date.year
#     frappe.errprint(patron_map)
#     for c in credits:
#         eqv_amount = credit_values_map[c["company"]] * c["credits"]
#         if (
#             c["posting_date"].month == last_month_m
#             and c["posting_date"].year == last_month_y
#         ):
#             patron_map[c["patron"]]["last_month_donated"] += eqv_amount
#         patron_map[c["patron"]]["total_donated"] += eqv_amount

#     for d in patron_map.values():
#         d["remaining_amount"] = d["committed_amount"] - d["total_donated"]
#     data = list(patron_map.values())
#     data = sorted(data, key=lambda x: (-x["committed_amount"], x["seva_type"]))

#     return get_columns(), data


# # def get_conditions(filters: dict) -> str:
# #     conditions = ""
# #     if filters.get("level"):
# #         conditions += f""" AND tp.seva_type = '{filters.get("level")}'"""
# #     return conditions


# def get_columns():
#     columns = [
#         {
#             "fieldname": "id",
#             "label": "Patron ID",
#             "fieldtype": "Data",
#             "width": 140,
#         },
#         {
#             "fieldname": "full_name",
#             "label": "Full Name",
#             "fieldtype": "Data",
#             "width": 200,
#         },
#         {
#             "fieldname": "display_names",
#             "label": "Display Names",
#             "fieldtype": "Data",
#             "width": 200,
#         },
#         {
#             "fieldname": "seva_type",
#             "label": "Level",
#             "fieldtype": "Data",
#             "width": 150,
#         },
#         {
#             "fieldname": "committed_amount",
#             "label": "Commitment",
#             "fieldtype": "Currency",
#             "width": 160,
#         },
#         {
#             "fieldname": "total_donated",
#             "label": "Total Donated",
#             "fieldtype": "Currency",
#             "width": 160,
#         },
#         {
#             "fieldname": "remaining_amount",
#             "label": "Remaining Amount",
#             "fieldtype": "Currency",
#             "width": 160,
#         },
#         {
#             "fieldname": "last_month_donated",
#             "label": "Last Month Donated",
#             "fieldtype": "Currency",
#             "width": 160,
#         },
#     ]
#     return columns
