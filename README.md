# 🚀 Razorpay Frappe Integration

A comprehensive Razorpay payment integration for Frappe/ERPNext, providing seamless payment link generation, QR code support, payment tracking, and ZohoCliq notifications.

## ✨ Features

### 💳 Payment Links Management
- **Automatic Payment Link Generation**: Create payment links directly from Quotations
- **QR Code Generation**: Automatic QR code generation and attachment to payment links
- **Partial Payment Support**: Allow customers to make partial payments
- **Payment Status Tracking**: Real-time payment status updates via webhooks
- **Payment Details**: Comprehensive payment history and reconciliation

### 🔗 Webhook Integration
- **Real-time Updates**: Automatic payment status synchronization
- **Secure Verification**: Webhook signature verification for security
- **Payment Reconciliation**: Detailed payment tracking and settlement management

### 📱 ZohoCliq Notifications
- **Quote Notifications**: Instant notifications for new and updated quotes
- **Payment Alerts**: Real-time payment status updates
- **Project Integration**: Task and project notifications
- **Customizable Templates**: Rich message templates with buttons and cards

### 🏢 Settlement Management
- **Settlement Tracking**: Monitor settlement status and reconciliation
- **Payment Entry Integration**: Automatic payment entry creation
- **Reconciliation Tools**: Comprehensive settlement reconciliation features

## 🛠️ Installation

### Prerequisites
- Frappe Framework 14+
- ERPNext 14+
- Python 3.8+
- Razorpay Account

### Installation Steps

1. **Install the App**
   ```bash
   bench get-app razorpay_frappe
   bench install-app razorpay_frappe
   ```

2. **Configure Razorpay Settings**
   - Navigate to **Razorpay Settings** in the desk
   - Configure your Razorpay API keys (Sandbox/Production)
   - Set up webhook secret for security
   - Configure payment preferences

3. **Set up Webhooks**
   - Add webhook URL in your Razorpay dashboard:
   ```
   https://your-domain.com/api/method/razorpay_frappe.webhook_handler.razorpay_webhook
   ```

## ⚙️ Configuration

### Razorpay Settings

#### 🔧 Environment Configuration
- **Sandbox Mode**: Toggle between testing and production environment
- **API Keys**: Configure sandbox and production API keys
- **Key Validation**: Automatic validation of API credentials

#### 💳 Payment Configuration
- **Partial Payments**: Enable/disable partial payment support
- **Expiry Days**: Set default expiry for payment links (1-365 days)
- **Guest Checkout**: Allow payments without account creation

#### 🔗 Webhook Configuration
- **Webhook Secret**: Secure webhook verification
- **Event Handling**: Automatic payment status updates

### ZohoCliq Integration

1. **Channel Configuration**
   - Set up ZohoCliq channels for different notification types
   - Configure webhook URLs for each channel

2. **Notification Types**
   - **Quote Notifications**: New and updated quote alerts
   - **Payment Notifications**: Payment status updates
   - **Project Notifications**: Task and project updates

## 📋 Usage

### Creating Payment Links

#### From Quotation
1. Create or open a Quotation
2. Submit the quotation
3. Payment link is automatically generated
4. QR code is attached to the payment link

#### Manual Creation
1. Navigate to **Razorpay Payment Link**
2. Click **New**
3. Fill in payment details
4. Save to generate payment link

### Payment Tracking

#### View Payment Details
1. Open **Razorpay Payment Link** document
2. Use **View Payments** button to see payment history
3. Check individual payment details and status

#### Sync Payment Status
1. Use **Sync Status** button for manual synchronization
2. Automatic sync via webhooks
3. Real-time status updates

### Settlement Management

#### View Settlements
1. Navigate to **Razorpay Settlement**
2. View settlement status and details
3. Track reconciliation status

#### Reconciliation
1. Use settlement reconciliation tools
2. Match payments with settlement entries
3. Generate reconciliation reports

## 🔧 API Reference

### Payment Link Creation
```python
from razorpay_frappe.utils import create_payment_link_for_quotation

# Create payment link for quotation
payment_link = create_payment_link_for_quotation("SAL-QTN-2025-00012")
```

### Payment Status Sync
```python
from razorpay_frappe.webhook_handler import sync_payment_link_status

# Sync payment link status
status = sync_payment_link_status("plink_xyz123")
```

### ZohoCliq Notifications
```python
from razorpay_frappe.utils import post_to_zohocliq

# Send notification
post_to_zohocliq("Payment received!", "Project")
```

## 📊 Dashboard

### Razorpay Workspace
- **Payment Links Management**: View and manage all payment links
- **Payment Details**: Track individual payment records
- **Settlements**: Monitor settlement status
- **Analytics**: Payment trends and statistics

### Number Cards
- **Active Payment Links**: Count of active payment links
- **Pending Settlements**: Count of pending settlements
- **Captured Payments**: Count of successful payments
- **Reconciled Payments**: Count of reconciled payments

## 🔒 Security Features

- **Webhook Signature Verification**: Secure webhook processing
- **API Key Encryption**: Secure storage of API credentials
- **Permission-based Access**: Role-based access control
- **Audit Trail**: Complete audit logging

## 🐛 Troubleshooting

### Common Issues

#### Payment Link Not Generated
- Check Razorpay Settings configuration
- Verify API keys are correct
- Ensure webhook is properly configured

#### Webhook Not Working
- Verify webhook URL is correct
- Check webhook secret configuration
- Ensure server is accessible from Razorpay

#### QR Code Not Attached
- Check file permissions
- Verify QR code generation is enabled
- Check error logs for details

### Debug Tools

#### Payment Link Debug
```python
from razorpay_frappe.utils import debug_payment_link_status

# Debug payment link status
debug_payment_link_status("plink_xyz123")
```

#### Settings Check
```python
from razorpay_frappe.utils import check_razorpay_settings_fields

# Check settings configuration
check_razorpay_settings_fields()
```

## 📝 Changelog

### Version 1.0.0
- Initial release
- Payment link generation from quotations
- QR code generation and attachment
- Webhook integration
- ZohoCliq notifications
- Settlement management
- Payment tracking and reconciliation

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [Link to documentation]
- **Issues**: [GitHub Issues](https://github.com/your-repo/razorpay_frappe/issues)
- **Email**: rejithr1995@gmail.com

## 🙏 Acknowledgments

- **Frappe Framework**: For the amazing framework
- **ERPNext**: For the comprehensive ERP solution
- **Razorpay**: For the excellent payment gateway API
- **ZohoCliq**: For the notification platform

---

**Made with ❤️ by AxelGear**

