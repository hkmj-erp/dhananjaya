from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

from dhananjaya.constants import INDIAN_STATES

fields = {
    "User": [
        dict(
            fieldname="dhananjaya_section",
            label="Dhananjaya Settings",
            fieldtype="Section Break",
            insert_after="roles",
            collapsible=1,
        ),
        dict(
            fieldname="default_indian_state",
            label="Default State",
            fieldtype="Select",
            options="\n" + "\n".join(INDIAN_STATES),
            default="Rajasthan",
            insert_after="dhananjaya_section",
        ),
        dict(
            fieldname="print_reference_id",
            label="Print Reference ID",
            fieldtype="Check",
            insert_after="default_indian_state",
        ),
        dict(
            fieldname="default_company",
            label="Default Company",
            fieldtype="Link",
            options="Company",
            insert_after="print_reference_id",
        ),
        dict(
            fieldname="column_break_ddi1v",
            label="Notifications",
            fieldtype="Column Break",
            insert_after="default_company",
        ),
        dict(
            fieldname="special_puja_notification",
            label="Special Puja",
            default=1,
            fieldtype="Check",
            insert_after="column_break_ddi1v",
        ),
        dict(
            fieldname="donor_creation_notification",
            label="Donor Creation",
            default=1,
            fieldtype="Check",
            insert_after="special_puja_notification",
        ),
        dict(
            fieldname="donor_claim_notification",
            label="Donor Claim",
            fieldtype="Check",
            default=1,
            insert_after="donor_creation_notification",
        ),
        dict(
            fieldname="donation_receipt_notification",
            label="Donation Receipt",
            fieldtype="Check",
            default=1,
            insert_after="donor_claim_notification",
        ),
        dict(
            fieldname="donor_reminder_notification",
            label="Donation Reminder",
            fieldtype="Check",
            default=1,
            insert_after="donation_receipt_notification",
        ),
    ],
}


def execute():
    create_custom_fields(fields, update=True)
