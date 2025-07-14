# Copyright (c) 2024, Build With Hussain and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils.data import get_timestamp, add_days, getdate
from frappe.utils import get_url

from razorpay_frappe.utils import get_in_razorpay_money, get_razorpay_client


class RazorpayPaymentLink(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		amount: DF.Currency
		callback_url: DF.Data | None
		currency: DF.Link
		customer_contact: DF.Phone | None
		customer_email: DF.Data | None
		customer_name: DF.Data | None
		expire_by: DF.Date | None
		id: DF.Data | None
		reference_doctype: DF.Link | None
		reference_docname: DF.DynamicLink | None
		short_url: DF.Data | None
		status: DF.Literal[
			"Created", "Partially Paid", "Expired", "Cancelled", "Paid"
		]
		type: DF.Literal["Standard", "UPI"]
	# end: auto-generated types

	def before_insert(self):
		payment_link = self.create_payment_link_on_razorpay()

		self.id = payment_link["id"]
		self.short_url = payment_link["short_url"]
		self.status = frappe.unscrub(payment_link["status"])

	def create_payment_link_on_razorpay(self):
		client = get_razorpay_client()
		return client.payment_link.create(
			{
				"amount": get_in_razorpay_money(self.amount),
				"currency": self.currency,
				"customer": {
					"name": self.customer_name,
					"email": self.customer_email,
					"contact": self.customer_contact,
				},
				"upi_link": self.type == "UPI",
				"expire_by": get_timestamp(self.expire_by),
			}
		)

	@frappe.whitelist()
	def fetch_latest_status(self):
		client = get_razorpay_client()
		payment_link = client.payment_link.fetch(self.id)
		link_status = frappe.unscrub(payment_link["status"])
		if link_status != self.status:
			self.status = link_status
			self.save()

	@frappe.whitelist()
	def get_or_create_payment_link_for_document(doctype, docname, amount=None, customer_name=None, customer_email=None, customer_contact=None):
		"""
		Get existing payment link or create new one for a document
		"""
		# Check if payment link already exists and is valid
		existing_link = frappe.db.get_value(
			"Razorpay Payment Link",
			{
				"reference_doctype": doctype,
				"reference_docname": docname,
				"status": ["in", ["Created", "Partially Paid"]]
			},
			"name"
		)
		
		if existing_link:
			payment_link = frappe.get_doc("Razorpay Payment Link", existing_link)
			return {
				"short_url": payment_link.short_url,
				"qr_code": get_qr_code_for_url(payment_link.short_url)
			}
		
		# Get document details
		doc = frappe.get_doc(doctype, docname)
		
		# Use provided amount or document grand total
		if amount is None:
			amount = doc.grand_total
		
		# Use provided customer details or get from document
		if customer_name is None:
			customer_name = doc.customer_name or doc.party_name or doc.customer or ""
		
		if customer_email is None:
			customer_email = doc.contact_email or doc.customer_email or ""
		
		if customer_contact is None:
			customer_contact = doc.contact_mobile or doc.customer_mobile or ""
		
		# Create new payment link
		payment_link = frappe.new_doc("Razorpay Payment Link")
		payment_link.amount = amount
		payment_link.currency = doc.currency or "INR"
		payment_link.customer_name = customer_name
		payment_link.customer_email = customer_email
		payment_link.customer_contact = customer_contact
		payment_link.type = "UPI"  # Default to UPI for better QR experience
		payment_link.expire_by = add_days(getdate(), 30)  # 30 days expiry
		payment_link.reference_doctype = doctype
		payment_link.reference_docname = docname
		
		payment_link.insert()
		
		return {
			"short_url": payment_link.short_url,
			"qr_code": get_qr_code_for_url(payment_link.short_url)
		}

	@frappe.whitelist()
	def create_payment_link_for_quotation(quotation_name):
		"""
		Create payment link for quotation with matching expiry
		"""
		quotation = frappe.get_doc("Quotation", quotation_name)
		
		# Cancel existing payment links for this quotation
		cancel_existing_payment_links("Quotation", quotation_name)
		
		# Create new payment link
		payment_link = frappe.new_doc("Razorpay Payment Link")
		payment_link.amount = quotation.grand_total
		payment_link.currency = quotation.currency or "INR"
		payment_link.customer_name = quotation.customer_name or quotation.party_name or ""
		payment_link.customer_email = quotation.contact_email or quotation.customer_email or ""
		payment_link.customer_contact = quotation.contact_mobile or quotation.customer_mobile or ""
		payment_link.type = "UPI"
		
		# Set expiry to match quotation expiry
		if quotation.valid_till:
			payment_link.expire_by = quotation.valid_till
		else:
			payment_link.expire_by = add_days(getdate(), 30)
		
		payment_link.reference_doctype = "Quotation"
		payment_link.reference_docname = quotation_name
		
		payment_link.insert()
		
		# Update quotation with payment link
		quotation.db_set("payment_link", payment_link.short_url)
		
		return {
			"short_url": payment_link.short_url,
			"qr_code": get_qr_code_for_url(payment_link.short_url),
			"expire_by": payment_link.expire_by
		}

	@frappe.whitelist()
	def create_payment_link_for_sales_order(sales_order_name):
		"""
		Create payment link for sales order
		"""
		sales_order = frappe.get_doc("Sales Order", sales_order_name)
		
		# Cancel existing payment links for this sales order
		cancel_existing_payment_links("Sales Order", sales_order_name)
		
		# Create new payment link
		payment_link = frappe.new_doc("Razorpay Payment Link")
		payment_link.amount = sales_order.grand_total
		payment_link.currency = sales_order.currency or "INR"
		payment_link.customer_name = sales_order.customer_name or sales_order.party_name or ""
		payment_link.customer_email = sales_order.contact_email or sales_order.customer_email or ""
		payment_link.customer_contact = sales_order.contact_mobile or sales_order.customer_mobile or ""
		payment_link.type = "UPI"
		payment_link.expire_by = add_days(getdate(), 30)  # 30 days for sales orders
		payment_link.reference_doctype = "Sales Order"
		payment_link.reference_docname = sales_order_name
		
		payment_link.insert()
		
		# Update sales order with payment link
		sales_order.db_set("payment_link", payment_link.short_url)
		
		return {
			"short_url": payment_link.short_url,
			"qr_code": get_qr_code_for_url(payment_link.short_url),
			"expire_by": payment_link.expire_by
		}


def cancel_existing_payment_links(doctype, docname):
	"""
	Cancel existing payment links for a document
	"""
	existing_links = frappe.get_all(
		"Razorpay Payment Link",
		filters={
			"reference_doctype": doctype,
			"reference_docname": docname,
			"status": ["in", ["Created", "Partially Paid"]]
		},
		fields=["name"]
	)
	
	for link in existing_links:
		try:
			payment_link = frappe.get_doc("Razorpay Payment Link", link.name)
			payment_link.status = "Cancelled"
			payment_link.save()
		except Exception as e:
			frappe.log_error(f"Failed to cancel payment link {link.name}: {str(e)}")


def get_qr_code_for_url(url, scale=512):
	"""
	Generate QR code for a URL with very high resolution for best readability
	"""
	try:
		import pyqrcode
		return pyqrcode.create(url).png_as_base64_str(scale=scale, quiet_zone=4)
	except ImportError:
		frappe.throw("pyqrcode library is required for QR code generation. Please install it.")
	except Exception as e:
		frappe.log_error(f"QR Code generation failed: {str(e)}")
		return None
