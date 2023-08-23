import frappe


@frappe.whitelist()
def get_festival_benefit(request):
    request = frappe.get_doc("Donation Receipt", request)

    donation_dict = {
        "donation_receipt": request.name,
        "donor": request.donor,
        "donor_name": request.full_name,
        "donation_amount": request.amount,
        "receipt_date": request.receipt_date,
        "preacher": request.preacher,
    }
    benefit_entry = frappe.new_doc("Donor Festival Benefit")
    benefit_entry.update(donation_dict)
    # donor_entry.set("accounts", accounts)
    return benefit_entry
