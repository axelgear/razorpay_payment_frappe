frappe.ui.form.on('Razorpay Settlement', {
    refresh: function(frm) {
        if (frm.doc.settlement_id) {
            frm.add_custom_button(__('Load Details'), function() {
                load_settlement_details(frm);
            }, __('Razorpay'));
            
            frm.add_custom_button(__('Reconcile'), function() {
                reconcile_settlement(frm);
            }, __('Razorpay'));
            
            frm.add_custom_button(__('Fetch Payment Entries'), function() {
                fetch_payment_entries(frm);
            }, __('Razorpay'));
        }
        
        frm.add_custom_button(__('Fetch Automatic Settlements'), function() {
            fetch_automatic_settlements();
        }, __('Razorpay'));
        
        frm.add_custom_button(__('Fetch On-Demand Settlements'), function() {
            fetch_ondemand_settlements();
        }, __('Razorpay'));
        
        frm.add_custom_button(__('Create On-Demand Settlement'), function() {
            create_ondemand_settlement();
        }, __('Razorpay'));
        
        frm.add_custom_button(__('Settlement Cycle Info'), function() {
            get_settlement_cycle_info();
        }, __('Razorpay'));
    }
});

function load_settlement_details(frm) {
    frappe.call({
        method: 'razorpay_frappe.utils.fetch_settlement',
        args: {
            settlement_id: frm.doc.settlement_id
        },
        callback: function(r) {
            if (r.exc) {
                frappe.msgprint(__('Error loading settlement details: ') + r.exc);
            } else if (r.message && r.message.success) {
                frappe.msgprint(__('Settlement details loaded successfully!'));
                frm.reload_doc();
            } else {
                frappe.msgprint(__('Error: ') + (r.message ? r.message.error : 'Unknown error'));
            }
        }
    });
}

function reconcile_settlement(frm) {
    frappe.call({
        method: 'razorpay_frappe.utils.settlement_recon',
        args: {
            settlement_id: frm.doc.settlement_id
        },
        callback: function(r) {
            if (r.exc) {
                frappe.msgprint(__('Error reconciling settlement: ') + r.exc);
            } else if (r.message && r.message.success) {
                frappe.msgprint(__('Settlement reconciled successfully!'));
                frm.reload_doc();
            } else {
                frappe.msgprint(__('Error: ') + (r.message ? r.message.error : 'Unknown error'));
            }
        }
    });
}

function fetch_payment_entries(frm) {
    frappe.call({
        method: 'razorpay_frappe.razorpay_integration.doctype.razorpay_settlement.razorpay_settlement.RazorpaySettlement.fetch_payment_entries',
        args: {
            settlement_name: frm.doc.name
        },
        callback: function(r) {
            if (r.exc) {
                frappe.msgprint(__('Error fetching payment entries: ') + r.exc);
            } else {
                frappe.msgprint(__('Payment entries fetched successfully!'));
                frm.reload_doc();
            }
        }
    });
}

function fetch_automatic_settlements() {
    let d = new frappe.ui.Dialog({
        title: __('Fetch Automatic Settlements'),
        fields: [
            {
                fieldtype: 'Date',
                fieldname: 'from_date',
                label: __('From Date')
            },
            {
                fieldtype: 'Date',
                fieldname: 'to_date',
                label: __('To Date')
            },
            {
                fieldtype: 'Int',
                fieldname: 'count',
                label: __('Count'),
                default: 10
            }
        ],
        primary_action_label: __('Fetch'),
        primary_action: function(values) {
            frappe.call({
                method: 'razorpay_frappe.utils.fetch_automatic_settlements',
                args: {
                    from_date: values.from_date,
                    to_date: values.to_date,
                    count: values.count
                },
                callback: function(r) {
                    if (r.exc) {
                        frappe.msgprint(__('Error fetching automatic settlements: ') + r.exc);
                    } else if (r.message && r.message.success) {
                        frappe.msgprint(__('Automatic settlements fetched successfully!'));
                        d.hide();
                        // Refresh the list view
                        frappe.set_route('List', 'Razorpay Settlement');
                    } else {
                        frappe.msgprint(__('Error: ') + (r.message ? r.message.error : 'Unknown error'));
                    }
                }
            });
        }
    });
    d.show();
}

