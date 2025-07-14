import frappe
import hmac
import hashlib
import json
from frappe.utils import nowdate
from razorpay_frappe.razorpay_integration.email_templates import send_payment_confirmation_email

def find_doc_by_razorpay_link(short_url):
    for doctype in ["Quotation", "Sales Order", "Sales Invoice"]:
        docs = frappe.get_all(doctype, filters={"razorpay_link": short_url}, limit=1)
        if docs:
            return frappe.get_doc(doctype, docs[0].name)
    return None

def create_payment_entry_for_doc(doc, payment_id, paid_at):
    # Check if Payment Entry already exists
    existing = frappe.get_all('Payment Entry', filters={
        'reference_no': payment_id,
        'reference_date': paid_at or nowdate(),
        'party_type': 'Customer',
        'party': getattr(doc, 'customer', None),
        'reference_doctype': doc.doctype,
        'reference_name': doc.name
    })
    if existing:
        return
    pe = frappe.new_doc('Payment Entry')
    pe.payment_type = 'Receive'
    pe.party_type = 'Customer'
    pe.party = getattr(doc, 'customer', None)
    pe.posting_date = paid_at or nowdate()
    pe.reference_no = payment_id
    pe.reference_date = paid_at or nowdate()
    pe.paid_amount = doc.grand_total
    pe.received_amount = doc.grand_total
    pe.received_from = getattr(doc, 'customer', None)
    pe.reference_doctype = doc.doctype
    pe.reference_name = doc.name
    pe.mode_of_payment = 'Razorpay'
    pe.save(ignore_permissions=True)
    pe.submit()
    send_payment_confirmation_email(doc, pe.name, pe.paid_amount, pe.posting_date)

@frappe.whitelist(allow_guest=True, methods=['POST'])
def razorpay_webhook():
    # Get Razorpay webhook secret from site config or environment
    secret = frappe.conf.get('razorpay_webhook_secret')
    if not secret:
        frappe.local.response['http_status_code'] = 500
        return 'Webhook secret not configured.'

    # Get request data and signature
    data = frappe.request.get_data(as_text=True)
    signature = frappe.get_request_header('X-Razorpay-Signature')
    if not signature:
        frappe.local.response['http_status_code'] = 400
        return 'Missing signature.'

    # Validate signature
    expected = hmac.new(secret.encode(), data.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        frappe.local.response['http_status_code'] = 403
        return 'Invalid signature.'

    event = json.loads(data)
    event_type = event.get('event')
    payload = event.get('payload', {})

    # Only handle payment_link events
    if event_type and event_type.startswith('payment_link.'):
        payment_link = payload.get('payment_link', {}).get('entity', {})
        short_url = payment_link.get('short_url')
        status = payment_link.get('status')
        payment_id = payment_link.get('id')
        paid_at = payment_link.get('paid_at')

        # Find document by razorpay_link
        if short_url:
            doc = find_doc_by_razorpay_link(short_url)
            if doc:
                doc.db_set('razorpay_payment_status', status.title())
                doc.db_set('razorpay_payment_id', payment_id)
                if status == 'paid':
                    create_payment_entry_for_doc(doc, payment_id, paid_at)
    return 'OK' 