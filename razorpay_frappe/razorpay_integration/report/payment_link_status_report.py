import frappe

def execute(filters=None):
    columns = [
        {"label": "Quotation", "fieldname": "name", "fieldtype": "Link", "options": "Quotation", "width": 140},
        {"label": "Customer", "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 180},
        {"label": "Grand Total", "fieldname": "grand_total", "fieldtype": "Currency", "width": 120},
        {"label": "Razorpay Link", "fieldname": "razorpay_link", "fieldtype": "Data", "width": 220},
        {"label": "Status", "fieldname": "razorpay_payment_status", "fieldtype": "Select", "options": "Created\nPaid\nExpired\nCancelled", "width": 100},
        {"label": "Expiry", "fieldname": "razorpay_expiry", "fieldtype": "Date", "width": 110},
        {"label": "Payment ID", "fieldname": "razorpay_payment_id", "fieldtype": "Data", "width": 180},
    ]
    conditions = []
    values = {}
    if filters and filters.get('razorpay_payment_status'):
        conditions.append("razorpay_payment_status = %(status)s")
        values['status'] = filters['razorpay_payment_status']
    data = frappe.db.get_all(
        "Quotation",
        fields=["name", "customer", "grand_total", "razorpay_link", "razorpay_payment_status", "razorpay_expiry", "razorpay_payment_id"],
        filters=conditions,
        order_by="creation desc"
    )
    return columns, data 