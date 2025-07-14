# Copyright (c) 2024, Build With Hussain and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import get_url


def get_payment_link_qr_code(doc, amount=None):
	"""
	Generate QR code for payment link of a document
	
	Args:
		doc: The document (Quotation, Sales Order, etc.)
		amount: Optional amount override
	
	Returns:
		dict: Contains 'qr_code' (base64) and 'short_url'
	"""
	try:
		# First, check if a payment link is already stored in the document
		stored_link = None
		if hasattr(doc, 'razorpay_link') and doc.razorpay_link:
			stored_link = doc.razorpay_link
		elif hasattr(doc, 'payment_link') and doc.payment_link:
			stored_link = doc.payment_link
		
		if stored_link:
			# Get the stored payment link from database
			payment_link_doc = frappe.db.get_value(
				"Razorpay Payment Link",
				{"short_url": stored_link, "status": ["in", ["Created", "Partially Paid"]]},
				["name", "short_url", "expire_by"],
				as_dict=True
			)
			
			if payment_link_doc:
				return {
					"short_url": payment_link_doc.short_url,
					"qr_code": get_qr_code_for_url(payment_link_doc.short_url),
					"expire_by": payment_link_doc.expire_by
				}
		
		# If no stored link or link is expired, create new one
		result = frappe.call(
			"razorpay_frappe.razorpay_integration.doctype.razorpay_payment_link.razorpay_payment_link.get_or_create_payment_link_for_document",
			doctype=doc.doctype,
			docname=doc.name,
			amount=amount,
			customer_name=doc.customer_name or doc.party_name or doc.customer or "",
			customer_email=doc.contact_email or doc.customer_email or "",
			customer_contact=doc.contact_mobile or doc.customer_mobile or ""
		)
		
		# If we successfully created / fetched, and doc has razorpay_link field but it is empty, save it.
		if result and result.get("short_url") and hasattr(doc, "razorpay_link") and not getattr(doc, "razorpay_link"):
			doc.db_set("razorpay_link", result["short_url"])
		if result and result.get("short_url") and hasattr(doc, "payment_link") and not getattr(doc, "payment_link"):
			doc.db_set("payment_link", result["short_url"])
		return result
	except Exception as e:
		frappe.log_error(f"Payment link generation failed for {doc.doctype} {doc.name}: {str(e)}")
		return {"qr_code": None, "short_url": None}


def get_payment_qr_code_base64(doc, amount=None):
	"""
	Get QR code as base64 string for use in print formats
	
	Args:
		doc: The document
		amount: Optional amount override
	
	Returns:
		str: Base64 encoded QR code image
	"""
	result = get_payment_link_qr_code(doc, amount)
	return result.get("qr_code") if result else None


def get_payment_link_url(doc, amount=None):
	"""
	Get payment link URL for use in print formats
	
	Args:
		doc: The document
		amount: Optional amount override
	
	Returns:
		str: Payment link URL
	"""
	result = get_payment_link_qr_code(doc, amount)
	return result.get("short_url") if result else None


def get_qr_code(text, scale=512):
	"""
	Generate QR code for any text/URL
	
	Args:
		text: Text or URL to encode
		scale: QR code scale (default: 512 for very high-res QR codes)
	
	Returns:
		str: Base64 encoded QR code image
	"""
	try:
		import pyqrcode
		return pyqrcode.create(text).png_as_base64_str(scale=scale, quiet_zone=4)
	except ImportError:
		frappe.throw("pyqrcode library is required for QR code generation. Please install it.")
	except Exception as e:
		frappe.log_error(f"QR Code generation failed: {str(e)}")
		return None 


@frappe.whitelist()
def test_generate_qr_code():
    """
    Test QR code generation for a simple string and save as PNG for inspection.
    """
    import pyqrcode
    import os
    url = 'https://google.com'
    qr = pyqrcode.create(url)
    output_path = '/www/wwwroot/erp/frappe-bench/test_google_qr.png'
    qr.png(output_path, scale=32, quiet_zone=4)
    print(f'Test QR code saved as {output_path}') 