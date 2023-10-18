from . import __version__ as app_version

app_name = "dhananjaya"
app_title = "Dhananjaya"
app_publisher = "Narahari Dasa"
app_description = "Donor Management App"
app_email = "nrhdasa@gmail.com"
app_license = "MIT"

# Includes in <head>
# ------------------

# Hare Krishna

# include js, css files in header of desk.html
# app_include_css = "/assets/dhananjaya/css/dhananjaya.css"
# app_include_js = "/assets/dhananjaya/js/dhananjaya.js"

# include js, css files in header of web template
# web_include_css = "/assets/dhananjaya/css/dhananjaya.css"
# web_include_js = "/assets/dhananjaya/js/dhananjaya.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "dhananjaya/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {"Bank Transaction": "public/js/bank_transaction.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

website_route_rules = [
    {"from_route": "/sl/<short_url>", "to_route": "redirect"},
]

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
jinja = {
    "methods": ["dhananjaya.dhananjaya.doctype.dhananjaya_settings.dhananjaya_settings.get_print_donation"]
    # "filters": "dhananjaya.utils.jinja_filters"
}

# Installation
# ------------

# before_install = "dhananjaya.install.before_install"
# after_install = "dhananjaya.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "dhananjaya.uninstall.before_uninstall"
# after_uninstall = "dhananjaya.uninstall.after_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "dhananjaya.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

permission_query_conditions = {
    "Donation Receipt": "dhananjaya.dhananjaya.doctype.donation_receipt.donation_receipt_filter.list",
    "Donor": "dhananjaya.dhananjaya.doctype.donor.donor_filter.list",
    "Patron": "dhananjaya.dhananjaya.doctype.patron.patron_filter.list",
}

has_permission = {
    "Donation Receipt": "dhananjaya.dhananjaya.doctype.donation_receipt.donation_receipt_filter.single",
    "Donor": "dhananjaya.dhananjaya.doctype.donor.donor_filter.single",
    "Patron": "dhananjaya.dhananjaya.doctype.patron.patron_filter.single",
}


#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
    "Journal Entry": {
        "on_submit": "dhananjaya.dhananjaya.statement_utils.reconcile_bank_transaction_for_entries_from_statement"
        # "on_cancel" : "dhananjaya.dhananjaya.doctype.donation_receipt.donation_receipt.cancel_connected_donation_docs",
    }
    # "*": {
    # 	"on_update": "method",
    # 	"on_cancel": "method",
    # 	"on_trash": "method"
    # }
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"dhananjaya.tasks.all"
# 	],
# 	"daily": [
# 		"dhananjaya.tasks.daily"
# 	],
# 	"hourly": [
# 		"dhananjaya.tasks.hourly"
# 	],
# 	"weekly": [
# 		"dhananjaya.tasks.weekly"
# 	],
# 	"monthly": [
# 		"dhananjaya.tasks.monthly"
# 	],
# }
scheduler_events = {
    "daily": ["dhananjaya.tasks.daily.execute"],
    "daily_long": ["dhananjaya.tasks.daily_long.execute"],
    "hourly_long": ["dhananjaya.tasks.hourly_long.execute"],
    "cron": {
        "* * * * *": ["dhananjaya.tasks.every_minute.execute"],
        "0 8 * * *": ["dhananjaya.tasks.every_day_8_am.execute"],
        # Hourly but offset by 30 minutes
        "30 * * * *": [
            "dhananjaya.tasks.hourly.execute",
        ],
    },
}

# Testing
# -------

# before_tests = "dhananjaya.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "dhananjaya.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "dhananjaya.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]


# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"dhananjaya.auth.validate"
# ]
