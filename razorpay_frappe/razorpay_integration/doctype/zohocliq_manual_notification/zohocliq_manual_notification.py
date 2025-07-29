import frappe
from frappe.model.document import Document


class ZohoCliqManualNotification(Document):
	def validate(self):
		"""Validate the notification before sending."""
		if self.template_type == "Simple Message":
			# For Simple Message, only message field is mandatory
			if not self.message:
				frappe.throw("Message is required for Simple Message template")
		else:
			# For other template types, validate template-specific fields
			self.validate_template_fields()
	
	def validate_template_fields(self):
		"""Validate required fields based on template type."""
		if self.template_type == "New Project":
			if not self.project_id:
				frappe.throw("Project ID is required for New Project template")
			if not self.customer_name:
				frappe.throw("Customer Name is required for New Project template")
		
		elif self.template_type == "Task Assignment":
			if not self.task_id:
				frappe.throw("Task ID is required for Task Assignment template")
			# Removed mandatory requirement for assigned_to since tasks might not have assigned users
		
		elif self.template_type == "Material Request":
			if not self.request_id:
				frappe.throw("Request ID is required for Material Request template")
			if not self.requested_by:
				frappe.throw("Requested By is required for Material Request template")
		
		elif self.template_type == "Meeting Schedule":
			if not self.meeting_title:
				frappe.throw("Meeting Title is required for Meeting Schedule template")
			if not self.scheduled_by:
				frappe.throw("Scheduled By is required for Meeting Schedule template")
			if not self.participants:
				frappe.throw("Participants are required for Meeting Schedule template")
			if not self.date_time:
				frappe.throw("Date & Time is required for Meeting Schedule template")
		
		elif self.template_type == "Status Update":
			if not self.status_title:
				frappe.throw("Status Title is required for Status Update template")
			if not self.status_details:
				frappe.throw("Status Details are required for Status Update template")
	
	def before_save(self):
		"""Auto-populate fields based on selected documents."""
		if self.template_type == "New Project" and self.project_id:
			self.auto_populate_project_fields()
		
		elif self.template_type == "Task Assignment" and self.task_id:
			self.auto_populate_task_fields()
		
		elif self.template_type == "Material Request" and self.request_id:
			self.auto_populate_material_request_fields()
	
	def auto_populate_project_fields(self):
		"""Auto-populate project-related fields."""
		try:
			project = frappe.get_doc("Project", self.project_id)
			if not self.customer_name and project.customer:
				self.customer_name = project.customer
			if not self.assigned_to and project.project_manager:
				self.assigned_to = project.project_manager
			if not self.erp_link:
				base_url = frappe.utils.get_url()
				self.erp_link = f"{base_url}/app/project/{self.project_id}"
		except Exception as e:
			frappe.log_error(f"Error auto-populating project fields: {str(e)}")
	
	def auto_populate_task_fields(self):
		"""Auto-populate task-related fields."""
		try:
			task = frappe.get_doc("Task", self.task_id)
			
			# Get task name from subject or name
			if not self.task_name:
				self.task_name = task.subject or task.name
			
			# Get assigned user from assignments array or direct field
			if not self.assigned_to:
				if hasattr(task, 'assignments') and task.assignments:
					# Get the first assigned user from assignments
					self.assigned_to = task.assignments[0].owner if task.assignments else None
				elif hasattr(task, 'assigned_to'):
					self.assigned_to = task.assigned_to
			
			# Get due date if not already set
			if not self.due_date and task.exp_end_date:
				self.due_date = task.exp_end_date
			
			# Get priority if available and not already set
			if not self.priority and hasattr(task, 'priority'):
				self.priority = task.priority or 'Medium'
			
			# Build ERP link
			if not self.erp_link:
				base_url = frappe.utils.get_url()
				self.erp_link = f"{base_url}/app/task/{self.task_id}"
				
		except Exception as e:
			frappe.log_error(f"Error auto-populating task fields: {str(e)}")
	
	def auto_populate_material_request_fields(self):
		"""Auto-populate material request fields."""
		try:
			mr = frappe.get_doc("Material Request", self.request_id)
			
			# Get requested by from owner or modified_by if not already set
			if not self.requested_by:
				try:
					self.requested_by = mr.owner or mr.modified_by
				except Exception as e:
					frappe.log_error(f"Error getting requested_by for MR {self.request_id}: {str(e)}")
			
			# Get urgency if available and not already set
			if not self.urgency:
				try:
					self.urgency = getattr(mr, 'urgency', 'Normal') or 'Normal'
				except Exception as e:
					frappe.log_error(f"Error getting urgency for MR {self.request_id}: {str(e)}")
					self.urgency = 'Normal'
			
			# Build ERP link
			if not self.erp_link:
				base_url = frappe.utils.get_url()
				self.erp_link = f"{base_url}/app/material-request/{self.request_id}"
				
		except Exception as e:
			frappe.log_error(f"Error auto-populating material request fields: {str(e)}")
	
	def after_insert(self):
		"""Send the notification based on template type."""
		if self.template_type == "Simple Message":
			self.send_simple_message()
		else:
			self.send_template_message()
	
	def send_simple_message(self):
		"""Send a simple text message."""
		if self.channel == "Other":
			if not self.custom_channel_name:
				frappe.throw("Please provide Custom Channel Name")
			from razorpay_frappe.utils import build_zohocliq_webhook_url, send_zohocliq_message
			webhook_url = build_zohocliq_webhook_url(self.custom_channel_name)
			send_zohocliq_message(webhook_url, self.message)
		else:
			from razorpay_frappe.utils import post_to_zohocliq
			post_to_zohocliq(self.message, self.channel)
		frappe.msgprint("Notification sent to ZohoCliq")
	
	def send_template_message(self):
		"""Send a templated message based on the selected template."""
		from razorpay_frappe.utils import (
			send_new_project_notification,
			send_task_assignment_notification,
			send_material_request_notification,
			send_meeting_notification,
			send_status_update,
			build_zohocliq_webhook_url,
			send_zohocliq_message_with_thread
		)
		
		try:
			if self.template_type == "New Project":
				# Handle None values for assigned_to
				assigned_to = self.assigned_to or ""
				
				message_id = send_new_project_notification(
					self.project_id,
					assigned_to,
					self.customer_name,
					self.channel
				)
			
			elif self.template_type == "Task Assignment":
				# Handle None values for assigned_to
				assigned_to = self.assigned_to or ""
				
				# Get task description from the form field
				description = self.task_description or None
				
				message_id = send_task_assignment_notification(
					self.task_id,
					self.task_name,
					assigned_to,
					self.due_date,
					self.priority,
					self.channel,
					description
				)
			
			elif self.template_type == "Material Request":
				# Get items from material request using the improved function
				items = []
				if self.request_id:
					try:
						# Use the get_material_request_details function to get items
						details = get_material_request_details(self.request_id)
						if details and not details.get('error'):
							items = details.get('items', [])
						else:
							# Fallback if function fails
							mr = frappe.get_doc("Material Request", self.request_id)
							items = [item.item_name for item in mr.items if item.item_name]
					except:
						items = ["Item 1", "Item 2"]  # Fallback
				
				# Handle None values
				requested_by = self.requested_by or ""
				
				message_id = send_material_request_notification(
					self.request_id,
					requested_by,
					items,
					self.urgency,
					self.channel
				)
			
			elif self.template_type == "Meeting Schedule":
				# Handle None values
				scheduled_by = self.scheduled_by or ""
				participants = [p.strip() for p in (self.participants or "").split(",") if p.strip()]
				
				message_id = send_meeting_notification(
					self.meeting_title,
					scheduled_by,
					participants,
					str(self.date_time),
					self.duration,
					self.channel
				)
			
			elif self.template_type == "Status Update":
				# Parse status details JSON
				details = {}
				if self.status_details:
					try:
						import json
						details = json.loads(self.status_details)
					except:
						details = {"Status": self.status_details}
				
				# Handle None values
				assigned_to = self.assigned_to or ""
				
				message_id = send_status_update(
					self.status_title,
					"Updated",  # Default status
					details,
					assigned_to,
					self.channel
				)
			
			frappe.msgprint(f"Templated notification sent to ZohoCliq (Message ID: {message_id})")
			
		except Exception as e:
			frappe.log_error(f"Error sending templated notification: {str(e)}")
			frappe.throw(f"Failed to send notification: {str(e)}")


