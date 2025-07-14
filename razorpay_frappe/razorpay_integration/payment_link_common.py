import frappe
from frappe.utils import getdate, add_days
from razorpay_frappe.razorpay_integration.jinja_functions import get_payment_link_qr_code

def create_or_update_razorpay_link(doc):
    payment_data = get_payment_link_qr_code(doc)
    if payment_data and payment_data.get('short_url'):
        # Save link in both legacy 'payment_link' and new 'razorpay_link' fields if they exist
        if hasattr(doc, 'razorpay_link'):
            doc.db_set('razorpay_link', payment_data['short_url'])
        if hasattr(doc, 'payment_link'):
            doc.db_set('payment_link', payment_data['short_url'])
        expiry = payment_data.get('expire_by') or add_days(getdate(), 30)
        doc.db_set('razorpay_expiry', expiry)
        doc.db_set('razorpay_payment_status', 'Created')
    else:
        if hasattr(doc, 'razorpay_link'):
            doc.db_set('razorpay_link', None)
        if hasattr(doc, 'payment_link'):
            doc.db_set('payment_link', None)
        doc.db_set('razorpay_expiry', None)
        doc.db_set('razorpay_payment_status', None)

    # Fallback: if still no link, create Razorpay Payment Link record manually
    if not doc.get('razorpay_link') and doc.grand_total:
        try:
            from frappe.utils.data import add_days, getdate
            payment_link = frappe.new_doc("Razorpay Payment Link")
            payment_link.amount = doc.grand_total
            payment_link.currency = getattr(doc, 'currency', None) or "INR"
            payment_link.customer_name = getattr(doc, 'customer_name', None) or getattr(doc, 'party_name', None) or getattr(doc, 'customer', None) or ""
            payment_link.customer_email = getattr(doc, 'contact_email', None) or getattr(doc, 'customer_email', None) or ""
            payment_link.customer_contact = getattr(doc, 'contact_mobile', None) or getattr(doc, 'customer_mobile', None) or ""
            payment_link.type = "Standard"
            # expiry
            expiry = getattr(doc, 'valid_till', None) or add_days(getdate(), 30)
            payment_link.expire_by = expiry
            payment_link.reference_doctype = doc.doctype
            payment_link.reference_docname = doc.name
            payment_link.insert()

            # update doc fields
            link_url = payment_link.short_url
            if hasattr(doc, 'razorpay_link'):
                doc.db_set('razorpay_link', link_url)
                doc.razorpay_link = link_url
            if hasattr(doc, 'payment_link'):
                doc.db_set('payment_link', link_url)
                doc.payment_link = link_url
            doc.db_set('razorpay_expiry', expiry)
            doc.db_set('razorpay_payment_status', 'Created')
            doc.razorpay_expiry = expiry
            doc.razorpay_payment_status = 'Created'
        except Exception as e:
            frappe.log_error(title="Razorpay Fallback Link Generation Failed", message=str(e))

def on_submit(doc, method=None):
    create_or_update_razorpay_link(doc)

@frappe.whitelist()
def regenerate_razorpay_link(doctype, docname):
    doc = frappe.get_doc(doctype, docname)
    debug_info = {}
    try:
        payment_data = create_or_update_razorpay_link(doc)
        debug_info['payment_data'] = payment_data
    except Exception as e:
        debug_info['exception'] = str(e)
        frappe.log_error(title="Razorpay regenerate debug", message=frappe.get_traceback())

    return {
        'razorpay_link': getattr(doc, 'razorpay_link', None),
        'razorpay_expiry': getattr(doc, 'razorpay_expiry', None),
        'razorpay_payment_status': getattr(doc, 'razorpay_payment_status', None),
        'debug': debug_info
    } 