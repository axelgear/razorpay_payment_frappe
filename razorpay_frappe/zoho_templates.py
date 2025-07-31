import frappe


def create_new_project_template(project_id: str, assigned_to: str, customer_name: str, erp_link: str = None):
	"""Create ZohoCliq template for new project notification."""
	mention = f"<users/{assigned_to}>" if assigned_to else ""
	
	message = {
		"card": {
			"title": "NEW PROJECT ADDED",
			"theme": "modern-inline",
		},
		"text": f"**New Project Created** {mention}",
		"slides": [
			{
				"type": "table",
				"title": "Project Details",
				"data": {
					"headers": ["Field", "Value"],
					"rows": [
						{"Field": "Project ID", "Value": project_id},
						{"Field": "Customer", "Value": customer_name},
						{"Field": "Assigned To", "Value": assigned_to or "Not assigned"}
					]
				}
			}
		]
	}
	
	if erp_link:
		message["buttons"] = [
			{
				"label": "View Project",
				"type": "+",
				"action": {
					"type": "open.url",
					"data": {"web": erp_link}
				}
			}
		]
	
	return message


def create_status_update_template(title: str, status: str, details: dict, assigned_to: str = None, erp_link: str = None):
	"""Create ZohoCliq template for status update notification."""
	mention = f"<users/{assigned_to}>" if assigned_to else ""
	
	message = {
		"card": {
			"title": title.upper(),
			"theme": "modern-inline",
		},
		"text": f"**{title}** {mention}",
		"slides": [
			{
				"type": "table",
				"title": "Status Details",
				"data": {
					"headers": ["Field", "Value"],
					"rows": [{"Field": k, "Value": v} for k, v in details.items()]
				}
			}
		]
	}
	
	if erp_link:
		message["buttons"] = [
			{
				"label": "View Details",
				"type": "+",
				"action": {
					"type": "open.url",
					"data": {"web": erp_link}
				}
			}
		]
	
	return message


def create_task_assignment_template(task_id: str, task_name: str, assigned_to: str, due_date: str = None, priority: str = "Medium", erp_link: str = None, description: str = None):
	"""Create ZohoCliq template for task assignment notification."""
	mention = f"<users/{assigned_to}>" if assigned_to else ""
	due_date_str = due_date if due_date else "Not set"
	description_str = description if description else "No description"
	
	message = {
		"card": {
			"title": "TASK ASSIGNED",
			"theme": "modern-inline",
		},
		"text": f"**Task Assigned** {mention}",
		"slides": [
			{
				"type": "table",
				"title": "Task Details",
				"data": {
					"headers": ["Field", "Value"],
					"rows": [
						{"Field": "Task ID", "Value": task_id},
						{"Field": "Task Name", "Value": task_name},
						{"Field": "Assigned To", "Value": assigned_to or "Not assigned"},
						{"Field": "Priority", "Value": priority},
						{"Field": "Due Date", "Value": due_date_str},
						{"Field": "Description", "Value": description_str}
					]
				}
			}
		]
	}
	
	if erp_link:
		message["buttons"] = [
			{
				"label": "View Task",
				"type": "+",
				"action": {
					"type": "open.url",
					"data": {"web": erp_link}
				}
			}
		]
	
	return message


def create_meeting_schedule_template(meeting_title: str, scheduled_by: str, participants: list, date_time: str, duration: str = "1 hour", erp_link: str = None):
	"""Create ZohoCliq template for meeting schedule notification."""
	participants_str = ", ".join(participants) if participants else "No participants"
	
	message = {
		"card": {
			"title": "MEETING SCHEDULED",
			"theme": "modern-inline",
		},
		"text": f"**Meeting Scheduled**",
		"slides": [
			{
				"type": "table",
				"title": "Meeting Details",
				"data": {
					"headers": ["Field", "Value"],
					"rows": [
						{"Field": "Meeting Title", "Value": meeting_title},
						{"Field": "Scheduled By", "Value": scheduled_by},
						{"Field": "Date & Time", "Value": date_time},
						{"Field": "Duration", "Value": duration},
						{"Field": "Participants", "Value": participants_str}
					]
				}
			}
		]
	}
	
	if erp_link:
		message["buttons"] = [
			{
				"label": "View Meeting",
				"type": "+",
				"action": {
					"type": "open.url",
					"data": {"web": erp_link}
				}
			}
		]
	
	return message


def create_material_request_template(request_id: str, requested_by: str, items: list, urgency: str = "Normal", erp_link: str = None):
	"""Create ZohoCliq template for material request notification."""
	items_str = "\n".join([f"- {item}" for item in items]) if items else "No items specified"
	
	message = {
		"card": {
			"title": "MATERIAL REQUEST",
			"theme": "modern-inline",
		},
		"text": f"**Material Request Created**",
		"slides": [
			{
				"type": "table",
				"title": "Request Details",
				"data": {
					"headers": ["Field", "Value"],
					"rows": [
						{"Field": "Request ID", "Value": request_id},
						{"Field": "Requested By", "Value": requested_by},
						{"Field": "Urgency", "Value": urgency},
						{"Field": "Items", "Value": items_str}
					]
				}
			}
		]
	}
	
	if erp_link:
		message["buttons"] = [
			{
				"label": "View Request",
				"type": "+",
				"action": {
					"type": "open.url",
					"data": {"web": erp_link}
				}
			}
		]
	
	return message


def create_thread_message_template(parent_message_id: str, thread_title: str, initial_message: str):
	"""Create ZohoCliq template for thread message."""
	return {
		"text": initial_message,
		"parent_message_id": parent_message_id,
		"thread_title": thread_title
	}


def create_quote_update_template(quote_name: str, quote_details: dict, payment_link: str, qr_image_url: str = None, is_update: bool = False):
	"""Create ZohoCliq template for quote notification."""
	
	# Create a very simple template to stay within 140 character limit
	if is_update:
		title = "QUOTE UPDATED"
		text = f"Quote Updated: {quote_name}"
	else:
		title = "NEW QUOTE"
		text = f"New Quote: {quote_name}"
	
	# Truncate customer name if too long
	customer_name = quote_details.get("customer_name", "")
	if len(customer_name) > 20:
		customer_name = customer_name[:17] + "..."
	
	# Truncate amount if too long
	amount_str = f"{quote_details.get('currency', '')} {quote_details.get('grand_total', 0)}"
	if len(amount_str) > 15:
		amount_str = amount_str[:12] + "..."
	
	message = {
		"card": {
			"title": title,
			"theme": "modern-inline",
		},
		"text": text,
		"slides": [
			{
				"type": "table",
				"title": "Details",
				"data": {
					"headers": ["Field", "Value"],
					"rows": [
						{"Field": "Customer", "Value": customer_name},
						{"Field": "Amount", "Value": amount_str}
					]
				}
			}
		],
		"buttons": [
			{
				"label": "Payment Link",
				"type": "+",
				"action": {
					"type": "open.url",
					"data": {"web": payment_link}
				}
			}
		]
	}
	
	return message


def create_simple_quote_notification(quote_name: str, is_update: bool = False):
	"""Create a simple text notification for quotes when template is too long."""
	if is_update:
		return f"Quote Updated: {quote_name}"
	else:
		return f"New Quote Created: {quote_name}" 