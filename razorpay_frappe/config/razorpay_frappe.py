app_name = "razorpay_frappe"
app_title = "Razorpay Frappe"
app_publisher = "Your Name"
app_description = "Razorpay integration for ERPNext"
app_icon = "octicon octicon-credit-card"
app_color = "blue"
app_email = "you@example.com"
app_license = "MIT"

# Add custom reports
app_reports = [
    {
        "module": "Razorpay Frappe",
        "name": "Payment Link Status Report",
        "doctype": "Quotation",
        "is_query_report": False,
        "ref_doctype": "Quotation",
        "report_type": "Script Report",
        "report_file": "razorpay_frappe/razorpay_integration/report/payment_link_status_report.py"
    }
] 