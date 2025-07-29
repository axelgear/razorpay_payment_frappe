frappe.ui.form.on('Quotation', {
    refresh: function(frm) {
        if (frm.doc.docstatus === 1) {
            frm.add_custom_button(__('Create Payment Link'), function() {
                create_payment_link(frm);
            }, __('Razorpay'));
            
            if (frm.doc.razorpay_payment_link) {
                frm.add_custom_button(__('Regenerate Payment Link'), function() {
                    regenerate_payment_link(frm);
                }, __('Razorpay'));
                
                frm.add_custom_button(__('View Payment Link'), function() {
                    if (frm.doc.razorpay_payment_link) {
                        window.open(frm.doc.razorpay_payment_link, '_blank');
                    }
                }, __('Razorpay'));
            }
        }
    }
});

function create_payment_link(frm) {
    frappe.call({
        method: 'razorpay_frappe.utils.create_payment_link_for_quotation',
        args: {
            quotation_name: frm.doc.name
        },
        callback: function(r) {
            if (r.exc) {
                frappe.msgprint(__('Error creating payment link: ') + r.exc);
            } else if (r.message) {
                frappe.msgprint(__('Payment link created successfully!'));
                frm.reload_doc();
            }
        }
    });
}

function regenerate_payment_link(frm) {
    frappe.call({
        method: 'razorpay_frappe.utils.update_payment_link_on_revision',
        args: {
            quotation_name: frm.doc.name
        },
        callback: function(r) {
            if (r.exc) {
                frappe.msgprint(__('Error regenerating payment link: ') + r.exc);
            } else if (r.message) {
                frappe.msgprint(__('Payment link regenerated successfully!'));
                frm.reload_doc();
            }
        }
    });
} 