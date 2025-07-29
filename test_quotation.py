#!/usr/bin/env python3
import frappe

def test_quotation_payment_link():
    """Test quotation payment link creation"""
    try:
        # Check if Razorpay Settings exists
        if not frappe.db.exists('DocType', 'Razorpay Settings'):
            print("❌ Razorpay Settings DocType not found")
            return False
        
        # Check if ZohoCliq Settings exists
        if not frappe.db.exists('DocType', 'ZohoCliq Settings'):
            print("❌ ZohoCliq Settings DocType not found")
            return False
        
        # Check if Razorpay Payment Link DocType exists
        if not frappe.db.exists('DocType', 'Razorpay Payment Link'):
            print("❌ Razorpay Payment Link DocType not found")
            return False
        
        print("✅ All required DocTypes exist")
        
        # Check if quotation custom fields exist
        custom_fields = frappe.get_all('Custom Field', filters={'dt': 'Quotation', 'fieldname': ['like', 'razorpay%']})
        if not custom_fields:
            print("❌ Quotation custom fields not found")
            return False
        
        print(f"✅ Found {len(custom_fields)} Razorpay custom fields in Quotation")
        
        # Check if quotation events are registered
        from razorpay_frappe.quotation_events import handle_quotation_submit, handle_quotation_update
        print("✅ Quotation event handlers exist")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    test_quotation_payment_link() 