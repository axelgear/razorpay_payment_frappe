# Copyright (c) 2024, Build With Hussain and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class RazorpaySettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		allow_guest_checkout: DF.Check
		key_id: DF.Data | None
		key_secret: DF.Password | None
		webhook_secret: DF.Password | None
	# end: auto-generated types

	pass


