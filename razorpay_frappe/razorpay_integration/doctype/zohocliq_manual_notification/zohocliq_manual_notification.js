frappe.ui.form.on('ZohoCliq Manual Notification', {
	refresh: function(frm) {
		// Add custom buttons for quick actions
		frm.add_custom_button(__('Test Connection'), function() {
			frm.call({
				method: 'razorpay_frappe.utils.post_to_zohocliq',
				args: {
					message: 'Test message from ERPNext',
					channel: frm.doc.channel || 'Notification'
				},
				callback: function(r) {
					if (r.exc) {
						frappe.msgprint(__('Test failed: ') + r.exc, 'Error');
					} else {
						frappe.msgprint(__('Test message sent successfully!'), 'Success');
					}
				}
			});
		});
	},

	template_type: function(frm) {
		// Clear fields when template type changes
		// Clear all template-specific fields
		frm.set_value('project_id', '');
		frm.set_value('assigned_to', '');
		frm.set_value('customer_name', '');
		frm.set_value('erp_link', '');
		frm.set_value('task_id', '');
		frm.set_value('task_name', '');
		frm.set_value('due_date', '');
		frm.set_value('priority', 'Medium');
		frm.set_value('request_id', '');
		frm.set_value('requested_by', '');
		frm.set_value('urgency', 'Normal');
		frm.set_value('meeting_title', '');
		frm.set_value('scheduled_by', '');
		frm.set_value('participants', '');
		frm.set_value('date_time', '');
		frm.set_value('duration', '1 hour');
		frm.set_value('status_title', '');
		frm.set_value('status_details', '');
		frm.set_value('message', '');
		
		// Set default channel based on template type
		if (frm.doc.template_type) {
			const channel_map = {
				'New Project': 'Project',
				'Task Assignment': 'Project',
				'Material Request': 'Purchase',
				'Meeting Schedule': 'Notification',
				'Status Update': 'Notification'
			};
			
			if (channel_map[frm.doc.template_type] && !frm.doc.channel) {
				frm.set_value('channel', channel_map[frm.doc.template_type]);
			}
		}
		
		// Refresh the form to show/hide fields based on dependencies
		frm.refresh();
	},

	project_id: function(frm) {
		// Auto-populate project details
		if (frm.doc.project_id && frm.doc.template_type === 'New Project') {
			frm.call({
				method: 'get_project_details',
				args: { project_id: frm.doc.project_id },
				callback: function(r) {
					if (r.message && !r.message.error) {
						const data = r.message;
						// Always populate customer name from project
						if (data.customer_name) {
							frm.set_value('customer_name', data.customer_name);
						}
						// Populate assigned_to if not already set
						if (data.assigned_to && !frm.doc.assigned_to) {
							frm.set_value('assigned_to', data.assigned_to);
						}
						// Always update ERP link
						if (data.erp_link) {
							frm.set_value('erp_link', data.erp_link);
						}
						
						frappe.msgprint(__('Project details auto-populated successfully!'), 'Success');
					} else if (r.message && r.message.error) {
						frappe.msgprint(__('Error fetching project details: ') + r.message.error, 'Error');
					} else {
						frappe.msgprint(__('No project details found'), 'Warning');
					}
				}
			});
		}
	},

	task_id: function(frm) {
		// Auto-populate task details
		if (frm.doc.task_id && frm.doc.template_type === 'Task Assignment') {
			frm.call({
				method: 'get_task_details',
				args: { task_id: frm.doc.task_id },
				callback: function(r) {
					if (r.message && !r.message.error) {
						const data = r.message;
						
						// Always populate task name if available
						if (data.task_name && !frm.doc.task_name) {
							frm.set_value('task_name', data.task_name);
						}
						
						// Populate assigned_to if available and not already set
						if (data.assigned_to && !frm.doc.assigned_to) {
							frm.set_value('assigned_to', data.assigned_to);
						}
						
						// Populate due date if available and not already set
						if (data.due_date && !frm.doc.due_date) {
							frm.set_value('due_date', data.due_date);
						}
						
						// Populate task description if available
						if (data.description && !frm.doc.task_description) {
							// Clean HTML tags from description
							let clean_description = data.description.replace(/<[^>]*>/g, '');
							clean_description = clean_description.replace(/&nbsp;/g, ' ').trim();
							frm.set_value('task_description', clean_description);
						}
						
						// Always update ERP link
						if (data.erp_link) {
							frm.set_value('erp_link', data.erp_link);
						}
						
						frappe.msgprint(__('Task details auto-populated successfully!'), 'Success');
					} else if (r.message && r.message.error) {
						frappe.msgprint(__('Error fetching task details: ') + r.message.error, 'Error');
					} else {
						frappe.msgprint(__('No task details found'), 'Warning');
					}
				}
			});
		}
	},

	request_id: function(frm) {
		// Auto-populate material request details
		if (frm.doc.request_id && frm.doc.template_type === 'Material Request') {
			frm.call({
				method: 'get_material_request_details',
				args: { request_id: frm.doc.request_id },
				callback: function(r) {
					if (r.message && !r.message.error) {
						const data = r.message;
						
						// Populate requested_by if available and not already set
						if (data.requested_by && !frm.doc.requested_by) {
							frm.set_value('requested_by', data.requested_by);
						}
						
						// Always update ERP link
						if (data.erp_link) {
							frm.set_value('erp_link', data.erp_link);
						}
						
						// Show items count if available
						if (data.items_count) {
							frappe.msgprint(__('Material Request loaded with ') + data.items_count + __(' items'), 'Success');
						} else {
							frappe.msgprint(__('Material Request details auto-populated successfully!'), 'Success');
						}
					} else if (r.message && r.message.error) {
						frappe.msgprint(__('Error fetching material request details: ') + r.message.error, 'Error');
					} else {
						frappe.msgprint(__('No material request details found'), 'Warning');
					}
				}
			});
		}
	},

	channel: function(frm) {
		// Update custom channel name field visibility
		if (frm.doc.channel === 'Other') {
			frm.set_df_property('custom_channel_name', 'hidden', 0);
		} else {
			frm.set_df_property('custom_channel_name', 'hidden', 1);
		}
	}
});