@frappe.whitelist()
def get_project_details(project_id):
	"""Get project details for auto-population."""
	try:
		project = frappe.get_doc("Project", project_id)
		
		# Try different possible customer field names
		customer_name = None
		if hasattr(project, 'customer') and project.customer:
			customer_name = project.customer
		elif hasattr(project, 'customer_name') and project.customer_name:
			customer_name = project.customer_name
		elif hasattr(project, 'party_name') and project.party_name:
			customer_name = project.party_name
		
		# If customer is a link field, get the customer name
		if customer_name and frappe.db.exists("Customer", customer_name):
			customer_doc = frappe.get_doc("Customer", customer_name)
			customer_name = customer_doc.customer_name or customer_name
		
		return {
			"customer_name": customer_name,
			"assigned_to": getattr(project, 'project_manager', None) or getattr(project, 'assigned_to', None),
			"erp_link": f"{frappe.utils.get_url()}/app/project/{project_id}"
		}
	except Exception as e:
		frappe.log_error(f"Error fetching project details for {project_id}: {str(e)}")
		return {"error": str(e)}


@frappe.whitelist()
def get_task_details(task_id):
	"""Get task details for auto-population."""
	try:
		task = frappe.get_doc("Task", task_id)
		
		# Get task name from subject or name
		task_name = task.subject or task.name
		
		# Get assigned users from assignments array
		assigned_to = None
		try:
			if hasattr(task, 'assignments') and task.assignments:
				# Get the first assigned user
				assigned_to = task.assignments[0].owner if task.assignments else None
			elif hasattr(task, 'assigned_to'):
				assigned_to = task.assigned_to
		except Exception as e:
			frappe.log_error(f"Error getting assigned_to for task {task_id}: {str(e)}")
			assigned_to = None
		
		# Get due date from expected end date
		due_date = getattr(task, 'exp_end_date', None)
		
		# Get priority if available
		priority = getattr(task, 'priority', 'Medium')
		
		# Get task description
		description = getattr(task, 'description', None)
		
		# Build ERP link
		base_url = frappe.utils.get_url()
		erp_link = f"{base_url}/app/task/{task_id}"
		
		result = {
			"task_name": task_name,
			"assigned_to": assigned_to,
			"due_date": due_date,
			"priority": priority,
			"description": description,
			"erp_link": erp_link
		}
		
		# Log successful result for debugging (concise)
		frappe.log_error(f"Task {task_id} details fetched successfully", "Task Details")
		
		return result
	except Exception as e:
		frappe.log_error(f"Error fetching task details for {task_id}: {str(e)}")
		return {"error": str(e)}


