import frappe
from frappe.model.document import Document


class RazorpayVirtualAccountReceiver(Document):
	"""Child table to store receiver details returned from Razorpay Virtual
	Account API. No custom behaviour required at the moment."""

	pass 