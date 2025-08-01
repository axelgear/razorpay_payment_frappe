import os
from enum import StrEnum

import frappe
import razorpay
from frappe.utils.password import get_decrypted_password
from .zoho_templates import (
	create_new_project_template,
	create_status_update_template,
	create_task_assignment_template,
	create_meeting_schedule_template,
	create_material_request_template,
	create_thread_message_template,
	create_quote_update_template,
)


class RazorpayPaymentWebhookEvents(StrEnum):
	PaymentCaptured = "payment.captured"
	RefundProcessed = "refund.processed"


class RazorpaySubscriptionWebhookEvents(StrEnum):
	SubscriptionActivated = "subscription.activated"
	SubscriptionCharged = "subscription.charged"
	SubscriptionCompleted = "subscription.completed"
	SubscriptionUpdated = "subscription.updated"
	SubscriptionPending = "subscription.pending"
	SubscriptionHalted = "subscription.halted"
	SubscriptionCancelled = "subscription.cancelled"
	SubscriptionPaused = "subscription.paused"
	SubscriptionResumed = "subscription.resumed"


def get_razorpay_client():
	"""Return a Razorpay client instance using credentials based on the current
	Razorpay Settings.

	Priority:
	1. If running in CI environment, fall back to env vars (maintains existing behaviour)
	2. If *Sandbox Mode* is enabled in settings use sandbox credentials
	3. Otherwise use production credentials
	"""
	in_ci = os.environ.get("CI")
	if in_ci:
		key_id = os.environ.get("RZP_SANDBOX_KEY_ID")
		key_secret = os.environ.get("RZP_SANDBOX_KEY_SECRET")
	else:
		razorpay_settings = frappe.get_cached_doc("Razorpay Settings")
		if getattr(razorpay_settings, "sandbox_mode", 0):
			key_id = razorpay_settings.sandbox_key_id
			key_secret = razorpay_settings.get_password("sandbox_key_secret")
		else:
			key_id = razorpay_settings.key_id
			key_secret = razorpay_settings.get_password("key_secret")

	if not (key_id or key_secret):
		frappe.throw(
			f"Please set API keys in {frappe.bold('Razorpay Settings')} before trying to create a razorpay client!"
		)

	return razorpay.Client(auth=(key_id, key_secret))


def get_in_razorpay_money(amount: int) -> int:
	return amount * 100


def convert_from_razorpay_money(amount: int) -> int:
	return amount / 100


def verify_webhook_signature(payload):
	signature = frappe.get_request_header("X-Razorpay-Signature")
	webhook_secret = get_decrypted_password(
		"Razorpay Settings", "Razorpay Settings", "webhook_secret"
	)

	client = get_razorpay_client()
	client.utility.verify_webhook_signature(
		payload.decode(), signature, webhook_secret
	)

# ------------- Notification Helpers -----------------
# Minimal helper to send messages to ZohoCliq channels when a webhook URL is
# configured. We keep this intentionally lightweight.


def get_channel_unique_name(channel: str) -> str:
    """Get channel unique name from ZohoCliq Settings."""
    settings = frappe.get_cached_doc("ZohoCliq Settings")
    
    # Map channel types to settings fields
    channel_field_map = {
        "Project": "project_channel_unique",
        "Quote": "quote_channel_unique", 
        "Notification": "notification_channel_unique",
        "Design": "design_channel_unique",
        "Accounts": "accounts_channel_unique",
        "Purchase": "purchase_channel_unique",
        "Sales": "sales_channel_unique",
        "Installation": "installation_channel_unique",
        "Production": "production_channel_unique",
        "Planning": "planning_channel_unique",
    }
    
    field_name = channel_field_map.get(channel)
    if not field_name:
        frappe.throw(f"Channel '{channel}' not supported. Supported channels: {', '.join(channel_field_map.keys())}")
    
    channel_unique_name = getattr(settings, field_name, None)
    if not channel_unique_name:
        frappe.throw(f"Channel '{channel}' unique name not configured in ZohoCliq Settings")
    
    return channel_unique_name


def build_zohocliq_webhook_url(channel_unique_name: str) -> str:
	"""Build ZohoCliq webhook URL for a given channel unique name.
	
	Args:
		channel_unique_name: The unique name of the channel
		
	Returns:
			The complete webhook URL with authentication parameters
	"""
	settings = frappe.get_cached_doc("ZohoCliq Settings")
	if not settings.enabled:
		frappe.throw("ZohoCliq Notifications not enabled")
	
	# Validate required fields
	if not channel_unique_name:
		frappe.throw("Channel unique name is required")
	
	if not settings.bot_unique_name:
		frappe.throw("Bot Unique Name not configured in ZohoCliq Settings")
	
	if not settings.bot_token:
		frappe.throw("Bot Token not configured in ZohoCliq Settings")
	
	# Get the decrypted token - try multiple methods
	token = None
	try:
		# Method 1: Try get_password first
		token = settings.get_password("bot_token")
		if not token:
			# Method 2: Try direct attribute (might be masked)
			token = settings.bot_token
			if token and token.startswith("*"):
				# If it's masked, try get_password again
				token = settings.get_password("bot_token")
	except Exception as e:
		frappe.log_error(f"Error getting bot token: {str(e)}", "ZohoCliq Token Error")
	
	if not token:
		frappe.throw("Bot Token not found or invalid")
	
	# Log the URL being constructed for debugging
	webhook_url = f"https://cliq.zoho.com/api/v2/channelsbyname/{channel_unique_name}/message?bot_unique_name={settings.bot_unique_name}&zapikey={token}"
	
	# Simple debug log without long URLs
	frappe.log_error(
		f"Building webhook URL for channel: {channel_unique_name}",
		"ZohoCliq Webhook URL Construction"
	)
	
	return webhook_url


