import frappe
from frappe.model.document import Document

class RazorpaySettlement(Document):
    def onload(self):
        """Load settlement details from Razorpay API"""
        if self.settlement_id and not self.amount:
            self.load_settlement_details()
    
    def load_settlement_details(self):
        """Load settlement details from Razorpay"""
        try:
            from .utils import fetch_settlement
            
            result = fetch_settlement(self.settlement_id)
            if result.get("success"):
                settlement = result["settlement"]
                
                # Update fields
                self.entity = settlement.get("entity")
                self.amount = settlement.get("amount")
                self.currency = settlement.get("currency")
                self.status = settlement.get("status")
                self.created_at = frappe.utils.get_datetime(settlement.get("created_at"))
                self.updated_at = frappe.utils.get_datetime(settlement.get("updated_at"))
                self.fee = settlement.get("fee")
                self.tax = settlement.get("tax")
                self.utr = settlement.get("utr")
                self.settlement_date = frappe.utils.get_date(settlement.get("settlement_date")) if settlement.get("settlement_date") else None
                self.on_hold = settlement.get("on_hold", False)
                self.on_hold_until = frappe.utils.get_datetime(settlement.get("on_hold_until")) if settlement.get("on_hold_until") else None
                self.description = settlement.get("description")
                self.notes = frappe.as_json(settlement.get("notes"))
                
                self.save()
                
        except Exception as e:
            frappe.log_error(f"Failed to load settlement details: {str(e)}", "Razorpay Settlement Load Error")
    
    def reconcile_settlement(self):
        """Reconcile this settlement"""
        try:
            from .utils import settlement_recon
            
            result = settlement_recon(self.settlement_id)
            if result.get("success"):
                self.reconciliation_status = "reconciled"
                self.reconciled_at = frappe.utils.now()
                self.reconciled_by = frappe.session.user
                self.save()
                
                frappe.msgprint("Settlement reconciled successfully!")
            else:
                frappe.throw(f"Failed to reconcile settlement: {result.get('error')}")
                
        except Exception as e:
            frappe.log_error(f"Failed to reconcile settlement: {str(e)}", "Razorpay Settlement Recon Error")
            frappe.throw(f"Failed to reconcile settlement: {str(e)}")
    
    def fetch_payment_entries(self):
        """Fetch payment entries for this settlement"""
        try:
            from .utils import fetch_payment_link_details
            
            # Get payment links associated with this settlement
            payment_links = frappe.get_all(
                "Razorpay Payment Link",
                filters={"settlement_id": self.settlement_id},
                fields=["payment_link_id"]
            )
            
            for pl in payment_links:
                if pl.payment_link_id:
                    result = fetch_payment_link_details(pl.payment_link_id)
                    if result.get("success") and result.get("payments"):
                        for payment in result["payments"]:
                            # Create payment entry record
                            payment_entry = frappe.new_doc("Razorpay Settlement Payment Entry")
                            payment_entry.parent = self.name
                            payment_entry.parentfield = "payment_entries"
                            payment_entry.parenttype = "Razorpay Settlement"
                            payment_entry.payment_id = payment["payment_id"]
                            payment_entry.amount = payment["amount"]
                            payment_entry.currency = payment["currency"]
                            payment_entry.status = payment["status"]
                            payment_entry.method = payment["method"]
                            payment_entry.created_at = frappe.utils.get_datetime(payment["created_at"])
                            payment_entry.captured_at = frappe.utils.get_datetime(payment["captured_at"]) if payment.get("captured_at") else None
                            payment_entry.description = payment["description"]
                            payment_entry.email = payment["email"]
                            payment_entry.contact = payment["contact"]
                            payment_entry.notes = frappe.as_json(payment["notes"])
                            
                            # Try to link to ERPNext documents
                            if payment.get("notes"):
                                notes = payment["notes"]
                                if notes.get("quotation_id"):
                                    payment_entry.quotation = notes["quotation_id"]
                                if notes.get("customer"):
                                    payment_entry.customer = notes["customer"]
                            
                            payment_entry.insert()
            
            frappe.msgprint("Payment entries fetched successfully!")
            
        except Exception as e:
            frappe.log_error(f"Failed to fetch payment entries: {str(e)}", "Razorpay Settlement Payment Error")
            frappe.throw(f"Failed to fetch payment entries: {str(e)}") 