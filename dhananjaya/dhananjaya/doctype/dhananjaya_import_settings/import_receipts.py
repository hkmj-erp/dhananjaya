import frappe
import re
from frappe.utils import validate_email_address, getdate
import dhananjaya.dhananjaya.doctype.dhananjaya_import_settings.constant_maps as maps
from dhananjaya.dhananjaya.doctype.dhananjaya_import_settings.utils import run_query
from datetime import datetime, timedelta
from frappe.model.workflow import apply_workflow


@frappe.whitelist()
def import_mode_of_payment(*args,**kwargs):
	data = run_query("select distinct PAYMENT_MODE from view_receipt_details")
	for d in data:
		if d['PAYMENT_MODE']:
			mode = frappe.get_doc(doctype='DJ Mode of Payment', mode=d['PAYMENT_MODE'])
			mode.insert(ignore_if_duplicate=True)




@frappe.whitelist()
def import_sevas(*args,**kwargs):
	
	companies = {}
	settings = frappe.get_cached_doc("Dhananjaya Import Settings")
	for c in settings.companies_to_import:
		companies.setdefault(c.old_trust_code,c.company)
	
	data = run_query("select distinct TRUST_ID, DONATION_CODE from view_receipt_details")
	for d in data:
		if d['DONATION_CODE'] and d['TRUST_ID'] in companies:
			seva_type = frappe.get_doc(doctype='Seva Type', seva_name=d['DONATION_CODE'], company = companies[d['TRUST_ID']])
			seva_type.insert(ignore_if_duplicate=True)

@frappe.whitelist()
def import_subsevas(*args,**kwargs):
	data = run_query("select distinct SEVA_CODE from view_receipt_details")
	for d in data:
		if d['SEVA_CODE']:
			seva_subtype = frappe.get_doc(doctype='Seva Subtype',enabled=1, seva_name=d['SEVA_CODE'])
			seva_subtype.insert(ignore_if_duplicate=True)

@frappe.whitelist()
def import_receipts(*args,**kwargs):
	settings = frappe.get_cached_doc("Dhananjaya Import Settings")
	
	companies_trust_code = {}
	for c in settings.companies_to_import:
		comp_abbr = frappe.db.get_value("Company", c.company, "abbr")
		companies_trust_code.setdefault(c.old_trust_code, {'abbr':comp_abbr,'name':c.company})
	
	
	test_string = f" limit {settings.test_run_records}" if settings.is_a_test else ""
	companies =	','.join([str(c.old_trust_code) for c in settings.companies_to_import])
	data = run_query(f"""SELECT * 
						from `view_receipt_details` 
						WHERE (PAYMENT_STATUS IN ('TS','ST','CL'))
						AND (TRUST_ID IN ({companies})) {test_string}
						AND DR_NUMBER = 2022107531
						""")

	donors = frappe.db.sql("""
				select old_donor_id,name
				from `tabDonor`
				where 1
				""")
	donor_map = {str(r[0]):str(r[1])  for r in donors}
	month_back_date = datetime.today() - timedelta(days=30)
	for ind,r in enumerate(data):
		id = donor_map[str(r['DONOR_ID'])]
		if r['PAYMENT_STATUS'] in ['TS','ST'] and getdate(r['PRESENTATION_DATE']) > month_back_date.date():
			frappe.enqueue(insert_a_receipt, queue='short',job_name="Inserting Receipt",timeout=100000,r=r, erp_id = id, company_trust= companies_trust_code)
		elif r['PAYMENT_STATUS'] == 'CL':
			frappe.enqueue(insert_a_receipt, queue='short',job_name="Inserting Receipt",timeout=100000,r=r, erp_id = id, company_trust = companies_trust_code, status="Realized")


# In Realised Stage
def insert_a_receipt(r,erp_id,company_trust,status=None):
	
	doc = frappe.new_doc('Donation Receipt')
	
	doc.company = company_trust[r['TRUST_ID']]['name']
	doc.donor = erp_id
	doc.old_dr_no = r['DR_NUMBER']
	doc.receipt_date = r['DR_DATE']
	doc.amount = r['INS_AMOUNT']
	doc.payment_method = r['PAYMENT_MODE']
	### Dyanamic Seva Type ###
	doc.seva_type = r['DONATION_CODE'] +" - "+ company_trust[r['TRUST_ID']]['abbr']

	doc.seva_subtype = r['SEVA_CODE']
	doc.preacher = r['PREACHER_CODE']
	doc.remarks = r['DR_REMARKS']

	#Cheque Details
	if r['PAYMENT_MODE'] == 'CQ':
		doc.cheque_number = r['INS_NUMBER']
		doc.cheque_date = r['PRESENTATION_DATE']
		doc.bank_name = r['INS_BANK']

	#OLD DATA
	doc.old_ar_no = r['AR_NUMBER']
	doc.old_ar_date = r['AR_DATE']
	doc.old_ins_bank = r['INS_BANK']
	doc.old_ins_account_number = r['INS_ACCOUNT_NUMBER']
	doc.old_ins_number = r['INS_NUMBER']
	doc.old_ins_date = r['INS_DATE']

	doc.insert(ignore_permissions=True)
	if status is not None:
		# apply_workflow(doc, status)
		doc.db_set("docstatus", 1)
		if r['PAYMENT_MODE'] == 'CH':
			doc.db_set("workflow_state", 'Received by Cashier')
		else:
			doc.db_set("workflow_state", 'Realized')

	
