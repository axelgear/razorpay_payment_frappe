import frappe
from frappe.utils.pdf import get_pdf
from frappe.utils.jinja import render_template

def send_payment_confirmation_email(doc, payment_entry_id, paid_amount, paid_at):
    # Determine document type and recipient
    doctype = doc.doctype
    docname = doc.name
    customer_email = getattr(doc, 'contact_email', None) or getattr(doc, 'customer_email', None) or getattr(doc, 'email_id', None)
    if not customer_email:
        return
    # Email subject and message
    subject = f"Payment Confirmation for {doctype} {docname}"
    context = {
        'doc': doc,
        'payment_entry_id': payment_entry_id,
        'doc_id': docname,
        'amount': paid_amount,
        'paid_at': paid_at,
    }
    message = render_template("""
        <p>Dear {{ doc.customer_name or doc.customer or '' }},</p>
        <p>We have received your payment for <b>{{ doc.doctype }} {{ doc.name }}</b>.</p>
        <ul>
            <li><b>Payment Entry ID:</b> {{ payment_entry_id }}</li>
            <li><b>{{ doc.doctype }} ID:</b> {{ doc_id }}</li>
            <li><b>Amount Paid:</b> {{ amount }}</li>
            <li><b>Payment Date:</b> {{ paid_at }}</li>
        </ul>
        <p>Attached is a copy of your {{ doc.doctype|lower }} for your records.</p>
        <p>Thank you for your business!</p>
    """, context)
    # Generate PDF
    pdf = get_pdf(frappe.get_print(doctype, docname, print_format=None, as_pdf=True))
    attachments = [{
        'fname': f'{doctype}-{docname}.pdf',
        'fcontent': pdf
    }]
    # Send email
    frappe.sendmail(
        recipients=[customer_email],
        subject=subject,
        message=message,
        attachments=attachments
    ) 