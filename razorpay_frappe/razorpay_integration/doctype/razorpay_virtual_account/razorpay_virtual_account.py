import frappe
from frappe.model.document import Document
from frappe.utils import nowdate, get_timestamp

from razorpay_frappe.utils import get_razorpay_client, post_to_zohocliq


class RazorpayVirtualAccount(Document):
	"""DocType controller for *Razorpay Virtual Account*.

	This is a streamlined port of the logic present in the archived app. Some
	behaviour (allowed payers / receivers mutation) is trimmed for brevity but can
	be extended later.
	"""

	def validate(self):
		if not self.customer:
			frappe.throw("Customer is mandatory.")

		if not self.customer_razorpay_id:
			frappe.throw(
				"Customer Razorpay ID is missing. Ensure the Customer has a valid Razorpay ID."
			)

		if self.project and not frappe.db.exists("Project", self.project):
			frappe.throw("Invalid Project reference.")

		if self.sales_order and not frappe.db.exists("Sales Order", self.sales_order):
			frappe.throw("Invalid Sales Order reference.")

		if self.quotation and not frappe.db.exists("Quotation", self.quotation):
			frappe.throw("Invalid Quotation reference.")

		if self.close_by and self.close_by < nowdate():
			frappe.throw("Close By date must be in the future.")

	def on_submit(self):
		self.create_virtual_account()

	# ------------------------------------------------------------
	# Razorpay helpers
	# ------------------------------------------------------------

	def create_virtual_account(self):
		client = get_razorpay_client()
		settings = frappe.get_single("Razorpay Settings")
		customer = frappe.get_doc("Customer", self.customer)

		va_data = {
			"receivers": {"types": ["bank_account"]},
			"description": self.description or f"Virtual Account for {customer.customer_name}",
			"customer_id": self.customer_razorpay_id,
			"notes": {
				"customer": self.customer,
				"project": self.project or "",
				"sales_order": self.sales_order or "",
				"quotation": self.quotation or "",
			},
		}

		if self.close_by:
			va_data["close_by"] = int(get_timestamp(self.close_by))
		if self.amount_expected:
			va_data["amount_expected"] = int(self.amount_expected * 100)

		try:
			va = client.virtual_account.create(data=va_data)
			self.virtual_account_id = f"{settings.virtual_account_prefix}{va['id']}"
			self.status = va.get("status")
			self.receivers = va.get("receivers", [])
			self.save()

			# Notification
			if settings.zohocliq_enabled and settings.zohocliq_webhook_url:
				post_to_zohocliq(
					f"New Virtual Account Created: {self.virtual_account_id} for Customer {self.customer}",
					settings.zohocliq_webhook_url,
				)
		except Exception as e:
			frappe.throw(f"Failed to create virtual account: {str(e)}") 