@frappe.whitelist()
def get_material_request_details(request_id):
	"""Get material request details for auto-population."""
	try:
		mr = frappe.get_doc("Material Request", request_id)
		
		# Get requested by from owner or modified_by
		requested_by = None
		try:
			requested_by = mr.owner or mr.modified_by
		except Exception as e:
			frappe.log_error(f"Error getting requested_by for MR {request_id}: {str(e)}")
			requested_by = None
		
		# Get material request title
		request_title = None
		try:
			request_title = mr.title or mr.name
		except Exception as e:
			frappe.log_error(f"Error getting request_title for MR {request_id}: {str(e)}")
			request_title = request_id
		
		# Get urgency level
		urgency = None
		try:
			urgency = getattr(mr, 'urgency', 'Normal')
		except Exception as e:
			frappe.log_error(f"Error getting urgency for MR {request_id}: {str(e)}")
			urgency = 'Normal'
		
		# Count items
		items_count = 0
		items = []
		try:
			if hasattr(mr, 'items') and mr.items:
				items_count = len(mr.items)
				for item in mr.items:
					if hasattr(item, 'item_name') and item.item_name:
						items.append(item.item_name)
					elif hasattr(item, 'item_code') and item.item_code:
						items.append(item.item_code)
		except Exception as e:
			frappe.log_error(f"Error getting items for MR {request_id}: {str(e)}")
			items = ["Item 1", "Item 2"]  # Fallback
			items_count = len(items)
		
		# Build ERP link
		base_url = frappe.utils.get_url()
		erp_link = f"{base_url}/app/material-request/{request_id}"
		
		result = {
			"requested_by": requested_by,
			"request_title": request_title,
			"urgency": urgency,
			"items_count": items_count,
			"items": items,
			"erp_link": erp_link
		}
		
		# Log successful result for debugging (concise)
		frappe.log_error(f"MR {request_id} details fetched successfully", "MR Details")
		
		return result
	except Exception as e:
		frappe.log_error(f"Error fetching material request details for {request_id}: {str(e)}")
		return {"error": str(e)} 