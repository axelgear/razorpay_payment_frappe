frappe.ui.form.on('Quotation', {
    refresh: function(frm) {
        if (!frm.is_new() && frm.doc.docstatus === 1) {
            frm.add_custom_button(__('Regenerate Razorpay Payment Link'), function() {
                frappe.call({
                    method: 'razorpay_frappe.razorpay_integration.payment_link_common.regenerate_razorpay_link',
                    args: { doctype: frm.doc.doctype, docname: frm.doc.name },
                    freeze: true,
                    callback: function(r) {
                        if (r.message) {
                            frm.set_value('razorpay_link', r.message.razorpay_link);
                            frm.set_value('razorpay_expiry', r.message.razorpay_expiry);
                            frm.set_value('razorpay_payment_status', r.message.razorpay_payment_status);
                            frm.reload_doc();
                            frappe.show_alert(__('Razorpay payment link regenerated!'));
                        } else {
                            frappe.msgprint(__('Failed to regenerate payment link.'));
                        }
                    }
                });
            });
        }
    }
}); 