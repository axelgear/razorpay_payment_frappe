import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields



def execute():
	create_custom_fields(get_custom_fields())



def get_custom_fields():
    fields = {
        "Razorpay Settings" : [
            {
                "fieldname" : "sent_email_for_quotation",
                "label" : "Sent Email For Quotation (Payment Link)",
                "fieldtype" : "Check",
                "insert_after" : "redirect_to"
            },
            {
                "fieldname" : "sent_sms_for_quotation",
                "label" : "Sent SMS For Quotation (Payment Link)",
                "fieldtype" : "Check",
                "insert_after" : "sent_email_for_quotation"
            }
        ]
    }

