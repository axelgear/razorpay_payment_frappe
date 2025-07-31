import frappe
from frappe.model.document import Document


class RazorpayPaymentDetail(Document):
    """Razorpay Payment Detail DocType for storing individual payment information."""
    
    def autoname(self):
        """Auto-generate name based on payment_id."""
        if self.payment_id:
            self.name = self.payment_id
        else:
            self.name = frappe.generate_hash("", 10)
    
    def validate(self):
        """Validate the payment detail document."""
        if not self.payment_id:
            frappe.throw("Payment ID is required")
        
        if not self.amount or self.amount <= 0:
            frappe.throw("Amount must be greater than 0")
        
        if not self.currency:
            self.currency = "INR"
    
    def before_insert(self):
        """Set default values before insert."""
        if not self.currency:
            self.currency = "INR" 