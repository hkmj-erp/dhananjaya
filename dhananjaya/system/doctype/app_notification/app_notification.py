# Copyright (c) 2023, Narahari Dasa and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
import frappe
from firebase_admin import messaging
import os
import sys
import firebase_admin

if not firebase_admin._apps:
    cred = firebase_admin.credentials.Certificate(os.path.join(sys.path[0], "firebase.json"))
    firebase_admin.initialize_app(cred)

class AppNotification(Document):
    def after_insert(self):
        self.send_app_notification()

    def send_app_notification(self):
        tokens = frappe.db.get_list('Firebase App Token', pluck='token',filters={'user': self.user},)
        if len(tokens)>0:
            # See documentation on defining a message payload.
            message = messaging.MulticastMessage(
                notification=messaging.Notification(
                                title=self.subject,
                                body=self.message,
                            ),
                tokens=tokens
            )
            response = messaging.send_multicast(message)
            return response