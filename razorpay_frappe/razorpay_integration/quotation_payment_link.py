import frappe
from frappe.model.document import Document
from frappe.utils import getdate, add_days
from razorpay_frappe.razorpay_integration.jinja_functions import get_payment_link_qr_code


def create_or_update_razorpay_link(quotation):
    """
    Create or update a Razorpay payment link for the given Quotation document.
    Save the link, expiry, and status to custom fields.
    """
    # Generate payment link using existing logic
    payment_data = get_payment_link_qr_code(quotation)
    if payment_data and payment_data.get('short_url'):
        quotation.db_set('razorpay_link', payment_data['short_url'])
        # Try to get expiry from payment_data, fallback to 30 days from today
        expiry = payment_data.get('expire_by')
        if not expiry:
            expiry = add_days(getdate(), 30)
        quotation.db_set('razorpay_expiry', expiry)
        quotation.db_set('razorpay_payment_status', 'Created')
    else:
        quotation.db_set('razorpay_link', None)
        quotation.db_set('razorpay_expiry', None)
        quotation.db_set('razorpay_payment_status', None)


def on_submit(doc, method=None):
    """
    Hook: Called when Quotation is submitted.
    """
    create_or_update_razorpay_link(doc)


@frappe.whitelist()
def regenerate_razorpay_link(quotation_name):
    """
    Regenerate a Razorpay payment link for a Quotation (button action).
    """
    quotation = frappe.get_doc('Quotation', quotation_name)
    create_or_update_razorpay_link(quotation)
    return {
        'razorpay_link': quotation.razorpay_link,
        'razorpay_expiry': quotation.razorpay_expiry,
        'razorpay_payment_status': quotation.razorpay_payment_status,
    } 