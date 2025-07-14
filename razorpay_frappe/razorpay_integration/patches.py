import frappe

def add_razorpay_fields_to_quotation():
    """
    Add Razorpay integration fields to Quotation DocType.
    """
    from frappe.custom.doctype.custom_field.custom_field import create_custom_field

    fields = [
        dict(
            fieldname='razorpay_link',
            label='Razorpay Payment Link',
            fieldtype='Data',
            insert_after='valid_till',
            read_only=1,
            description='Auto-generated Razorpay payment link',
        ),
        dict(
            fieldname='razorpay_expiry',
            label='Razorpay Link Expiry',
            fieldtype='Date',
            insert_after='razorpay_link',
            read_only=1,
            description='Expiry date of the Razorpay payment link',
        ),
        dict(
            fieldname='razorpay_payment_status',
            label='Razorpay Payment Status',
            fieldtype='Select',
            options='Created\nPaid\nExpired\nCancelled',
            insert_after='razorpay_expiry',
            read_only=1,
            description='Status of the Razorpay payment link',
        ),
        dict(
            fieldname='razorpay_payment_id',
            label='Razorpay Payment ID',
            fieldtype='Data',
            insert_after='razorpay_payment_status',
            read_only=1,
            description='Razorpay Payment ID (if paid)',
        ),
    ]

    for field in fields:
        create_custom_field('Quotation', field)

def add_razorpay_fields_to_sales_order():
    from frappe.custom.doctype.custom_field.custom_field import create_custom_field
    fields = [
        dict(fieldname='razorpay_link', label='Razorpay Payment Link', fieldtype='Data', insert_after='valid_till', read_only=1),
        dict(fieldname='razorpay_expiry', label='Razorpay Link Expiry', fieldtype='Date', insert_after='razorpay_link', read_only=1),
        dict(fieldname='razorpay_payment_status', label='Razorpay Payment Status', fieldtype='Select', options='Created\nPaid\nExpired\nCancelled', insert_after='razorpay_expiry', read_only=1),
        dict(fieldname='razorpay_payment_id', label='Razorpay Payment ID', fieldtype='Data', insert_after='razorpay_payment_status', read_only=1),
    ]
    for field in fields:
        create_custom_field('Sales Order', field)

def add_razorpay_fields_to_sales_invoice():
    from frappe.custom.doctype.custom_field.custom_field import create_custom_field
    fields = [
        dict(fieldname='razorpay_link', label='Razorpay Payment Link', fieldtype='Data', insert_after='due_date', read_only=1),
        dict(fieldname='razorpay_expiry', label='Razorpay Link Expiry', fieldtype='Date', insert_after='razorpay_link', read_only=1),
        dict(fieldname='razorpay_payment_status', label='Razorpay Payment Status', fieldtype='Select', options='Created\nPaid\nExpired\nCancelled', insert_after='razorpay_expiry', read_only=1),
        dict(fieldname='razorpay_payment_id', label='Razorpay Payment ID', fieldtype='Data', insert_after='razorpay_payment_status', read_only=1),
    ]
    for field in fields:
        create_custom_field('Sales Invoice', field)

def unhide_razorpay_fields():
    for doctype in ["Quotation", "Sales Order", "Sales Invoice"]:
        for field in ["razorpay_link", "razorpay_expiry", "razorpay_payment_status", "razorpay_payment_id"]:
            cf = frappe.db.get_value("Custom Field", {"dt": doctype, "fieldname": field})
            if cf:
                frappe.db.set_value("Custom Field", {"dt": doctype, "fieldname": field}, "hidden", 0) 