// Add field formatting and validation
frappe.ui.form.on('ZohoCliq Manual Notification', {
	participants: function(frm) {
		// Format participants field with email validation
		if (frm.doc.participants) {
			const emails = frm.doc.participants.split(',').map(email => email.trim());
			const valid_emails = emails.filter(email => email.includes('@'));
			if (valid_emails.length !== emails.length) {
				frappe.msgprint(__('Please enter valid email addresses separated by commas'), 'Warning');
			}
		}
	},

	status_details: function(frm) {
		// Validate JSON format for status details
		if (frm.doc.status_details) {
			try {
				JSON.parse(frm.doc.status_details);
			} catch (e) {
				frappe.msgprint(__('Status Details should be in JSON format: {"Field": "Value"}'), 'Warning');
			}
		}
	},

	message: function(frm) {
		// Validate message field for Simple Message template
		if (frm.doc.template_type === 'Simple Message' && !frm.doc.message) {
			frappe.msgprint(__('Message is required for Simple Message template'), 'Warning');
		}
	}
});

// Add help text and tooltips
frappe.ui.form.on('ZohoCliq Manual Notification', {
	refresh: function(frm) {
		// Add help text for template types
		const template_help = {
			'New Project': 'Creates a project notification with discussion thread',
			'Task Assignment': 'Assigns a task to a team member',
			'Material Request': 'Notifies about material requirements',
			'Meeting Schedule': 'Schedules meetings with participants',
			'Status Update': 'Updates project/task status',
			'Simple Message': 'Send a plain text message'
		};
		
		frm.set_df_property('template_type', 'description', 
			template_help[frm.doc.template_type] || 'Select a template type');
		
		// Add help for status details
		if (frm.doc.template_type === 'Status Update') {
			frm.set_df_property('status_details', 'description', 
				'Enter details in JSON format: {"Status": "In Progress", "Progress": "75%"}');
		}
		
		// Add help for task assignment
		if (frm.doc.template_type === 'Task Assignment') {
			frm.set_df_property('task_id', 'description', 
				'Select a task to auto-populate task details');
			frm.set_df_property('assigned_to', 'description', 
				'User who will be assigned to this task');
		}
		
		// Add help for material request
		if (frm.doc.template_type === 'Material Request') {
			frm.set_df_property('request_id', 'description', 
				'Select a material request to auto-populate details');
			frm.set_df_property('requested_by', 'description', 
				'User who requested the materials');
		}
	}
}); 