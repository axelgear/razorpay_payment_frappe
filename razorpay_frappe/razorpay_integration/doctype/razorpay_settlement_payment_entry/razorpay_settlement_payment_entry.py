import frappe
from frappe.model.document import Document

class RazorpaySettlementPaymentEntry(Document):
    def onload(self):
        """Load payment details from Razorpay API"""
        if self.payment_id and not self.amount:
            self.load_payment_details()
    
    def load_payment_details(self):
        """Load payment details from Razorpay"""
        try:
            from .utils import get_razorpay_client
            
            client = get_razorpay_client()
            payment = client.payment.fetch(self.payment_id)
            
            # Update fields
            self.amount = payment.get("amount") / 100 if payment.get("amount") else 0
            self.currency = payment.get("currency")
            self.status = payment.get("status")
            self.method = payment.get("method")
            self.created_at = frappe.utils.get_datetime(payment.get("created_at"))
            self.captured_at = frappe.utils.get_datetime(payment.get("captured_at")) if payment.get("captured_at") else None
            self.description = payment.get("description")
            self.email = payment.get("email")
            self.contact = payment.get("contact")
            self.notes = frappe.as_json(payment.get("notes"))
            
            # Try to link to ERPNext documents
            if payment.get("notes"):
                notes = payment["notes"]
                if notes.get("quotation_id"):
                    self.quotation = notes["quotation_id"]
                if notes.get("customer"):
                    self.customer = notes["customer"]
            
            self.save()
            
        except Exception as e:
            frappe.log_error(f"Failed to load payment details: {str(e)}", "Razorpay Payment Load Error")
    
    def reconcile_payment(self):
        """Reconcile this payment entry"""
        try:
            # Find corresponding Payment Entry in ERPNext
            payment_entries = frappe.get_all(
                "Payment Entry",
                filters={
                    "razorpay_payment_id": self.payment_id
                },
                fields=["name", "docstatus"]
            )
            
            if payment_entries:
                payment_entry = payment_entries[0]
                if payment_entry["docstatus"] == 1:  # Submitted
                    self.reconciliation_status = "reconciled"
                    self.payment_entry = payment_entry["name"]
                    self.reconciled_at = frappe.utils.now()
                    self.reconciled_by = frappe.session.user
                    self.save()
                    
                    frappe.msgprint("Payment reconciled successfully!")
                else:
                    frappe.throw("Payment Entry is not submitted")
            else:
                frappe.throw("No corresponding Payment Entry found")
                
        except Exception as e:
            frappe.log_error(f"Failed to reconcile payment: {str(e)}", "Razorpay Payment Recon Error")
            frappe.throw(f"Failed to reconcile payment: {str(e)}")
    
    def create_payment_entry(self):
        """Create Payment Entry in ERPNext"""
        try:
            if not self.payment_id:
                frappe.throw("Payment ID is required")
            
            # Load payment details first
            self.load_payment_details()
            
            # Create Payment Entry
            payment_entry = frappe.new_doc("Payment Entry")
            payment_entry.payment_type = "Receive"
            payment_entry.party_type = "Customer"
            payment_entry.party = self.customer or "Unknown"
            payment_entry.paid_amount = self.amount
            payment_entry.received_amount = self.amount
            payment_entry.paid_from = frappe.get_value("Company", {"default_company": 1}, "default_receivable_account")
            payment_entry.paid_to = frappe.get_value("Company", {"default_company": 1}, "default_receivable_account")
            payment_entry.reference_no = self.payment_id
            payment_entry.reference_date = frappe.utils.getdate()
            payment_entry.razorpay_payment_id = self.payment_id
            payment_entry.razorpay_settlement_payment_entry = self.name
            
            # Add reference to quotation if available
            if self.quotation:
                payment_entry.reference_doc_type = "Quotation"
                payment_entry.reference_doc = self.quotation
            
            payment_entry.insert()
            
            # Update this record
            self.payment_entry = payment_entry.name
            self.save()
            
            frappe.msgprint(f"Payment Entry {payment_entry.name} created successfully!")
            
        except Exception as e:
            frappe.log_error(f"Failed to create payment entry: {str(e)}", "Razorpay Payment Entry Error")
            frappe.throw(f"Failed to create payment entry: {str(e)}") 