import hashlib
import hmac
import json
import frappe
from frappe import _
from razorpay_frappe.utils import get_razorpay_client


@frappe.whitelist(allow_guest=True, methods=['POST'])
def razorpay_webhook():
    """Handle Razorpay webhook events for payment links"""
    try:
        # Get Razorpay webhook secret from settings
        settings = frappe.get_single("Razorpay Settings")
        secret = settings.get_password("webhook_secret")
        
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

        # Parse webhook data
        event = json.loads(data)
        event_type = event.get('event')
        payload = event.get('payload', {})
        
        # Log webhook event for debugging
        frappe.logger().info(f"Razorpay webhook received: {event_type}")
        
        # Handle payment link events
        if event_type and event_type.startswith('payment_link.'):
            handle_payment_link_webhook(event_type, payload)
        
        # Set proper response headers
        frappe.local.response['http_status_code'] = 200
        frappe.local.response['content_type'] = 'text/plain'
        return 'OK'
        
    except Exception as e:
        frappe.log_error(f"Razorpay webhook error: {str(e)}")
        frappe.local.response['http_status_code'] = 500
        return f'Webhook processing error: {str(e)}'


def handle_payment_link_webhook(event_type: str, payload: dict):
    """Handle payment link webhook events"""
    try:
        payment_link_entity = payload.get('payment_link', {}).get('entity', {})
        payment_link_id = payment_link_entity.get('id')
        
        if not payment_link_id:
            frappe.log_error("Payment link ID not found in webhook payload")
            return
        
        # Find the payment link document
        payment_link_doc = frappe.db.get_value("Razorpay Payment Link", {"id": payment_link_id}, "name")
        if not payment_link_doc:
            frappe.log_error(f"Payment link document not found for ID: {payment_link_id}")
            return
        
        payment_link_doc = frappe.get_doc("Razorpay Payment Link", payment_link_doc)
        
        # Handle different payment link events
        if event_type == 'payment_link.paid':
            handle_payment_link_paid(payment_link_doc, payment_link_entity)
        elif event_type == 'payment_link.cancelled':
            handle_payment_link_cancelled(payment_link_doc, payment_link_entity)
        elif event_type == 'payment_link.expired':
            handle_payment_link_expired(payment_link_doc, payment_link_entity)
        
    except Exception as e:
        frappe.log_error(f"Error handling payment link webhook: {str(e)}")


def handle_payment_link_paid(payment_link_doc, payment_link_entity):
    """Handle payment link paid event"""
    try:
        # Get payment details from Razorpay
        client = get_razorpay_client()
        payment_link_details = client.payment_link.fetch(payment_link_doc.id)
        
        # Update payment link document
        payment_link_doc.status = payment_link_details.get('status', 'Paid')
        
        # Update amount paid
        amount_paid = payment_link_details.get('amount_paid', 0)
        if amount_paid:
            payment_link_doc.amount_paid = amount_paid / 100  # Convert from paise to rupees
        
        # Update payment details
        payment_link_doc.razorpay_payment_id = payment_link_details.get('payment_id')
        payment_link_doc.razorpay_payment_status = 'Paid'
        
        # Calculate remaining amount
        total_amount = payment_link_doc.amount
        remaining_amount = max(0, total_amount - payment_link_doc.amount_paid)
        payment_link_doc.remaining_amount = remaining_amount
        
        # Update status based on payment amount
        if payment_link_doc.amount_paid >= total_amount:
            payment_link_doc.status = 'Paid'
        elif payment_link_doc.amount_paid > 0:
            payment_link_doc.status = 'Partially Paid'
        
        # Update payment details child table
        update_payment_details_table(payment_link_doc, payment_link_details)
        
        # Save the document
        payment_link_doc.save()
        
        # Log the payment
        frappe.logger().info(f"Payment link {payment_link_doc.name} updated - Amount Paid: {payment_link_doc.amount_paid}, Status: {payment_link_doc.status}")
        
        # Send notification
        send_payment_notification(payment_link_doc)
        
    except Exception as e:
        frappe.log_error(f"Error handling payment link paid event: {str(e)}")


def handle_payment_link_cancelled(payment_link_doc, payment_link_entity):
    """Handle payment link cancelled event"""
    try:
        payment_link_doc.status = 'Cancelled'
        payment_link_doc.save()
        
        frappe.logger().info(f"Payment link {payment_link_doc.name} cancelled")
        
    except Exception as e:
        frappe.log_error(f"Error handling payment link cancelled event: {str(e)}")


def handle_payment_link_expired(payment_link_doc, payment_link_entity):
    """Handle payment link expired event"""
    try:
        payment_link_doc.status = 'Expired'
        payment_link_doc.save()
        
        frappe.logger().info(f"Payment link {payment_link_doc.name} expired")
        
    except Exception as e:
        frappe.log_error(f"Error handling payment link expired event: {str(e)}")


