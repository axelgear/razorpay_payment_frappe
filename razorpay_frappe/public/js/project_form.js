frappe.ui.form.on('Project', {
    refresh: function(frm) {
        // Add ZohoCliq notification button
        frm.add_custom_button(__('Send ZohoCliq Notification'), function() {
            frappe.call({
                method: 'razorpay_frappe.utils.send_project_notification_with_thread',
                args: {
                    project_id: frm.doc.name,
                    channel: 'Project'
                },
                callback: function(r) {
                    if (r.exc) {
                        frappe.msgprint({
                            title: __('Error'),
                            message: __('Failed to send notification: ') + r.exc,
                            indicator: 'red'
                        });
                    } else if (r.message && r.message.success) {
                        frappe.msgprint({
                            title: __('Success'),
                            message: __('Project notification sent successfully! Thread ID: ') + (r.message.thread_id || 'N/A'),
                            indicator: 'green'
                        });
                        frm.reload_doc();
                    } else {
                        frappe.msgprint({
                            title: __('Error'),
                            message: __('Failed to send notification: ') + (r.message.error || 'Unknown error'),
                            indicator: 'red'
                        });
                    }
                }
            });
        }, __('ZohoCliq'));
        
        // Add button to send task notification to thread (if thread exists)
        if (frm.doc.zohocliq_thread_id) {
            frm.add_custom_button(__('Send Task to Thread'), function() {
                frappe.prompt([
                    {
                        fieldname: 'task_id',
                        fieldtype: 'Link',
                        options: 'Task',
                        label: __('Task ID'),
                        reqd: 1,
                        description: __('Enter the Task ID to send notification to project thread')
                    }
                ], function(values) {
                    frappe.call({
                        method: 'razorpay_frappe.utils.send_task_notification_to_project_thread',
                        args: {
                            task_id: values.task_id,
                            project_id: frm.doc.name
                        },
                        callback: function(r) {
                            if (r.exc) {
                                frappe.msgprint({
                                    title: __('Error'),
                                    message: __('Failed to send task notification: ') + r.exc,
                                    indicator: 'red'
                                });
                            } else if (r.message && r.message.success) {
                                frappe.msgprint({
                                    title: __('Success'),
                                    message: __('Task notification sent to project thread!'),
                                    indicator: 'green'
                                });
                            } else {
                                frappe.msgprint({
                                    title: __('Error'),
                                    message: __('Failed to send task notification: ') + (r.message.error || 'Unknown error'),
                                    indicator: 'red'
                                });
                            }
                        }
                    });
                }, __('Send Task Notification'), __('Send'));
            }, __('ZohoCliq'));
        }
    }
}); 