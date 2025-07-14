#!/usr/bin/env python3
"""
Test script for payment link generation functionality
"""

import frappe
import sys
import os

# Add the bench directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

def test_payment_link_generation():
    """Test payment link generation for a sample document"""
    
    try:
        # Test with a sample quotation
        sample_quotation = {
            "doctype": "Quotation",
            "name": "TEST-QTN-001",
            "grand_total": 1000.00,
            "currency": "INR",
            "customer_name": "Test Customer",
            "customer_email": "test@example.com",
            "customer_mobile": "9876543210"
        }
        
        print("Testing payment link generation...")
        
        # Test the whitelisted method
        result = frappe.call(
            "razorpay_frappe.razorpay_integration.doctype.razorpay_payment_link.razorpay_payment_link.get_or_create_payment_link_for_document",
            doctype="Quotation",
            docname="TEST-QTN-001",
            amount=1000.00,
            customer_name="Test Customer",
            customer_email="test@example.com",
            customer_contact="9876543210"
        )
        
        print("✅ Payment link generation successful!")
        print(f"Short URL: {result.get('short_url', 'N/A')}")
        print(f"QR Code generated: {'Yes' if result.get('qr_code') else 'No'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Payment link generation failed: {str(e)}")
        return False

def test_qr_code_generation():
    """Test QR code generation"""
    
    try:
        from razorpay_frappe.razorpay_integration.jinja_functions import get_qr_code
        
        test_text = "https://example.com"
        qr_code = get_qr_code(test_text)
        
        if qr_code:
            print("✅ QR code generation successful!")
            return True
        else:
            print("❌ QR code generation failed")
            return False
            
    except Exception as e:
        print(f"❌ QR code generation failed: {str(e)}")
        return False

def test_jinja_functions():
    """Test Jinja functions"""
    
    try:
        from razorpay_frappe.razorpay_integration.jinja_functions import get_qr_code
        
        # Test basic QR generation
        qr_code = get_qr_code("test")
        if qr_code:
            print("✅ Jinja functions working correctly!")
            return True
        else:
            print("❌ Jinja functions not working")
            return False
            
    except Exception as e:
        print(f"❌ Jinja functions test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Payment Link Generation System")
    print("=" * 50)
    
    # Initialize Frappe
    frappe.init(site="frontend")
    frappe.connect()
    
    try:
        # Run tests
        test1 = test_qr_code_generation()
        test2 = test_jinja_functions()
        test3 = test_payment_link_generation()
        
        print("\n" + "=" * 50)
        print("📊 Test Results:")
        print(f"QR Code Generation: {'✅ PASS' if test1 else '❌ FAIL'}")
        print(f"Jinja Functions: {'✅ PASS' if test2 else '❌ FAIL'}")
        print(f"Payment Link Generation: {'✅ PASS' if test3 else '❌ FAIL'}")
        
        if all([test1, test2, test3]):
            print("\n🎉 All tests passed! The system is ready to use.")
        else:
            print("\n⚠️  Some tests failed. Please check the configuration.")
            
    except Exception as e:
        print(f"❌ Test execution failed: {str(e)}")
    
    finally:
        frappe.destroy() 