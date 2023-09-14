# Copyright (c) 2023, Narahari Dasa and contributors
# For license information, please see license.txt

import json
import frappe
from frappe.model.document import Document

class DonorMerger(Document):
	pass

@frappe.whitelist()
def get_donor_details(donor):
	data = frappe.get_doc("Donor",donor)
	return data.as_json()

@frappe.whitelist()
def merge_donors(donor_first, donor_second, priority_first,	priority_second, address_values,contact_values):
	priority_first = int(priority_first)
	priority_second = int(priority_second)
	address_values = json.loads(address_values)
	contact_values = json.loads(contact_values)

	if priority_first:
		merge_to = frappe.get_doc("Donor",donor_first)
		merge_from = frappe.get_doc("Donor",donor_second)
	elif priority_second:
		merge_to = frappe.get_doc("Donor",donor_second)
		merge_from = frappe.get_doc("Donor",donor_first)
	
	# chosen_addresses = []

	chosen_addresses = frappe.get_all("Donor Address", filters = {"name":["IN",address_values]}, fields = ['preferred','type','name','parent','address_line_1'])
	v = []
	# for address in addresses:
	# 	if address['preferred']:
	# 		for c_add in chosen_addresses:
	# 			v.append([address.address_line_1,c_add['address_line_1'],c_add['preferred'], c_add['parent'], merge_to.name])
	# 			if c_add['preferred'] and c_add['parent'] == merge_to.name:
	# 				c_add['preferred'] = 0
	# 	chosen_addresses.append(address)
	# return v

	preferred_adds = list(filter(lambda x: x['preferred'], chosen_addresses))

	if len(preferred_adds)>1:
		for add in chosen_addresses:
			if add['preferred'] and add['parent'] != merge_to.name:
				add['preferred'] = 0
	
	# return chosen_addresses
	all_addresses =  merge_to.addresses + merge_from.addresses

	# return chosen_addresses,address_values, merge_to.full_name, merge_from.full_name

	for address in all_addresses:
		remove_flag = 1
		for c_add in chosen_addresses:
			if address.name == c_add['name']:
				address.preferred = c_add['preferred']
				if address.parent != merge_to.name:
					address.parent = merge_to.name
				address.save()
				remove_flag = 0
				break
		if remove_flag:
			if merge_to.name == address.parent:
				# return address,chosen_addresses
				merge_to.remove(address)
				merge_to.save()
			else:
				# merge_from.remove(address)
				merge_from.save()

	merge_from.reload()
	merge_to.reload()
	
	# return all_addresses

	# contacts = [c.contact_no  for c in merge_to.contacts ]
	# for con in merge_from.contacts:
	# 	if (not con in contacts):
	# 		con.parent = merge_to.name
	# 		con.save()

	all_contacts =  merge_to.contacts + merge_from.contacts
	for contact in all_contacts:
		if contact.name in contact_values:
			if contact.parent != merge_to.name:
				contact.parent = merge_to.name
				contact.save()
				# frappe.db.set_value("Donor Contact",contact.name,'parent',merge_to.name)
		else:
			if merge_to.name == contact.parent:
				merge_to.remove(contact)
				merge_to.save()
			else:
				merge_from.remove(contact)
				merge_from.save()

	merge_to.reload()
	merge_from.reload()

	for em in merge_from.emails:
		em.parent = merge_to.name
		em.save()
	
	merge_to.reload()
	merge_from.reload()

	for puja in merge_from.puja_details:
		puja.parent = merge_to.name
		puja.save()
	
	merge_to.reload()
	merge_from.reload()
	
	merge_to.old_donor_id = (if_none(merge_to.old_donor_id)+","+if_none(merge_from.old_donor_id)).strip(',')
	merge_to.unresolved_fax_column = (if_none(merge_to.unresolved_fax_column)+","+if_none(merge_from.unresolved_fax_column)).strip(',')

	if merge_from.pan_no:
		if merge_to.pan_no and merge_to.pan_no != merge_from.pan_no:
			merge_to.pan_no = merge_to.pan_no +","+merge_from.pan_no
		else:
			merge_to.pan_no = merge_from.pan_no
	if merge_from.aadhar_no:
		if merge_to.aadhar_no and merge_to.aadhar_no != merge_from.aadhar_no:
			merge_to.aadhar_no = merge_to.aadhar_no +","+merge_from.aadhar_no
		else:
			merge_to.aadhar_no = merge_from.aadhar_no
	if merge_from.driving_license:
		merge_to.driving_license = merge_from.driving_license
	if merge_from.passport:
		merge_to.passport = merge_from.passport
	
	## ECS Merging

	ecs_details_idx = [ field.idx for field in merge_to.meta.fields if field.fieldname == 'ecs_details'][0]
	
	all_ecs_fields = [ field for field in merge_to.meta.fields if field.idx >= ecs_details_idx and field.fieldtype in ('Data','Select','Currency','Date','Check','Link')]

	for field in all_ecs_fields:
		if not getattr(merge_to,field.fieldname):
			setattr(merge_to, field.fieldname, getattr(merge_from,field.fieldname))

	merge_from.save()
	merge_to.save()
	
	frappe.db.commit()

	merge_to.reload()
	merge_from.reload()
	
	frappe.rename_doc("Donor", merge_from.name, merge_to.name, merge=1)

def if_none(val):
    if val is None:
        return""
    return val