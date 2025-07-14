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
	"""Add payment link field to print format if not exists"""
	
	# Check if field exists in Quotation print format
	quotation_print_format = frappe.db.get_value("Print Format", "Quotation")
	if quotation_print_format:
		format_doc = frappe.get_doc("Print Format", "Quotation")
		field_exists = any(field.fieldname == "payment_link" for field in format_doc.fields)
		
		if not field_exists:
			format_doc.append("fields", {
				"fieldname": "payment_link",
				"label": "Payment Link",
				"fieldtype": "Data",
				"hidden": 1
			})
			format_doc.save()
			frappe.msgprint("Added payment_link field to Quotation print format")
	
	# Check if field exists in Sales Order print format
	sales_order_print_format = frappe.db.get_value("Print Format", "Sales Order")
	if sales_order_print_format:
		format_doc = frappe.get_doc("Print Format", "Sales Order")
		field_exists = any(field.fieldname == "payment_link" for field in format_doc.fields)
		
		if not field_exists:
			format_doc.append("fields", {
				"fieldname": "payment_link",
				"label": "Payment Link",
				"fieldtype": "Data",
				"hidden": 1
			})
			format_doc.save()
			frappe.msgprint("Added payment_link field to Sales Order print format") 