def send_payment_notification(payment_link_doc):
    """Send payment notification to ZohoCliq"""
    try:
        from razorpay_frappe.utils import post_to_zohocliq
        
        # Get associated document details
        quotation_name = payment_link_doc.quotation
        customer_name = payment_link_doc.customer
        
        message = f"Payment received for {customer_name} - Amount: ₹{payment_link_doc.amount_paid}, Payment Link: {payment_link_doc.name}"
        if quotation_name:
            message += f", Quotation: {quotation_name}"
        
        # Send to Accounts channel
        post_to_zohocliq(message, channel="Accounts")
        
    except Exception as e:
        frappe.log_error(f"Error sending payment notification: {str(e)}")


@frappe.whitelist()
def sync_payment_link_status(payment_link_name: str):
    """Manually sync payment link status from Razorpay"""
    try:
        payment_link_doc = frappe.get_doc("Razorpay Payment Link", payment_link_name)
        
        # Fetch latest details from Razorpay
        client = get_razorpay_client()
        payment_link_details = client.payment_link.fetch(payment_link_doc.id)
        
        # Update status based on Razorpay status
        razorpay_status = payment_link_details.get('status', 'created')
        if razorpay_status == 'paid':
            payment_link_doc.status = 'Paid'
        elif razorpay_status == 'cancelled':
            payment_link_doc.status = 'Cancelled'
        elif razorpay_status == 'expired':
            payment_link_doc.status = 'Expired'
        else:
            payment_link_doc.status = 'Created'
        
        # Update amount paid
        amount_paid = payment_link_details.get('amount_paid', 0)
        if amount_paid:
            payment_link_doc.amount_paid = amount_paid / 100
        
        # Update payment details
        payment_link_doc.razorpay_payment_id = payment_link_details.get('payment_id')
        
        # Calculate remaining amount
        total_amount = payment_link_doc.amount
        remaining_amount = max(0, total_amount - payment_link_doc.amount_paid)
        payment_link_doc.remaining_amount = remaining_amount
        
        # Update payment status
        if payment_link_doc.amount_paid >= total_amount:
            payment_link_doc.razorpay_payment_status = 'Paid'
        elif payment_link_doc.amount_paid > 0:
            payment_link_doc.razorpay_payment_status = 'Partially Paid'
        else:
            payment_link_doc.razorpay_payment_status = 'Pending'
        
        # Update payment details child table
        update_payment_details_table(payment_link_doc, payment_link_details)
        
        # Save the document
        payment_link_doc.save()
        
        return {
            "success": True,
            "status": payment_link_doc.status,
            "amount_paid": payment_link_doc.amount_paid,
            "total_amount": payment_link_doc.amount,
            "remaining_amount": payment_link_doc.remaining_amount,
            "razorpay_status": razorpay_status,
            "payment_id": payment_link_doc.razorpay_payment_id
        }
        
    except Exception as e:
        frappe.log_error(f"Error syncing payment link status: {str(e)}")
        return {"success": False, "error": str(e)}


def update_payment_details_table(payment_link_doc, payment_link_details):
    """Update the payment_details by creating separate payment detail documents."""
    try:
        # Get payments from Razorpay response
        payments = payment_link_details.get('payments', [])
        
        for payment in payments:
            try:
                # Check if payment detail already exists
                existing_payment = frappe.db.exists("Razorpay Payment Detail", {"payment_id": payment['payment_id']})
                
                if existing_payment:
                    # Update existing payment detail
                    payment_detail_doc = frappe.get_doc("Razorpay Payment Detail", existing_payment)
                else:
                    # Create new payment detail
                    payment_detail_doc = frappe.new_doc("Razorpay Payment Detail")
                
                # Get detailed payment information from Razorpay
                client = get_razorpay_client()
                payment_info = client.payment.fetch(payment['payment_id'])
                
                # Update payment detail fields
                payment_detail_doc.payment_id = payment['payment_id']
                payment_detail_doc.amount = payment_info.get('amount', 0) / 100  # Convert from paise to rupees
                payment_detail_doc.currency = payment_info.get('currency', 'INR')
                payment_detail_doc.status = payment_info.get('status', 'created')
                payment_detail_doc.method = payment_info.get('method', '')
                payment_detail_doc.created_at = frappe.utils.get_datetime(payment_info.get('created_at'))
                payment_detail_doc.payment_link = payment_link_doc.name
                payment_detail_doc.customer = payment_link_doc.customer
                payment_detail_doc.quotation = payment_link_doc.quotation
                
                # Save the payment detail
                payment_detail_doc.save()
                
            except Exception as e:
                frappe.log_error(f"Error processing payment {payment['payment_id']}: {str(e)}")
                # Add basic payment info if detailed fetch fails
                try:
                    existing_payment = frappe.db.exists("Razorpay Payment Detail", {"payment_id": payment['payment_id']})
                    
                    if existing_payment:
                        payment_detail_doc = frappe.get_doc("Razorpay Payment Detail", existing_payment)
                    else:
                        payment_detail_doc = frappe.new_doc("Razorpay Payment Detail")
                    
                    payment_detail_doc.payment_id = payment['payment_id']
                    payment_detail_doc.amount = payment.get('amount', 0) / 100
                    payment_detail_doc.currency = payment_link_details.get('currency', 'INR')
                    payment_detail_doc.status = payment.get('status', 'created')
                    payment_detail_doc.method = payment.get('method', '')
                    payment_detail_doc.created_at = frappe.utils.get_datetime(payment.get('created_at'))
                    payment_detail_doc.payment_link = payment_link_doc.name
                    payment_detail_doc.customer = payment_link_doc.customer
                    payment_detail_doc.quotation = payment_link_doc.quotation
                    
                    payment_detail_doc.save()
                    
                except Exception as fallback_error:
                    frappe.log_error(f"Error in fallback payment processing {payment['payment_id']}: {str(fallback_error)}")
        
    except Exception as e:
        frappe.log_error(f"Error updating payment details: {str(e)}")


