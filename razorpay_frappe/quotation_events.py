from __future__ import annotations
import frappe
from razorpay_frappe.utils import (
    create_payment_link_for_quotation,
    update_payment_link_on_revision,
    post_to_zohocliq,
    create_quote_update_template,
)

def handle_quotation_submit(doc, method=None):
    """Generate payment link on quotation submit."""
    try:
        # Always create a new payment link (Razorpay doesn't allow updating amounts/dates)
        # For revisions, we'll create a new link but track the relationship
        result = create_payment_link_for_quotation(doc.name)
        
        # Check if payment link creation was successful
        if isinstance(result, dict) and result.get("success") == False:
            # Payment link creation failed
            frappe.log_error(f"Payment link creation failed: {result.get('error')}", "Razorpay Quotation Submit")
            return
        
        # Get the short URL from the response
        short_url = None
        if isinstance(result, dict):
            short_url = result.get("short_url")
        elif hasattr(result, 'get'):
            short_url = result.get("short_url")
        
        # Notify via ZohoCliq with template
        if short_url:
            # Get quote details
            quote_details = {
                "name": doc.name,
                "customer_name": doc.customer_name,
                "grand_total": doc.grand_total,
                "currency": doc.currency,
                "valid_till": doc.valid_till,
            }
            
            # Get QR code URL if available
            qr_image_url = None
            if hasattr(doc, 'razorpay_qr_code') and doc.razorpay_qr_code:
                qr_image_url = doc.razorpay_qr_code
            
            # Create and send template
            template = create_quote_update_template(doc.name, quote_details, short_url, qr_image_url)
            
            # Send to ZohoCliq using Sales channel
            try:
                from razorpay_frappe.utils import send_zohocliq_message, build_zohocliq_webhook_url
                settings = frappe.get_single("ZohoCliq Settings")
                
                # Use the configured Sales channel
                sales_channel = settings.sales_channel_unique
                if not sales_channel:
                    frappe.log_error("Sales channel not configured in ZohoCliq Settings", "ZohoCliq Error")
                    return
                
                webhook_url = f"https://cliq.zoho.com/api/v2/channelsbyname/{sales_channel}/message?bot_unique_name={settings.bot_unique_name}&zapikey={settings.get_password('bot_token')}"
                send_zohocliq_message(webhook_url, template)
            except Exception as zoho_error:
                # Use shorter error message to avoid length issues
                error_msg = str(zoho_error)[:100] if len(str(zoho_error)) > 100 else str(zoho_error)
                frappe.log_error(f"ZohoCliq notification failed: {error_msg}", "ZohoCliq Error")
        else:
            post_to_zohocliq(
                message=f"Payment Link generation failed for Quotation *{doc.name}*",
                channel="Sales",
            )
    except Exception as e:
        frappe.log_error(str(e), "Razorpay Quotation Submit")
        # Still send notification about the failure
        try:
            post_to_zohocliq(
                message=f"Payment Link generation failed for Quotation *{doc.name}* - {str(e)}",
                channel="Sales",
            )
        except:
            pass


def handle_quotation_update(doc, method=None):
    """Handle quotation revision: regenerate or update payment link."""
    try:
        result = update_payment_link_on_revision(doc.name)
        
        # Check if payment link update was successful
        if isinstance(result, dict) and result.get("success") == False:
            # Payment link update failed
            frappe.log_error(f"Payment link update failed: {result.get('error')}", "Razorpay Quotation Update")
            return
        
        # Get the short URL from the response
        short_url = None
        if isinstance(result, dict):
            short_url = result.get("short_url")
        elif hasattr(result, 'get'):
            short_url = result.get("short_url")
        
        # Notify via ZohoCliq with template
        if short_url:
            # Get quote details
            quote_details = {
                "name": doc.name,
                "customer_name": doc.customer_name,
                "grand_total": doc.grand_total,
                "currency": doc.currency,
                "valid_till": doc.valid_till,
            }
            
            # Get QR code URL if available
            qr_image_url = None
            if hasattr(doc, 'razorpay_qr_code') and doc.razorpay_qr_code:
                qr_image_url = doc.razorpay_qr_code
            
            # Create and send template
            template = create_quote_update_template(doc.name, quote_details, short_url, qr_image_url)
            
            # Send to ZohoCliq using Sales channel
            try:
                from razorpay_frappe.utils import send_zohocliq_message
                settings = frappe.get_single("ZohoCliq Settings")
                
                # Use the configured Sales channel
                sales_channel = settings.sales_channel_unique
                if not sales_channel:
                    frappe.log_error("Sales channel not configured in ZohoCliq Settings", "ZohoCliq Error")
                    return
                
                webhook_url = f"https://cliq.zoho.com/api/v2/channelsbyname/{sales_channel}/message?bot_unique_name={settings.bot_unique_name}&zapikey={settings.get_password('bot_token')}"
                send_zohocliq_message(webhook_url, template)
            except Exception as zoho_error:
                # Use shorter error message to avoid length issues
                error_msg = str(zoho_error)[:100] if len(str(zoho_error)) > 100 else str(zoho_error)
                frappe.log_error(f"ZohoCliq notification failed: {error_msg}", "ZohoCliq Error")
        else:
            post_to_zohocliq(
                message=f"Payment Link update failed for Quotation *{doc.name}*",
                channel="Sales",
            )
    except Exception as e:
        frappe.log_error(str(e), "Razorpay Quotation Update")
        # Still send notification about the failure
        try:
            post_to_zohocliq(
                message=f"Payment Link update failed for Quotation *{doc.name}* - {str(e)}",
                channel="Sales",
            )
        except:
            pass 