function fetch_ondemand_settlements() {
    let d = new frappe.ui.Dialog({
        title: __('Fetch On-Demand Settlements'),
        fields: [
            {
                fieldtype: 'Date',
                fieldname: 'from_date',
                label: __('From Date')
            },
            {
                fieldtype: 'Date',
                fieldname: 'to_date',
                label: __('To Date')
            },
            {
                fieldtype: 'Int',
                fieldname: 'count',
                label: __('Count'),
                default: 10
            }
        ],
        primary_action_label: __('Fetch'),
        primary_action: function(values) {
            frappe.call({
                method: 'razorpay_frappe.utils.fetch_all_ondemand_settlements',
                args: {
                    from_date: values.from_date,
                    to_date: values.to_date,
                    count: values.count
                },
                callback: function(r) {
                    if (r.exc) {
                        frappe.msgprint(__('Error fetching on-demand settlements: ') + r.exc);
                    } else if (r.message && r.message.success) {
                        frappe.msgprint(__('On-demand settlements fetched successfully!'));
                        d.hide();
                        // Refresh the list view
                        frappe.set_route('List', 'Razorpay Settlement');
                    } else {
                        frappe.msgprint(__('Error: ') + (r.message ? r.message.error : 'Unknown error'));
                    }
                }
            });
        }
    });
    d.show();
}

function get_settlement_cycle_info() {
    frappe.call({
        method: 'razorpay_frappe.utils.get_settlement_cycle_info',
        callback: function(r) {
            if (r.exc) {
                frappe.msgprint(__('Error fetching settlement cycle info: ') + r.exc);
            } else if (r.message && r.message.success) {
                let account = r.message.account;
                let msg = __('Settlement Cycle Information:') + '<br><br>';
                msg += __('Account Name: ') + account.name + '<br>';
                msg += __('Email: ') + account.email + '<br>';
                msg += __('Contact: ') + account.contact + '<br>';
                msg += __('Type: ') + account.type + '<br>';
                
                if (account.bank_accounts && account.bank_accounts.length > 0) {
                    msg += '<br>' + __('Bank Accounts:') + '<br>';
                    account.bank_accounts.forEach(function(bank, index) {
                        msg += (index + 1) + '. ' + bank.name + ' - ' + bank.ifsc + '<br>';
                    });
                }
                
                frappe.msgprint({
                    title: __('Settlement Cycle Info'),
                    message: msg,
                    indicator: 'green'
                });
            } else {
                frappe.msgprint(__('Error: ') + (r.message ? r.message.error : 'Unknown error'));
            }
        }
    });
}

function create_ondemand_settlement() {
    let d = new frappe.ui.Dialog({
        title: __('Create On-Demand Settlement'),
        fields: [
            {
                fieldtype: 'Currency',
                fieldname: 'amount',
                label: __('Amount'),
                reqd: 1
            },
            {
                fieldtype: 'Link',
                fieldname: 'currency',
                label: __('Currency'),
                options: 'Currency',
                default: 'INR',
                reqd: 1
            },
            {
                fieldtype: 'Text',
                fieldname: 'description',
                label: __('Description')
            }
        ],
        primary_action_label: __('Create'),
        primary_action: function(values) {
            frappe.call({
                method: 'razorpay_frappe.utils.create_ondemand_settlement',
                args: {
                    amount: values.amount,
                    currency: values.currency,
                    description: values.description
                },
                callback: function(r) {
                    if (r.exc) {
                        frappe.msgprint(__('Error creating settlement: ') + r.exc);
                    } else if (r.message && r.message.success) {
                        frappe.msgprint(__('On-demand settlement created successfully!'));
                        d.hide();
                        // Refresh the list view
                        frappe.set_route('List', 'Razorpay Settlement');
                    } else {
                        frappe.msgprint(__('Error: ') + (r.message ? r.message.error : 'Unknown error'));
                    }
                }
            });
        }
    });
    d.show();
} 