import frappe

def execute():
    """Add ZohoCliq thread ID field to Project DocType"""
    
    # Check if field already exists
    if frappe.db.exists("Custom Field", {"dt": "Project", "fieldname": "zohocliq_thread_id"}):
        return
    
    # Create custom field
    custom_field = frappe.get_doc({
        "doctype": "Custom Field",
        "dt": "Project",
        "fieldname": "zohocliq_thread_id",
        "label": "ZohoCliq Thread ID",
        "fieldtype": "Data",
        "read_only": 1,
        "hidden": 0,  # Make it visible for debugging
        "description": "Thread ID for ZohoCliq project discussions"
    })
    
    custom_field.insert(ignore_permissions=True)
    frappe.db.commit()
    
    print("Added zohocliq_thread_id field to Project DocType") 