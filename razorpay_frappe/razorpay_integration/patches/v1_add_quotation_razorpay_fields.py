import frappe

def execute():
    """Add Razorpay fields to Quotation DocType"""
    
    # Check if custom fields already exist
    if frappe.db.exists("Custom Field", "Quotation-razorpay_payment_link"):
        return
    
    # Add Razorpay section
    frappe.get_doc({
        "doctype": "Custom Field",
        "dt": "Quotation",
        "fieldname": "section_break_razorpay",
        "fieldtype": "Section Break",
        "label": "Razorpay",
        "collapsible": 1,
        "collapsible_depends_on": "eval:doc.razorpay_payment_link"
    }).insert()
    
    # Add Payment Link field
    frappe.get_doc({
        "doctype": "Custom Field",
        "dt": "Quotation",
        "fieldname": "razorpay_payment_link",
        "fieldtype": "Data",
        "label": "Payment Link",
        "read_only": 1,
        "description": "Razorpay payment link URL"
    }).insert()
    
    # Add Payment Link ID field
    frappe.get_doc({
        "doctype": "Custom Field",
        "dt": "Quotation",
        "fieldname": "razorpay_payment_link_id",
        "fieldtype": "Data",
        "label": "Payment Link ID",
        "read_only": 1,
        "hidden": 1
    }).insert()
    
    # Add QR Code field
    frappe.get_doc({
        "doctype": "Custom Field",
        "dt": "Quotation",
        "fieldname": "razorpay_qr",
        "fieldtype": "Attach",
        "label": "QR Code",
        "read_only": 1,
        "description": "QR code for payment"
    }).insert()
    
    # Add Expiry field
    frappe.get_doc({
        "doctype": "Custom Field",
        "dt": "Quotation",
        "fieldname": "razorpay_expiry",
        "fieldtype": "Datetime",
        "label": "Expiry",
        "read_only": 1,
        "description": "Payment link expiry date"
    }).insert()
    
    # Add Column Break
    frappe.get_doc({
        "doctype": "Custom Field",
        "dt": "Quotation",
        "fieldname": "column_break_razorpay_2",
        "fieldtype": "Column Break"
    }).insert()
    
    # Add Payment Status field
    frappe.get_doc({
        "doctype": "Custom Field",
        "dt": "Quotation",
        "fieldname": "razorpay_status",
        "fieldtype": "Select",
        "label": "Payment Status",
        "options": "Pending\nPaid\nFailed\nExpired",
        "read_only": 1,
        "default": "Pending"
    }).insert()
    
    # Add Amount Paid field
    frappe.get_doc({
        "doctype": "Custom Field",
        "dt": "Quotation",
        "fieldname": "razorpay_amount_paid",
        "fieldtype": "Currency",
        "label": "Amount Paid",
        "read_only": 1,
        "description": "Amount received via Razorpay"
    }).insert()
    
    # Add Payment ID field
    frappe.get_doc({
        "doctype": "Custom Field",
        "dt": "Quotation",
        "fieldname": "razorpay_payment_id",
        "fieldtype": "Data",
        "label": "Payment ID",
        "read_only": 1,
        "hidden": 1,
        "description": "Razorpay payment ID"
    }).insert()
    
    frappe.db.commit() 