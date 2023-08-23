import frappe
from firebase_admin import messaging
import os
import sys
import firebase_admin

if not firebase_admin._apps:
    cred = firebase_admin.credentials.Certificate(os.path.join(sys.path[0], "firebase.json"))
    firebase_admin.initialize_app(cred)

def send_app_notification(user,title,content,data=None):
        
    tokens = frappe.db.get_list('Firebase App Token', pluck='token',filters={'user': user},)
    if len(tokens)>0:
        # See documentation on defining a message payload.
        message = messaging.MulticastMessage(
            data=data,
            notification=messaging.Notification(
                            title=title,
                            body=content,
                        ),
            tokens=tokens
        )
        response = messaging.send_multicast(message)
        return response

def user_profile():
    pass