@frappe.whitelist()
def sync_all_payment_links():
    """Sync all payment links from Razorpay"""
    try:
        # Get all payment links
        payment_links = frappe.get_all("Razorpay Payment Link", fields=["name", "id"])
        
        results = []
        for pl in payment_links:
            try:
                result = sync_payment_link_status(pl.name)
                results.append({
                    "payment_link": pl.name,
                    "result": result
                })
            except Exception as e:
                results.append({
                    "payment_link": pl.name,
                    "result": {"success": False, "error": str(e)}
                })
        
        return {
            "success": True,
            "results": results,
            "total": len(payment_links)
        }
        
    except Exception as e:
        frappe.log_error(f"Error syncing all payment links: {str(e)}")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_payment_link_details(payment_link_name: str):
    """Get detailed payment link information"""
    try:
        payment_link_doc = frappe.get_doc("Razorpay Payment Link", payment_link_name)
        
        # Use the correct payment link ID
        payment_link_id = payment_link_doc.id
        
        # Fetch latest details from Razorpay
        client = get_razorpay_client()
        payment_link_details = client.payment_link.fetch(payment_link_id)
        
        # Get payment details if available
        payments = []
        if payment_link_details.get('payments'):
            for payment in payment_link_details['payments']:
                try:
                    payment_info = client.payment.fetch(payment['payment_id'])
                    payments.append({
                        "payment_id": payment['payment_id'],
                        "amount": payment_info.get('amount', 0) / 100,
                        "currency": payment_info.get('currency'),
                        "status": payment_info.get('status'),
                        "method": payment_info.get('method'),
                        "created_at": payment_info.get('created_at')
                    })
                except Exception as e:
                    frappe.log_error(f"Error fetching payment {payment.get('payment_id', 'unknown')}: {str(e)}")
        
        return {
            "success": True,
            "payment_link": {
                "name": payment_link_doc.name,
                "id": payment_link_doc.id,
                "razorpay_payment_id": payment_link_doc.razorpay_payment_id,
                "status": payment_link_doc.status,
                "amount": payment_link_doc.amount,
                "amount_paid": payment_link_doc.amount_paid,
                "remaining_amount": payment_link_doc.remaining_amount,
                "currency": payment_link_doc.currency,
                "short_url": payment_link_doc.short_url,
                "expire_by": payment_link_doc.expire_by,
                "customer": payment_link_doc.customer,
                "quotation": payment_link_doc.quotation
            },
            "razorpay_details": payment_link_details,
            "payments": payments
        }
        
    except Exception as e:
        import traceback
        frappe.log_error(f"Error getting payment link details: {str(e)}\nTraceback: {traceback.format_exc()}")
        return {"success": False, "error": str(e)} 


@frappe.whitelist()
def get_payment_details_for_link(payment_link_name: str):
    """Get all payment details for a specific payment link."""
    try:
        # Get payment link document
        payment_link_doc = frappe.get_doc("Razorpay Payment Link", payment_link_name)
        
        # Get all payment details for this payment link
        payment_details = frappe.get_all(
            "Razorpay Payment Detail",
            filters={"payment_link": payment_link_name},
            fields=["name", "payment_id", "amount", "currency", "status", "method", "created_at"],
            order_by="created_at desc"
        )
        
        # Calculate totals
        total_paid = sum(pd['amount'] for pd in payment_details if pd['status'] == 'captured')
        total_payments = len(payment_details)
        
        return {
            "success": True,
            "payment_link": {
                "name": payment_link_doc.name,
                "status": payment_link_doc.status,
                "amount": payment_link_doc.amount,
                "amount_paid": payment_link_doc.amount_paid,
                "remaining_amount": payment_link_doc.amount - total_paid,
                "currency": payment_link_doc.currency,
                "customer": payment_link_doc.customer,
                "quotation": payment_link_doc.quotation
            },
            "payment_details": payment_details,
            "summary": {
                "total_payments": total_payments,
                "total_paid": total_paid,
                "remaining_amount": payment_link_doc.amount - total_paid
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting payment details for link: {str(e)}")
        return {"success": False, "error": str(e)} 