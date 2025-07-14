# Copyright (c) 2024, Build With Hussain and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import get_url


def on_quotation_submit(doc, method):
	"""
	Generate payment link when quotation is submitted
	"""
	try:
		if doc.grand_total > 0:
			result = frappe.call(
				"razorpay_frappe.razorpay_integration.doctype.razorpay_payment_link.razorpay_payment_link.create_payment_link_for_quotation",
				quotation_name=doc.name
			)
			
			if result and result.get("short_url"):
				frappe.msgprint(
					_("Payment link generated successfully! Link: {0}").format(result.get("short_url")),
					indicator="green"
				)
			else:
				frappe.msgprint(
					_("Payment link generation failed. Please check Razorpay settings."),
					indicator="red"
				)
		else:
			frappe.msgprint(
				_("Payment link not generated - quotation amount is zero."),
				indicator="orange"
			)
			
	except Exception as e:
		frappe.log_error(f"Payment link generation failed for Quotation {doc.name}: {str(e)}")
		frappe.msgprint(
			_("Payment link generation failed. Please check logs for details."),
			indicator="red"
		)


def on_quotation_amend(doc, method):
	"""
	Generate new payment link when quotation is amended/revised
	"""
	try:
		if doc.grand_total > 0:
			result = frappe.call(
				"razorpay_frappe.razorpay_integration.doctype.razorpay_payment_link.razorpay_payment_link.create_payment_link_for_quotation",
				quotation_name=doc.name
			)
			
			if result and result.get("short_url"):
				frappe.msgprint(
					_("New payment link generated for revised quotation! Link: {0}").format(result.get("short_url")),
					indicator="green"
				)
			else:
				frappe.msgprint(
					_("Payment link generation failed for revised quotation. Please check Razorpay settings."),
					indicator="red"
				)
		else:
			frappe.msgprint(
				_("Payment link not generated - revised quotation amount is zero."),
				indicator="orange"
			)
			
	except Exception as e:
		frappe.log_error(f"Payment link generation failed for revised Quotation {doc.name}: {str(e)}")
		frappe.msgprint(
			_("Payment link generation failed for revised quotation. Please check logs for details."),
			indicator="red"
		)


def on_sales_order_submit(doc, method):
	"""
	Generate payment link when sales order is submitted
	"""
	try:
		if doc.grand_total > 0:
			result = frappe.call(
				"razorpay_frappe.razorpay_integration.doctype.razorpay_payment_link.razorpay_payment_link.create_payment_link_for_sales_order",
				sales_order_name=doc.name
			)
			
			if result and result.get("short_url"):
				frappe.msgprint(
					_("Payment link generated successfully! Link: {0}").format(result.get("short_url")),
					indicator="green"
				)
			else:
				frappe.msgprint(
					_("Payment link generation failed. Please check Razorpay settings."),
					indicator="red"
				)
		else:
			frappe.msgprint(
				_("Payment link not generated - sales order amount is zero."),
				indicator="orange"
			)
			
	except Exception as e:
		frappe.log_error(f"Payment link generation failed for Sales Order {doc.name}: {str(e)}")
		frappe.msgprint(
			_("Payment link generation failed. Please check logs for details."),
			indicator="red"
		)


def on_sales_order_amend(doc, method):
	"""
	Generate new payment link when sales order is amended
	"""
	try:
		if doc.grand_total > 0:
			result = frappe.call(
				"razorpay_frappe.razorpay_integration.doctype.razorpay_payment_link.razorpay_payment_link.create_payment_link_for_sales_order",
				sales_order_name=doc.name
			)
			
			if result and result.get("short_url"):
				frappe.msgprint(
					_("New payment link generated for amended sales order! Link: {0}").format(result.get("short_url")),
					indicator="green"
				)
			else:
				frappe.msgprint(
					_("Payment link generation failed for amended sales order. Please check Razorpay settings."),
					indicator="red"
				)
		else:
			frappe.msgprint(
				_("Payment link not generated - amended sales order amount is zero."),
				indicator="orange"
			)
			
	except Exception as e:
		frappe.log_error(f"Payment link generation failed for amended Sales Order {doc.name}: {str(e)}")
		frappe.msgprint(
			_("Payment link generation failed for amended sales order. Please check logs for details."),
			indicator="red"
		) 