def send_zohocliq_message(webhook_url: str, message):
	"""Send message to ZohoCliq via webhook URL and log on failure."""
	import json, requests
	try:
		# Handle both string messages and template objects
		if isinstance(message, str):
			payload = {"text": message}
		else:
			# Template object (dict)
			payload = message
		
		# Check message length before sending
		message_str = json.dumps(payload)
		if len(message_str) > 4000:  # ZohoCliq has limits
			frappe.log_error(f"ZohoCliq message too long ({len(message_str)} chars). Truncating.", "ZohoCliq Message Length")
			# Truncate the message
			if isinstance(message, dict) and "text" in message:
				message["text"] = message["text"][:100] + "..."
				payload = message
		
		resp = requests.post(
			webhook_url,
			data=json.dumps(payload),
			headers={"Content-Type": "application/json"},
			timeout=10,  # Increased timeout
		)
		if resp.status_code not in (200, 201, 204):  # 204 is also success for ZohoCliq
			# Log detailed error information and raise so caller can fallback
			error_data = {
				"url": webhook_url,
				"status": resp.status_code,
				"response": resp.text[:200] if resp.text else "",
				"message_length": len(json.dumps(payload)),
				"message_preview": str(payload)[:200] if len(str(payload)) > 200 else str(payload),
			}
			frappe.log_error(error_data, "ZohoCliq Notification Failed")
			raise Exception(f"ZohoCliq returned HTTP {resp.status_code}")
		else:
			frappe.logger().info(f"ZohoCliq message sent successfully to {webhook_url}")
	except Exception as e:
		# Log detailed error information
		error_data = {
			"url": webhook_url,
			"error": str(e),
			"message_type": type(message).__name__,
			"message_length": len(str(message)) if message else 0,
		}
		frappe.log_error(error_data, "ZohoCliq Error")


def post_to_zohocliq(message: str, channel: str):
	"""Public helper to send message to a configured ZohoCliq channel.

	Args:
		message: Text/content to send
		channel: One of "Project", "Quote", "Notification"
	"""
	settings = frappe.get_cached_doc("ZohoCliq Settings")
	if not settings.enabled:
		return

	unique_map = {
		"Project": settings.project_channel_unique,
		"Quote": settings.quote_channel_unique,
		"Notification": settings.notification_channel_unique,
		"Design": settings.design_channel_unique,
		"Accounts": settings.accounts_channel_unique,
		"Purchase": settings.purchase_channel_unique,
		"Sales": settings.sales_channel_unique,
		"Installation": settings.installation_channel_unique,
		"Production": settings.production_channel_unique,
		"Planning": settings.planning_channel_unique,
	}
	unique_name = unique_map.get(channel)
	if not unique_name:
		# Provide helpful error message with configuration instructions
		error_msg = f"""
		Channel '{channel}' unique name not configured in ZohoCliq Settings.
		
		Please configure the following in ZohoCliq Settings:
		- {channel} Channel Unique Name: Set to your ZohoCliq channel unique name
		
		Example: For Project channel, set 'Project Channel Unique Name' to 'project'
		"""
		frappe.throw(error_msg)

	webhook_url = build_zohocliq_webhook_url(unique_name)
	send_zohocliq_message(webhook_url, message)

# ------------------- QR Code helper -------------------


def generate_qr_code(short_url: str) -> bytes:
	"""Return a PNG byte-string representing a simple QR of the link."""
	import qrcode
	from io import BytesIO

	qr = qrcode.QRCode(version=1, box_size=10, border=4)
	qr.add_data(short_url)
	qr.make(fit=True)
	img = qr.make_image(fill_color="black", back_color="white")
	buf = BytesIO()
	img.save(buf, format="PNG")
	return buf.getvalue()

# -------------------- Payment & Utility APIs --------------------


def generate_payment_slip(payment_doc):
	"""Generate a PDF payment slip and attach to given document."""
	from frappe.utils.pdf import get_pdf
	from frappe.utils.file_manager import save_file

	html = frappe.render_template(
		"<h3>Payment Slip</h3><p>Amount: {{ amount }}</p>",
		{"amount": payment_doc.amount},
	)
	pdf_data = get_pdf(html)
	file_doc = save_file(
		f"PaymentSlip-{payment_doc.name}.pdf", pdf_data, payment_doc.doctype, payment_doc.name, is_private=1
	)
	payment_doc.payment_slip = file_doc.file_url
	payment_doc.save(ignore_permissions=True)
	return file_doc.file_url


# Stubs for functions requested – flesh out later


