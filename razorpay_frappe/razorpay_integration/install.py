# Copyright (c) 2024, Build With Hussain and contributors
# For license information, please see license.txt

import frappe
import subprocess
import sys


def install_pyqrcode():
	"""Install pyqrcode dependency if not already installed"""
	try:
		import pyqrcode
		frappe.msgprint("pyqrcode is already installed")
	except ImportError:
		try:
			subprocess.check_call([sys.executable, "-m", "pip", "install", "pyqrcode"])
			frappe.msgprint("pyqrcode installed successfully")
		except subprocess.CalledProcessError:
			frappe.throw("Failed to install pyqrcode. Please install it manually: pip install pyqrcode")


def after_install():
	"""Run after app installation"""
	install_pyqrcode()
	
	# Create custom field for Quotation and Sales Order if not exists
	create_custom_fields()


def create_custom_fields():
	"""Create custom fields for payment link tracking"""
	
	# Check if custom field already exists for Quotation
	if not frappe.db.exists("Custom Field", "Quotation-payment_link"):
		frappe.get_doc({
			"doctype": "Custom Field",
			"dt": "Quotation",
			"fieldname": "payment_link",
			"label": "Payment Link",
			"fieldtype": "Data",
			"read_only": 1,
			"hidden": 1,
			"description": "Razorpay payment link for this quotation"
		}).insert()
		frappe.msgprint("Created payment_link field for Quotation")
	
	# Check if custom field already exists for Sales Order
	if not frappe.db.exists("Custom Field", "Sales Order-payment_link"):
		frappe.get_doc({
			"doctype": "Custom Field",
			"dt": "Sales Order",
			"fieldname": "payment_link",
			"label": "Payment Link",
			"fieldtype": "Data",
			"read_only": 1,
			"hidden": 1,
			"description": "Razorpay payment link for this sales order"
		}).insert()
		frappe.msgprint("Created payment_link field for Sales Order")
	
	# Add payment link field to print format
	add_payment_link_to_print_format()


def add_payment_link_to_print_format():
    """Safely attempt to add the payment_link column to standard Quotation and Sales Order print formats.
    
    In Frappe v15 the Print Format DocType structure changed and the legacy `fields` child
    table is no longer present. Attempting to access it raises an `AttributeError`, which
    currently breaks the installation of the app. Until a version-specific implementation
    is added, gracefully skip this step if the expected attribute is missing so that the
    rest of the installation can complete successfully.
    """
    
    # Fetch standard print formats for Quotation and Sales Order (if any)
    for doctype in ("Quotation", "Sales Order"):
        pf_name = frappe.db.get_value("Print Format", {"doc_type": doctype, "standard": "Yes"})
        if not pf_name:
            # No standard print format found – nothing to update
            continue

        format_doc = frappe.get_doc("Print Format", pf_name)

        # Newer Frappe versions don't expose a `fields` child table. Exit early if not found.
        if not hasattr(format_doc, "fields") or format_doc.fields is None:
            # Skip silently; log for reference
            frappe.logger().debug(
                "[razorpay_frappe] Skipping payment_link field injection for Print Format %s – incompatible structure",
                pf_name,
            )
            continue

        # Check if the field already exists
        field_exists = any(getattr(field, "fieldname", None) == "payment_link" for field in format_doc.fields)
        if field_exists:
            continue

        # Append a hidden data field so the link can be rendered if desired
        format_doc.append("fields", {
            "fieldname": "payment_link",
            "label": "Payment Link",
            "fieldtype": "Data",
            "hidden": 1,
        })
        format_doc.save()
        frappe.msgprint(f"Added payment_link field to {doctype} print format ({pf_name})") 