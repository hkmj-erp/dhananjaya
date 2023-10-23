# Copyright (c) 2023, Narahari Dasa and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from datetime import datetime
from dhananjaya.dhananjaya.notification_tags import DJNotificationTags

from dhananjaya.dhananjaya.utils import check_user_notify, get_preacher_users


class DonorECSCreationRequest(Document):
    def on_change(self):
        if self.has_value_changed("status"):
            self.notify_mobile_app_users()
            if self.status == "Completed":
                self.update_donor_ecs_details()

    #######################################################

    def notify_mobile_app_users(self):
        message = title = None
        current_time = datetime.now().strftime("%d %B, %Y %I:%M %p")
        if self.status == "Completed":
            title = f"ECS Request Completed!"
            message = f"ECS Request {self.name} ({self.account_holder_name}) is completed. Sit back & relax to observe auto-generation of receipts."

        elif self.status == "Rejected":
            title = f"ECS Request Rejected!"
            message = f"ECS Request {self.name} ({self.account_holder_name}) is rejected. Please contact Administrator for resolution."

        # IF Message is Ready!
        if title is not None:
            erp_users = [self.owner]
            settings_doc = frappe.get_cached_doc("Dhananjaya Settings")
            for erp_user in erp_users:
                doc = frappe.get_doc(
                    {
                        "doctype": "App Notification",
                        "app": settings_doc.firebase_admin_app,
                        "tag": DJNotificationTags.ECS_CREATION_TAG,
                        "notify": check_user_notify(erp_user, DJNotificationTags.ECS_CREATION_TAG),
                        "user": erp_user,
                        "subject": title,
                        "message": message,
                    }
                )
                doc.insert(ignore_permissions=True)

    ##########################################################

    def update_donor_ecs_details(self):
        settings_doc = frappe.get_cached_doc("Dhananjaya Settings")
        frappe.set_value(
            "Donor",
            self.donor,
            {
                "ecs_active": 1,
                "ecs_bank":settings_doc.default_ecs_bank,
                "bank": self.account_bank_name,
                "ecs_bank_ac_no": self.account_number,
                "account_holder": self.account_holder_name,
                "ecs_id": self.name,
                "opening_date": self.start_date,
                "closing_date": self.end_date,
                "ecs_amount": self.amount,
                "settlement_day": self.debit_pay_on,
                "periodicity": self.frequency[0].upper(),
                "ecs_default_seva_type": self.seva_type,
                "ecs_default_patron": self.patron,
            },
        )