@frappe.whitelist()
def check_quotation_custom_fields():
    """Check Quotation custom fields"""
    try:
        fields = frappe.get_all('Custom Field', 
            filters={'dt': 'Quotation', 'fieldname': ['like', 'razorpay%']}, 
            fields=['fieldname', 'label', 'fieldtype'])
        
        return {
            "success": True,
            "fields": fields
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


def extract_original_quote_number(quotation_name: str) -> str:
    """Extract the original quote number without revision numbers.
    
    Examples:
    SAL-QTN-2025-00012 -> SAL-QTN-2025-00012
    SAL-QTN-2025-00012-1 -> SAL-QTN-2025-00012
    SAL-QTN-2025-00012-2 -> SAL-QTN-2025-00012
    """
    if not quotation_name:
        return quotation_name
    
    # Split by '-' and check if the last part is a number
    parts = quotation_name.split('-')
    if len(parts) >= 4:
        # Check if the last part is a number (revision)
        try:
            int(parts[-1])
            # If it's a number, remove it to get the original quote
            return '-'.join(parts[:-1])
        except ValueError:
            # If the last part is not a number, it's already the original quote
            return quotation_name
    
    return quotation_name


@frappe.whitelist()
def create_payment_link_for_quotation(quotation_name: str, advanced_options: dict | None = None):
    """Create a Razorpay payment link for the given quotation.

    Returns the response from Razorpay API.
    """
    try:
        quotation = frappe.get_doc("Quotation", quotation_name)
        settings = frappe.get_single("Razorpay Settings")

        client = get_razorpay_client()

        amount_rupees = quotation.grand_total
        amount_paise = int(amount_rupees * 100)

        payload = {
            "amount": amount_paise,
            "currency": quotation.currency or "INR",
            "accept_partial": bool(settings.allow_partial_payments),
            "description": f"Payment for Quotation {quotation.name}{' (Revised)' if quotation.amended_from else ''}",
            "reference_id": f"{quotation.name}",
            "customer": {
                "name": quotation.customer_name,
                "email": quotation.contact_email or "",
                "contact": quotation.contact_mobile or "",
            },
            "notify": {"sms": True, "email": True},
            "reminder_enable": True,
            "notes": {
                "quotation_id": quotation.name,
                "customer": quotation.customer_name,
                "is_revision": bool(quotation.amended_from),
                "revised_from": quotation.amended_from if quotation.amended_from else None,
                "original_quote": extract_original_quote_number(quotation.name)
            }
        }

        # Expiry
        if quotation.valid_till:
            payload["expire_by"] = int(frappe.utils.get_timestamp(quotation.valid_till))
        else:
            # Set default expiry to 30 days from now
            from datetime import datetime, time
            from frappe.utils import getdate, add_days
            
            expiry_date = add_days(getdate(), 30)
            expiry_datetime = datetime.combine(expiry_date, time(23, 59, 59))
            payload["expire_by"] = int(expiry_datetime.timestamp())

        # Merge advanced options
        if advanced_options:
            payload.update({k: v for k, v in advanced_options.items() if v is not None})

        # Create payment link
        response = client.payment_link.create(payload)
        
        # Debug: Log the response (shorter version)
        frappe.log_error(f"Payment link created: {response.get('id')} - {response.get('short_url')}", "Razorpay Debug")

        # Create Payment Link DocType entry
        pl_doc = frappe.new_doc("Razorpay Payment Link")
        # Flag to indicate link already created, so DocType shouldn't hit API again
        pl_doc.flags.link_already_created = True
        pl_doc.id = response.get("id")
        pl_doc.short_url = response.get("short_url")
        pl_doc.status = "Created"  # Use proper case
        pl_doc.amount = amount_rupees
        pl_doc.currency = quotation.currency
        pl_doc.quotation = quotation.name
        pl_doc.customer = quotation.customer_name
        pl_doc.expire_by = frappe.utils.getdate(response.get("expire_by")) if response.get("expire_by") else frappe.utils.add_days(frappe.utils.getdate(), 30)
        pl_doc.insert(ignore_permissions=True)
        
        # Update the payment link ID in the document
        pl_doc.db_set("payment_link_id", response.get("id"))

        # Attach QR code to Payment Link and Quotation
        qr_bytes = generate_qr_code(response.get("short_url"))
        if qr_bytes:
            try:
                # Use payment link name for QR filename
                fname = f"QR-{pl_doc.name}.png"
                
                # Create file document manually with public access
                file_doc = frappe.get_doc({
                    "doctype": "File",
                    "file_name": fname,
                    "content": qr_bytes,
                    "is_private": 0,  # Make it public
                    "attached_to_doctype": pl_doc.doctype,  # Attach to Razorpay Payment Link
                    "attached_to_name": pl_doc.name,  # Attach to the payment link document itself
                })
                file_doc.save()
                
                # Update both quotation and payment link with QR code URL
                quotation.razorpay_qr_code = file_doc.file_url
                pl_doc.qr = file_doc.file_url
            except Exception as qr_error:
                # Use shorter error message to avoid length issues
                error_msg = str(qr_error)[:100] if len(str(qr_error)) > 100 else str(qr_error)
                frappe.log_error(f"QR attachment failed for {quotation.name}: {error_msg}", "Razorpay QR Error")

        # Update Quotation fields
        quotation.db_set("razorpay_payment_url", response.get("short_url"))
        quotation.db_set("razorpay_payment_link", pl_doc.name)  # Link to the Payment Link DocType
        quotation.db_set("razorpay_expiry", pl_doc.expire_by)
        
        # Update QR code if generated
        if qr_bytes and hasattr(quotation, 'razorpay_qr_code'):
            quotation.db_set("razorpay_qr_code", quotation.razorpay_qr_code)

        return response
    except Exception as e:
        # Use shorter error message to avoid CharacterLengthExceededError
        error_msg = str(e)[:100] if len(str(e)) > 100 else str(e)
        frappe.log_error(f"Payment link creation failed for {quotation_name}: {error_msg}")
        return {"success": False, "error": str(e)}





@frappe.whitelist()
def check_razorpay_settings_fields():
    """Check what fields are in Razorpay Settings"""
    try:
        settings = frappe.get_single("Razorpay Settings")
        
        # Get all field values
        field_values = {}
        for field in settings.meta.fields:
            if field.fieldtype == "Password":
                field_values[field.fieldname] = "***HIDDEN***"
            else:
                field_values[field.fieldname] = getattr(settings, field.fieldname, None)
        
        return {
            "success": True,
            "fields": field_values
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def fetch_payment_link_details(payment_link_id: str):
    """Fetch payment details for a payment link"""
    try:
        client = get_razorpay_client()
        
        # Fetch payment link details from Razorpay
        payment_link = client.payment_link.fetch(payment_link_id)
        
        # Get payment details
        payments = []
        if payment_link.get("payments"):
            for payment in payment_link["payments"]:
                payment_details = client.payment.fetch(payment["id"])
                payments.append({
                    "payment_id": payment["id"],
                    "amount": payment["amount"] / 100,  # Convert from paise to rupees
                    "currency": payment["currency"],
                    "status": payment["status"],
                    "method": payment["method"],
                    "created_at": payment["created_at"],
                    "captured_at": payment.get("captured_at"),
                    "description": payment.get("description", ""),
                    "email": payment.get("email", ""),
                    "contact": payment.get("contact", ""),
                    "notes": payment.get("notes", {})
                })
        
        return {
            "success": True,
            "payment_link": {
                "id": payment_link["id"],
                "short_url": payment_link["short_url"],
                "amount": payment_link["amount"] / 100,
                "amount_paid": payment_link["amount_paid"] / 100,
                "currency": payment_link["currency"],
                "status": payment_link["status"],
                "created_at": payment_link["created_at"],
                "expire_by": payment_link.get("expire_by"),
                "expired_at": payment_link.get("expired_at"),
                "cancelled_at": payment_link.get("cancelled_at"),
                "description": payment_link.get("description", ""),
                "reference_id": payment_link.get("reference_id", ""),
                "accept_partial": payment_link.get("accept_partial", False),
                "first_min_partial_amount": payment_link.get("first_min_partial_amount", 0) / 100 if payment_link.get("first_min_partial_amount") else 0
            },
            "payments": payments
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def update_payment_link_status(payment_link_name: str):
    """Update payment link status and track payments"""
    try:
        # Get the payment link document
        pl_doc = frappe.get_doc("Razorpay Payment Link", payment_link_name)
        
        # Fetch latest details from Razorpay
        client = get_razorpay_client()
        payment_link = client.payment_link.fetch(pl_doc.id)
        
        # Update status
        pl_doc.status = payment_link["status"]
        
        # Update amount paid
        if payment_link.get("amount_paid"):
            pl_doc.amount_paid = payment_link["amount_paid"] / 100
        
        # Save the document
        pl_doc.save()
        
        return {
            "success": True,
            "status": payment_link["status"],
            "amount_paid": payment_link.get("amount_paid", 0) / 100,
            "total_amount": payment_link["amount"] / 100
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def debug_payment_link_status():
    """Debug payment link status for a quotation"""
    try:
        quotation_name = "SAL-QTN-2025-00010-5"
        quotation = frappe.get_doc("Quotation", quotation_name)
        
        return {
            "success": True,
            "quotation_name": quotation.name,
            "razorpay_payment_link": quotation.razorpay_payment_link,
            "razorpay_payment_url": quotation.razorpay_payment_url,
            "razorpay_qr_code": quotation.razorpay_qr_code,
            "razorpay_expiry": quotation.razorpay_expiry,
            "grand_total": quotation.grand_total,
            "valid_till": quotation.valid_till,
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def debug_payment_link_doc():
    """Debug payment link document details"""
    try:
        pl_doc_name = "plink_QyO7BvlG8N35Vd"
        pl_doc = frappe.get_doc("Razorpay Payment Link", pl_doc_name)
        
        return {
            "success": True,
            "pl_doc_name": pl_doc.name,
            "payment_link_id": pl_doc.payment_link_id,
            "short_url": pl_doc.short_url,
            "amount": pl_doc.amount,
            "currency": pl_doc.currency,
            "status": pl_doc.status,
            "expire_by": pl_doc.expire_by,
            "quotation": pl_doc.quotation,
            "customer": pl_doc.customer,
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


# ------------- Enhanced ZohoCliq Functions -----------------

def send_zohocliq_message_with_thread(webhook_url: str, main_message: dict, thread_title: str = None, thread_message: str = None):
	"""Send a message and optionally create a thread for discussions."""
	import json, requests
	
	try:
		# Send main message
		resp = requests.post(
			webhook_url,
			data=json.dumps(main_message),
			headers={"Content-Type": "application/json"},
			timeout=10,
		)
		
		if resp.status_code not in (200, 201):
			frappe.log_error(
				{
					"url": webhook_url,
					"status": resp.status_code,
					"response": resp.text,
					"message": main_message,
				},
				"ZohoCliq Main Message Failed",
			)
			return None
		
		# Parse response to get message_id
		resp_data = resp.json()
		message_id = resp_data.get("message_id") or (resp_data.get("data", {}).get("message_id"))
		
		if not message_id:
			frappe.log_error(
				{
					"url": webhook_url,
					"response": resp_data,
					"message": "No message_id in response",
				},
				"ZohoCliq Message ID Missing",
			)
			return None
		
		# Create thread if requested
		if thread_title and thread_message:
			thread_payload = create_thread_message_template(message_id, thread_title, thread_message)
			
			thread_resp = requests.post(
				webhook_url,
				data=json.dumps(thread_payload),
				headers={"Content-Type": "application/json"},
				timeout=10,
			)
			
			if thread_resp.status_code not in (200, 201):
				frappe.log_error(
					{
						"url": webhook_url,
						"status": thread_resp.status_code,
						"response": thread_resp.text,
						"thread_payload": thread_payload,
					},
					"ZohoCliq Thread Creation Failed",
				)
		
		return {
			"success": True,
			"message_id": message_id,
			"thread_message_id": message_id  # For thread messages, the message_id is the thread_id
		}
		
	except Exception as e:
		frappe.log_error(f"ZohoCliq Message with Thread Failed: {str(e)}", "ZohoCliq Message with Thread Failed")
		return {"success": False, "error": str(e)}


# ------------- Convenience Functions -----------------

@frappe.whitelist()
def send_new_project_notification(project_id: str, assigned_to: str, customer_name: str, channel: str = "Project"):
	"""Send new project notification with thread creation."""
	# Handle None or empty assigned_to
	assigned_to = assigned_to or ""
	
	main_message = create_new_project_template(project_id, assigned_to, customer_name)
	thread_title = f"Discussion – {project_id}"
	thread_message = f"Thread for project **{project_id}** discussions.\nPlease use this thread to collaborate on tasks, updates, and clarifications."
	
	# Get the actual channel unique name from settings
	channel_unique_name = get_channel_unique_name(channel)
	
	webhook_url = build_zohocliq_webhook_url(channel_unique_name)
	return send_zohocliq_message_with_thread(webhook_url, main_message, thread_title, thread_message)


@frappe.whitelist()
def send_task_assignment_notification(task_id: str, task_name: str, assigned_to: str, due_date: str = None, priority: str = "Medium", channel: str = "Project", description: str = None):
	"""Send task assignment notification."""
	# Handle None values
	assigned_to = assigned_to or ""
	task_name = task_name or ""
	description = description or ""
	
	main_message = create_task_assignment_template(task_id, task_name, assigned_to, due_date, priority, description=description)
	# Get the actual channel unique name from settings
	channel_unique_name = get_channel_unique_name(channel)
	
	webhook_url = build_zohocliq_webhook_url(channel_unique_name)
	return send_zohocliq_message_with_thread(webhook_url, main_message)


@frappe.whitelist()
def send_material_request_notification(request_id: str, requested_by: str, items: list, urgency: str = "Normal", channel: str = "Purchase"):
	"""Send material request notification."""
	# Handle None values
	requested_by = requested_by or ""
	
	main_message = create_material_request_template(request_id, requested_by, items, urgency)
	# Get the actual channel unique name from settings
	channel_unique_name = get_channel_unique_name(channel)
	
	webhook_url = build_zohocliq_webhook_url(channel_unique_name)
	return send_zohocliq_message_with_thread(webhook_url, main_message)


@frappe.whitelist()
def send_meeting_notification(meeting_title: str, scheduled_by: str, participants: list, date_time: str, duration: str = "1 hour", channel: str = "Notification"):
	"""Send meeting schedule notification."""
	# Handle None values
	meeting_title = meeting_title or ""
	scheduled_by = scheduled_by or ""
	participants = participants or []
	
	main_message = create_meeting_schedule_template(meeting_title, scheduled_by, participants, date_time, duration)
	# Get the actual channel unique name from settings
	channel_unique_name = get_channel_unique_name(channel)
	
	webhook_url = build_zohocliq_webhook_url(channel_unique_name)
	return send_zohocliq_message_with_thread(webhook_url, main_message)


@frappe.whitelist()
def send_status_update(title: str, status: str, details: dict, assigned_to: str = None, channel: str = "Notification"):
	"""Send status update notification."""
	# Handle None values
	title = title or ""
	assigned_to = assigned_to or ""
	
	main_message = create_status_update_template(title, status, details, assigned_to)
	# Get the actual channel unique name from settings
	channel_unique_name = get_channel_unique_name(channel)
	
	webhook_url = build_zohocliq_webhook_url(channel_unique_name)
	return send_zohocliq_message_with_thread(webhook_url, main_message)


@frappe.whitelist()
def send_project_notification_with_thread(project_id, channel="Project"):
    """Send project notification with thread creation and save thread ID to project"""
    try:
        # Get project details
        project = frappe.get_doc("Project", project_id)
        
        # Get assigned users
        assigned_users = []
        if project.users:
            for user in project.users:
                assigned_users.append(user.user)
        
        # Get the first assigned user or use project owner
        assigned_to = assigned_users[0] if assigned_users else project.owner
        
        # Create project template
        template = create_new_project_template(
            project_id=project.name,
            assigned_to=assigned_to,
            customer_name=project.customer,
            erp_link=f"{frappe.utils.get_url()}/app/project/{project.name}"
        )
        
        # Get ZohoCliq settings
        settings = frappe.get_single("ZohoCliq Settings")
        if not settings.enabled:
            return {"success": False, "error": "ZohoCliq not enabled"}
        
        # Get channel unique name
        unique_name = get_channel_unique_name(channel)
        
        # Build webhook URL
        webhook_url = build_zohocliq_webhook_url(unique_name)
        
        # Clean HTML tags from notes
        import re
        clean_notes = re.sub(r'<[^>]+>', '', project.notes or '') if project.notes else 'No notes available'
        
        # Send main message and create thread
        result = send_zohocliq_message_with_thread(
            webhook_url=webhook_url,
            main_message=template,
            thread_title=f"Project Discussion - {project.project_name}",
            thread_message=f"Project Details:\n\n**Project Name:** {project.project_name}\n**Customer:** {project.customer}\n**Status:** {project.status}\n**Expected Start:** {project.expected_start_date}\n**Expected End:** {project.expected_end_date}\n**Priority:** {project.priority}\n\n**Notes:**\n{clean_notes}\n\n**Assigned Users:**\n" + ("\n".join([f"- {user}" for user in assigned_users]) if assigned_users else "- No users assigned")
        )
        
        # Ensure result is a dictionary
        if isinstance(result, str):
            return {"success": False, "error": result}
        
        if result.get("success"):
            # Save thread ID to project
            thread_id = result.get("thread_message_id")
            if thread_id:
                # Debug: Log the thread ID
                frappe.log_error(f"Saving thread ID {thread_id} to project {project.name}", "ZohoCliq Thread Save")
                
                # Try to save the thread ID
                try:
                    project.db_set("zohocliq_thread_id", thread_id)
                    frappe.db.commit()
                    
                    # Verify the save
                    updated_project = frappe.get_doc("Project", project.name)
                    saved_thread_id = getattr(updated_project, 'zohocliq_thread_id', None)
                    frappe.log_error(f"Thread ID saved: {saved_thread_id}", "ZohoCliq Thread Save")
                    
                except Exception as save_error:
                    frappe.log_error(f"Failed to save thread ID: {str(save_error)}", "ZohoCliq Thread Save Error")
            
            return {
                "success": True,
                "message": "Project notification sent successfully",
                "thread_id": thread_id,
                "project_id": project.name
            }
        else:
            return result
            
    except Exception as e:
        frappe.log_error(f"Project notification error: {str(e)}", "ZohoCliq Project Notification")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def send_task_notification_to_project_thread(task_id, project_id=None):
    """Send task notification to the project's thread"""
    try:
        # Get task details
        task = frappe.get_doc("Task", task_id)
        
        # If project_id not provided, get from task
        if not project_id:
            project_id = task.project
        
        if not project_id:
            return {"success": False, "error": "No project associated with task"}
        
        # Get project to check thread ID
        project = frappe.get_doc("Project", project_id)
        thread_id = project.zohocliq_thread_id
        
        if not thread_id:
            return {"success": False, "error": "No thread ID found for project"}
        
        # Clean HTML tags from task description
        import re
        clean_description = re.sub(r'<[^>]+>', '', task.description or '') if task.description else 'No description'
        
        # Create task notification message
        task_message = {
            "text": f"**New Task Created**\n\n**Task:** {task.subject}\n**Assigned To:** {task.owner}\n**Status:** {task.status}\n**Priority:** {task.priority}\n**Due Date:** {task.exp_end_date or 'Not set'}\n\n**Description:**\n{clean_description}"
        }
        
        # Get ZohoCliq settings
        settings = frappe.get_single("ZohoCliq Settings")
        if not settings.enabled:
            return {"success": False, "error": "ZohoCliq not enabled"}
        
        # Get channel unique name (use project channel)
        unique_name = settings.project_channel_unique
        if not unique_name:
            return {"success": False, "error": "Project channel not configured"}
        
        # Build webhook URL
        webhook_url = build_zohocliq_webhook_url(unique_name)
        
        # Send message to thread
        thread_payload = {
            "text": task_message["text"],
            "thread_message_id": thread_id
        }
        
        response = send_zohocliq_message(webhook_url, thread_payload)
        
        if response.get("success"):
            return {
                "success": True,
                "message": "Task notification sent to project thread",
                "task_id": task_id,
                "project_id": project_id,
                "thread_id": thread_id
            }
        else:
            return response
            
    except Exception as e:
        return {"success": False, "error": str(e)}


# ------------- Settlement Functions -----------------

@frappe.whitelist()
def fetch_settlement(settlement_id: str):
    """Fetch settlement details from Razorpay"""
    try:
        client = get_razorpay_client()
        settlement = client.settlement.fetch(settlement_id)
        
        return {
            "success": True,
            "settlement": {
                "id": settlement.get("id"),
                "entity": settlement.get("entity"),
                "amount": settlement.get("amount") / 100 if settlement.get("amount") else 0,
                "currency": settlement.get("currency"),
                "status": settlement.get("status"),
                "created_at": settlement.get("created_at"),
                "updated_at": settlement.get("updated_at"),
                "fee": settlement.get("fee") / 100 if settlement.get("fee") else 0,
                "tax": settlement.get("tax") / 100 if settlement.get("tax") else 0,
                "utr": settlement.get("utr"),
                "settlement_date": settlement.get("settlement_date"),
                "on_hold": settlement.get("on_hold", False),
                "on_hold_until": settlement.get("on_hold_until"),
                "description": settlement.get("description", ""),
                "notes": settlement.get("notes", {}),
                # Additional Razorpay settlement fields
                "settlement_type": settlement.get("settlement_type", "regular"),
                "bank_account": settlement.get("bank_account", ""),
                "ifsc_code": settlement.get("ifsc_code", ""),
                "account_number": settlement.get("account_number", ""),
                "account_type": settlement.get("account_type", ""),
                "beneficiary_name": settlement.get("beneficiary_name", ""),
                "beneficiary_email": settlement.get("beneficiary_email", ""),
                "beneficiary_mobile": settlement.get("beneficiary_mobile", ""),
                "processed_at": settlement.get("processed_at"),
                "cancelled_at": settlement.get("cancelled_at"),
                "failure_reason": settlement.get("failure_reason", ""),
                "failure_code": settlement.get("failure_code", ""),
                "bank_reference_number": settlement.get("bank_reference_number", ""),
                "bank_branch": settlement.get("bank_branch", ""),
                "bank_city": settlement.get("bank_city", ""),
                "bank_state": settlement.get("bank_state", ""),
                "bank_pincode": settlement.get("bank_pincode", ""),
                "bank_country": settlement.get("bank_country", ""),
                "bank_phone": settlement.get("bank_phone", ""),
                "bank_email": settlement.get("bank_email", "")
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Failed to fetch settlement {settlement_id}: {str(e)}", "Razorpay Settlement Error")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def fetch_all_settlements(from_date: str = None, to_date: str = None, count: int = 10):
    """Fetch all settlements from Razorpay"""
    try:
        client = get_razorpay_client()
        
        # Prepare parameters
        params = {"count": count}
        if from_date:
            params["from"] = int(frappe.utils.get_timestamp(from_date))
        if to_date:
            params["to"] = int(frappe.utils.get_timestamp(to_date))
        
        settlements = client.settlement.all(params)
        
        # Process settlements
        processed_settlements = []
        for settlement in settlements.get("items", []):
            processed_settlements.append({
                "id": settlement.get("id"),
                "entity": settlement.get("entity"),
                "amount": settlement.get("amount") / 100 if settlement.get("amount") else 0,
                "currency": settlement.get("currency"),
                "status": settlement.get("status"),
                "created_at": settlement.get("created_at"),
                "updated_at": settlement.get("updated_at"),
                "fee": settlement.get("fee") / 100 if settlement.get("fee") else 0,
                "tax": settlement.get("tax") / 100 if settlement.get("tax") else 0,
                "utr": settlement.get("utr"),
                "settlement_date": settlement.get("settlement_date"),
                "on_hold": settlement.get("on_hold", False),
                "on_hold_until": settlement.get("on_hold_until"),
                "description": settlement.get("description", ""),
                "notes": settlement.get("notes", {}),
                # Additional Razorpay settlement fields
                "settlement_type": settlement.get("settlement_type", "regular"),
                "bank_account": settlement.get("bank_account", ""),
                "ifsc_code": settlement.get("ifsc_code", ""),
                "account_number": settlement.get("account_number", ""),
                "account_type": settlement.get("account_type", ""),
                "beneficiary_name": settlement.get("beneficiary_name", ""),
                "beneficiary_email": settlement.get("beneficiary_email", ""),
                "beneficiary_mobile": settlement.get("beneficiary_mobile", ""),
                "processed_at": settlement.get("processed_at"),
                "cancelled_at": settlement.get("cancelled_at"),
                "failure_reason": settlement.get("failure_reason", ""),
                "failure_code": settlement.get("failure_code", ""),
                "bank_reference_number": settlement.get("bank_reference_number", ""),
                "bank_branch": settlement.get("bank_branch", ""),
                "bank_city": settlement.get("bank_city", ""),
                "bank_state": settlement.get("bank_state", ""),
                "bank_pincode": settlement.get("bank_pincode", ""),
                "bank_country": settlement.get("bank_country", ""),
                "bank_phone": settlement.get("bank_phone", ""),
                "bank_email": settlement.get("bank_email", "")
            })
        
        return {
            "success": True,
            "settlements": processed_settlements,
            "count": len(processed_settlements),
            "total_count": settlements.get("count", 0)
        }
        
    except Exception as e:
        frappe.log_error(f"Failed to fetch settlements: {str(e)}", "Razorpay Settlement Error")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def settlement_recon(settlement_id: str):
    """Reconcile settlement with local records"""
    try:
        # Fetch settlement from Razorpay
        settlement_data = fetch_settlement(settlement_id)
        if not settlement_data.get("success"):
            return settlement_data
        
        settlement = settlement_data["settlement"]
        
        # Create or update settlement DocType
        settlement_doc = None
        try:
            settlement_doc = frappe.get_doc("Razorpay Settlement", settlement_id)
        except frappe.DoesNotExistError:
            settlement_doc = frappe.new_doc("Razorpay Settlement")
            settlement_doc.settlement_id = settlement_id
        
        # Update settlement details
        settlement_doc.settlement_id = settlement["id"]
        settlement_doc.entity = settlement["entity"]
        settlement_doc.amount = settlement["amount"]
        settlement_doc.currency = settlement["currency"]
        settlement_doc.status = settlement["status"]
        settlement_doc.created_at = frappe.utils.get_datetime(settlement["created_at"])
        settlement_doc.updated_at = frappe.utils.get_datetime(settlement["updated_at"])
        settlement_doc.fee = settlement["fee"]
        settlement_doc.tax = settlement["tax"]
        settlement_doc.utr = settlement["utr"]
        settlement_doc.settlement_date = frappe.utils.get_date(settlement["settlement_date"]) if settlement["settlement_date"] else None
        settlement_doc.on_hold = settlement["on_hold"]
        settlement_doc.on_hold_until = frappe.utils.get_datetime(settlement["on_hold_until"]) if settlement["on_hold_until"] else None
        settlement_doc.description = settlement["description"]
        settlement_doc.notes = frappe.as_json(settlement["notes"])
        
        # Additional Razorpay settlement fields
        settlement_doc.settlement_type = settlement.get("settlement_type", "regular")
        settlement_doc.bank_account = settlement.get("bank_account", "")
        settlement_doc.ifsc_code = settlement.get("ifsc_code", "")
        settlement_doc.account_number = settlement.get("account_number", "")
        settlement_doc.account_type = settlement.get("account_type", "")
        settlement_doc.beneficiary_name = settlement.get("beneficiary_name", "")
        settlement_doc.beneficiary_email = settlement.get("beneficiary_email", "")
        settlement_doc.beneficiary_mobile = settlement.get("beneficiary_mobile", "")
        settlement_doc.processed_at = frappe.utils.get_datetime(settlement["processed_at"]) if settlement.get("processed_at") else None
        settlement_doc.cancelled_at = frappe.utils.get_datetime(settlement["cancelled_at"]) if settlement.get("cancelled_at") else None
        settlement_doc.failure_reason = settlement.get("failure_reason", "")
        settlement_doc.failure_code = settlement.get("failure_code", "")
        settlement_doc.bank_reference_number = settlement.get("bank_reference_number", "")
        settlement_doc.bank_branch = settlement.get("bank_branch", "")
        settlement_doc.bank_city = settlement.get("bank_city", "")
        settlement_doc.bank_state = settlement.get("bank_state", ""),
        settlement_doc.bank_pincode = settlement.get("bank_pincode", ""),
        settlement_doc.bank_country = settlement.get("bank_country", ""),
        settlement_doc.bank_phone = settlement.get("bank_phone", ""),
        settlement_doc.bank_email = settlement.get("bank_email", "")
        
        settlement_doc.save()
        
        return {
            "success": True,
            "message": f"Settlement {settlement_id} reconciled successfully",
            "settlement_name": settlement_doc.name
        }
        
    except Exception as e:
        frappe.log_error(f"Failed to reconcile settlement {settlement_id}: {str(e)}", "Razorpay Settlement Recon Error")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def create_ondemand_settlement(amount: float, currency: str = "INR", description: str = None):
    """Create on-demand settlement (for immediate settlement of captured payments)"""
    try:
        client = get_razorpay_client()
        
        payload = {
            "amount": int(amount * 100),  # Convert to paise
            "currency": currency,
            "description": description or f"On-demand settlement for {amount} {currency}"
        }
        
        settlement = client.settlement.create_ondemand(payload)
        
        return {
            "success": True,
            "settlement": {
                "id": settlement.get("id"),
                "entity": settlement.get("entity"),
                "amount": settlement.get("amount") / 100 if settlement.get("amount") else 0,
                "currency": settlement.get("currency"),
                "status": settlement.get("status"),
                "created_at": settlement.get("created_at"),
                "updated_at": settlement.get("updated_at"),
                "fee": settlement.get("fee") / 100 if settlement.get("fee") else 0,
                "tax": settlement.get("tax") / 100 if settlement.get("tax") else 0,
                "utr": settlement.get("utr"),
                "settlement_date": settlement.get("settlement_date"),
                "on_hold": settlement.get("on_hold", False),
                "on_hold_until": settlement.get("on_hold_until"),
                "description": settlement.get("description", ""),
                "notes": settlement.get("notes", {}),
                # Additional Razorpay settlement fields
                "settlement_type": "ondemand",
                "bank_account": settlement.get("bank_account", ""),
                "ifsc_code": settlement.get("ifsc_code", ""),
                "account_number": settlement.get("account_number", ""),
                "account_type": settlement.get("account_type", ""),
                "beneficiary_name": settlement.get("beneficiary_name", ""),
                "beneficiary_email": settlement.get("beneficiary_email", ""),
                "beneficiary_mobile": settlement.get("beneficiary_mobile", ""),
                "processed_at": settlement.get("processed_at"),
                "cancelled_at": settlement.get("cancelled_at"),
                "failure_reason": settlement.get("failure_reason", ""),
                "failure_code": settlement.get("failure_code", ""),
                "bank_reference_number": settlement.get("bank_reference_number", ""),
                "bank_branch": settlement.get("bank_branch", ""),
                "bank_city": settlement.get("bank_city", ""),
                "bank_state": settlement.get("bank_state", ""),
                "bank_pincode": settlement.get("bank_pincode", ""),
                "bank_country": settlement.get("bank_country", ""),
                "bank_phone": settlement.get("bank_phone", ""),
                "bank_email": settlement.get("bank_email", "")
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Failed to create on-demand settlement: {str(e)}", "Razorpay Settlement Error")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def fetch_all_ondemand_settlements(from_date: str = None, to_date: str = None, count: int = 10):
    """Fetch all on-demand settlements from Razorpay"""
    try:
        client = get_razorpay_client()
        
        # Prepare parameters
        params = {"count": count}
        if from_date:
            params["from"] = int(frappe.utils.get_timestamp(from_date))
        if to_date:
            params["to"] = int(frappe.utils.get_timestamp(to_date))
        
        settlements = client.settlement.fetch_all_ondemand(params)
        
        # Process settlements
        processed_settlements = []
        for settlement in settlements.get("items", []):
            processed_settlements.append({
                "id": settlement.get("id"),
                "entity": settlement.get("entity"),
                "amount": settlement.get("amount") / 100 if settlement.get("amount") else 0,
                "currency": settlement.get("currency"),
                "status": settlement.get("status"),
                "created_at": settlement.get("created_at"),
                "updated_at": settlement.get("updated_at"),
                "fee": settlement.get("fee") / 100 if settlement.get("fee") else 0,
                "tax": settlement.get("tax") / 100 if settlement.get("tax") else 0,
                "utr": settlement.get("utr"),
                "settlement_date": settlement.get("settlement_date"),
                "on_hold": settlement.get("on_hold", False),
                "on_hold_until": settlement.get("on_hold_until"),
                "description": settlement.get("description", ""),
                "notes": settlement.get("notes", {}),
                # Additional Razorpay settlement fields
                "settlement_type": "ondemand",
                "bank_account": settlement.get("bank_account", ""),
                "ifsc_code": settlement.get("ifsc_code", ""),
                "account_number": settlement.get("account_number", ""),
                "account_type": settlement.get("account_type", ""),
                "beneficiary_name": settlement.get("beneficiary_name", ""),
                "beneficiary_email": settlement.get("beneficiary_email", ""),
                "beneficiary_mobile": settlement.get("beneficiary_mobile", ""),
                "processed_at": settlement.get("processed_at"),
                "cancelled_at": settlement.get("cancelled_at"),
                "failure_reason": settlement.get("failure_reason", ""),
                "failure_code": settlement.get("failure_code", ""),
                "bank_reference_number": settlement.get("bank_reference_number", ""),
                "bank_branch": settlement.get("bank_branch", ""),
                "bank_city": settlement.get("bank_city", ""),
                "bank_state": settlement.get("bank_state", ""),
                "bank_pincode": settlement.get("bank_pincode", ""),
                "bank_country": settlement.get("bank_country", ""),
                "bank_phone": settlement.get("bank_phone", ""),
                "bank_email": settlement.get("bank_email", "")
            })
        
        return {
            "success": True,
            "settlements": processed_settlements,
            "count": len(processed_settlements),
            "total_count": settlements.get("count", 0)
        }
        
    except Exception as e:
        frappe.log_error(f"Failed to fetch on-demand settlements: {str(e)}", "Razorpay Settlement Error")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def fetch_automatic_settlements(from_date: str = None, to_date: str = None, count: int = 10):
    """Fetch automatic settlements created by Razorpay based on captured payments"""
    try:
        client = get_razorpay_client()
        
        # Prepare parameters
        params = {"count": count}
        if from_date:
            params["from"] = int(frappe.utils.get_timestamp(from_date))
        if to_date:
            params["to"] = int(frappe.utils.get_timestamp(to_date))
        
        # Fetch regular settlements (automatic settlements)
        settlements = client.settlement.all(params)
        
        # Process settlements
        processed_settlements = []
        for settlement in settlements.get("items", []):
            # Only include regular settlements (not on-demand)
            if settlement.get("settlement_type") != "ondemand":
                processed_settlements.append({
                    "id": settlement.get("id"),
                    "entity": settlement.get("entity"),
                    "amount": settlement.get("amount") / 100 if settlement.get("amount") else 0,
                    "currency": settlement.get("currency"),
                    "status": settlement.get("status"),
                    "created_at": settlement.get("created_at"),
                    "updated_at": settlement.get("updated_at"),
                    "fee": settlement.get("fee") / 100 if settlement.get("fee") else 0,
                    "tax": settlement.get("tax") / 100 if settlement.get("tax") else 0,
                    "utr": settlement.get("utr"),
                    "settlement_date": settlement.get("settlement_date"),
                    "on_hold": settlement.get("on_hold", False),
                    "on_hold_until": settlement.get("on_hold_until"),
                    "description": settlement.get("description", ""),
                    "notes": settlement.get("notes", {}),
                    # Additional Razorpay settlement fields
                    "settlement_type": "regular",
                    "bank_account": settlement.get("bank_account", ""),
                    "ifsc_code": settlement.get("ifsc_code", ""),
                    "account_number": settlement.get("account_number", ""),
                    "account_type": settlement.get("account_type", ""),
                    "beneficiary_name": settlement.get("beneficiary_name", ""),
                    "beneficiary_email": settlement.get("beneficiary_email", ""),
                    "beneficiary_mobile": settlement.get("beneficiary_mobile", ""),
                    "processed_at": settlement.get("processed_at"),
                    "cancelled_at": settlement.get("cancelled_at"),
                    "failure_reason": settlement.get("failure_reason", ""),
                    "failure_code": settlement.get("failure_code", ""),
                    "bank_reference_number": settlement.get("bank_reference_number", ""),
                    "bank_branch": settlement.get("bank_branch", ""),
                    "bank_city": settlement.get("bank_city", ""),
                    "bank_state": settlement.get("bank_state", ""),
                    "bank_pincode": settlement.get("bank_pincode", ""),
                    "bank_country": settlement.get("bank_country", ""),
                    "bank_phone": settlement.get("bank_phone", ""),
                    "bank_email": settlement.get("bank_email", "")
                })
        
        return {
            "success": True,
            "settlements": processed_settlements,
            "count": len(processed_settlements),
            "total_count": settlements.get("count", 0)
        }
        
    except Exception as e:
        frappe.log_error(f"Failed to fetch automatic settlements: {str(e)}", "Razorpay Settlement Error")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_settlement_cycle_info():
    """Get information about settlement cycle and bank account details"""
    try:
        client = get_razorpay_client()
        
        # Get account details (this might include settlement cycle info)
        account = client.account.fetch()
        
        return {
            "success": True,
            "account": {
                "id": account.get("id"),
                "name": account.get("name"),
                "email": account.get("email"),
                "contact": account.get("contact"),
                "type": account.get("type"),
                "profile": account.get("profile", {}),
                "bank_accounts": account.get("bank_accounts", []),
                "settlement_cycle": account.get("settlement_cycle", {}),
                "settlement_schedule": account.get("settlement_schedule", {})
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Failed to fetch settlement cycle info: {str(e)}", "Razorpay Settlement Error")
        return {"success": False, "error": str(e)}

