frappe.ui.form.on('Razorpay Payment Link', {
    refresh: function(frm) {
        // Add sync button to manually sync payment status from Razorpay
        frm.add_custom_button(__('Sync Status'), function() {
            sync_payment_link_status(frm.doc.name);
        }, __('Razorpay'));
        
        // Add button to get detailed payment information
        frm.add_custom_button(__('Payment Details'), function() {
            get_payment_link_details(frm.doc.name);
        }, __('Razorpay'));
        
        // Add button to view payment details
        frm.add_custom_button(__('View Payments'), function() {
            get_payment_details_for_link(frm.doc.name);
        }, __('Razorpay'));
        
        // Add refresh button to reload the form
        frm.add_custom_button(__('Refresh'), function() {
            frm.reload_doc();
        }, __('Razorpay'));
    }
});

function sync_payment_link_status(payment_link_name) {
    frappe.call({
        method: 'razorpay_frappe.webhook_handler.sync_payment_link_status',
        args: {
            payment_link_name: payment_link_name
        },
        callback: function(r) {
            if (r.exc) {
                frappe.msgprint(__('Error syncing payment link status: ') + r.exc);
            } else if (r.message && r.message.success) {
                frappe.msgprint({
                    title: __('Status Synced'),
                    message: __('Payment link status synced successfully!') + '<br><br>' +
                             __('Status: ') + r.message.status + '<br>' +
                             __('Amount Paid: ₹') + r.message.amount_paid + '<br>' +
                             __('Total Amount: ₹') + r.message.total_amount + '<br>' +
                             __('Remaining Amount: ₹') + r.message.remaining_amount,
                    indicator: 'green'
                });
                // Refresh the form to show updated values
                frappe.model.sync(r.message);
                cur_frm.refresh();
            } else {
                frappe.msgprint(__('Error: ') + (r.message ? r.message.error : 'Unknown error'));
            }
        }
    });
}

function get_payment_link_details(payment_link_name) {
    frappe.call({
        method: 'razorpay_frappe.webhook_handler.get_payment_link_details',
        args: {
            payment_link_name: payment_link_name
        },
        callback: function(r) {
            if (r.exc) {
                frappe.msgprint(__('Error getting payment details: ') + r.exc);
            } else if (r.message && r.message.success) {
                let message = __('Payment Link Details:') + '<br><br>';
                message += __('Status: ') + r.message.payment_link.status + '<br>';
                message += __('Amount: ₹') + r.message.payment_link.amount + '<br>';
                message += __('Amount Paid: ₹') + r.message.payment_link.amount_paid + '<br>';
                message += __('Remaining: ₹') + r.message.payment_link.remaining_amount + '<br>';
                message += __('Customer: ') + r.message.payment_link.customer + '<br>';
                message += __('Quotation: ') + r.message.payment_link.quotation + '<br><br>';
                
                if (r.message.payments && r.message.payments.length > 0) {
                    message += __('Payment Details:') + '<br>';
                    r.message.payments.forEach(function(payment, index) {
                        message += (index + 1) + '. Payment ID: ' + payment.payment_id + '<br>';
                        message += '   Amount: ₹' + payment.amount + '<br>';
                        message += '   Status: ' + payment.status + '<br>';
                        message += '   Method: ' + payment.method + '<br><br>';
                    });
                } else {
                    message += __('No payments found.');
                }
                
                frappe.msgprint({
                    title: __('Payment Details'),
                    message: message,
                    indicator: 'blue'
                });
            } else {
                frappe.msgprint(__('Error: ') + (r.message ? r.message.error : 'Unknown error'));
            }
        }
    });
}

function get_payment_details_for_link(payment_link_name) {
    frappe.call({
        method: 'razorpay_frappe.webhook_handler.get_payment_details_for_link',
        args: {
            payment_link_name: payment_link_name
        },
        callback: function(r) {
            if (r.exc) {
                frappe.msgprint(__('Error getting payment details: ') + r.exc);
            } else if (r.message && r.message.success) {
                let message = __('Payment Summary:') + '<br><br>';
                message += __('Total Payments: ') + r.message.summary.total_payments + '<br>';
                message += __('Total Paid: ₹') + r.message.summary.total_paid + '<br>';
                message += __('Remaining: ₹') + r.message.summary.remaining_amount + '<br><br>';
                
                if (r.message.payment_details && r.message.payment_details.length > 0) {
                    message += __('Payment History:') + '<br>';
                    r.message.payment_details.forEach(function(payment, index) {
                        const date = new Date(payment.created_at).toLocaleString();
                        message += (index + 1) + '. ' + date + '<br>';
                        message += '   Payment ID: ' + payment.payment_id + '<br>';
                        message += '   Amount: ₹' + payment.amount + '<br>';
                        message += '   Status: ' + payment.status + '<br>';
                        message += '   Method: ' + payment.method + '<br><br>';
                    });
                } else {
                    message += __('No payment details found.');
                }
                
                frappe.msgprint({
                    title: __('Payment Details'),
                    message: message,
                    indicator: 'green'
                });
            } else {
                frappe.msgprint(__('Error: ') + (r.message ? r.message.error : 'Unknown error'));
            }
        }
    });
} 