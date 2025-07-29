# Razorpay Integration for ERPNext

A comprehensive ERPNext app that integrates Razorpay's payment gateway and Smart Collect features, including virtual accounts, payment links, QR codes, partial payments, refunds, settlements, and payment verifications.

## 🚀 Features

### Core Payment Features
- **Payment Links**: Create and manage payment links for quotations
- **Virtual Accounts**: Create virtual accounts for customers with bank account, QR code, or TPV support
- **QR Codes**: Generate QR codes for quotations with payment links
- **Partial Payments**: Support for partial payments on payment links
- **Refunds**: Process normal and instant refunds
- **Settlements**: Fetch and manage settlements
- **Payment Verification**: Verify payments using webhook signatures

### Advanced Features
- **Sandbox/Production Mode**: Toggle between testing and live environments
- **Auto-expiring Links**: Payment links expire based on quotation validity
- **Payment Entry Creation**: Automatic creation of payment entries on successful payments
- **Payment Slips**: Generate payment receipts automatically
- **Customer UUID**: Automatic generation of unique customer IDs for Razorpay
- **Quotation Revision**: Automatic payment link updates on quotation revisions
- **Multiple Payment Tracking**: Track multiple payments for single payment links

### Notifications
- **Email Notifications**: Send payment notifications to accounts
- **ZohoCliq Integration**: Send notifications to ZohoCliq channels
- **Webhook Notifications**: Real-time payment status updates

### Dashboard & Analytics
- **Payment Analytics**: View payment statistics and trends
- **Settlement Reports**: Track settlement details
- **Transaction Reports**: Detailed payment transaction reports

## 📦 Installation

### Prerequisites
- ERPNext v14 or later
- Python 3.10 or later
- Razorpay account with API credentials

### Installation Steps

1. **Get the app**:
   ```bash
   bench get-app https://github.com/axelgear/razorpay_integration.git --branch main --skip-assets
   ```

2. **Add to apps.txt**:
   ```bash
   echo "razorpay_integration" >> sites/apps.txt
   ```

3. **Install the app**:
   ```bash
   bench --site [your-site-name] install-app razorpay_integration
   ```

4. **Install dependencies**:
   ```bash
   pip install -r apps/razorpay_integration/requirements.txt
   ```

5. **Run migrations and build**:
   ```bash
   bench migrate
   bench build --app razorpay_integration
   bench restart
   ```

## ⚙️ Configuration

### 1. Razorpay Integration Settings

Navigate to **Razorpay Integration Settings** and configure:

#### API Configuration
- **Enabled**: Enable/disable the integration
- **Sandbox Mode**: Toggle between sandbox and production
- **Sandbox API Key**: Your Razorpay sandbox API key
- **Sandbox API Secret**: Your Razorpay sandbox API secret
- **Production API Key**: Your Razorpay production API key
- **Production API Secret**: Your Razorpay production API secret

#### Webhook Configuration
- **Webhook Secret**: Secret key for webhook verification
- **Default Expiry Days**: Default payment link expiry (default: 7 days)
- **Allow Partial Payments**: Enable partial payments on payment links
- **Virtual Account Prefix**: Prefix for virtual account IDs (default: VA-)

#### Notification Configuration
- **ZohoCliq Notifications**: Enable ZohoCliq notifications
- **ZohoCliq Webhook URL**: Your ZohoCliq webhook URL

### 2. Razorpay Dashboard Configuration

Configure webhooks in your Razorpay Dashboard:

#### Payment Link Webhook
```
URL: https://your-site.com/api/method/razorpay_integration.razorpay_integration.utils.handle_payment_link_callback
Events: payment_link.paid
```

#### Virtual Account Webhook
```
URL: https://your-site.com/api/method/razorpay_integration.razorpay_integration.utils.handle_virtual_account_payment
Events: virtual_account.credited
```

#### Subscription Webhook
```
URL: https://your-site.com/api/method/razorpay_integration.razorpay_integration.utils.handle_subscription_payment_callback
Events: subscription.charged
```

### 3. Custom Fields

The app automatically creates custom fields:

#### Quotation Custom Fields
- `custom_payment_status`: Payment status (Pending/Partially Paid/Paid/Refunded)
- `custom_advance_amount`: Advance amount received
- `custom_sales_order`: Linked sales order
- `custom_qr_code`: QR code attachment

#### Customer Custom Fields
- `custom_razorpay_customer_id`: Unique Razorpay customer ID

## 🎯 Usage

### Creating Payment Links

#### From Quotation
1. Open a quotation
2. Click **"Create Payment Link"** button
3. Configure payment options:
   - Amount (defaults to quotation total)
   - Accept partial payments
   - Expiry date
   - UPI link option
   - Notifications
4. Click **"Create Link"**

#### Advanced Options
- **Description**: Custom payment description
- **Reference ID**: Custom reference for tracking
- **Options**: Additional Razorpay options
- **Generate QR Code**: Create QR code for the payment link

### Virtual Accounts

#### Creating Virtual Accounts
1. Open a customer
2. Click **"Create Virtual Account"** button
3. Configure:
   - Description
   - Expected amount
   - Receiver types (bank_account/qr_code/tpv)
   - Close by date
4. Click **"Create"**

#### Managing Virtual Accounts
- **Add Allowed Payers**: Add specific payers to virtual account
- **Close Account**: Close virtual account when no longer needed
- **Fetch Payments**: Sync payments from Razorpay
- **View Transactions**: See all payments received

### Refunds

#### Processing Refunds
1. Open a payment document
2. Click **"Process Refund"** button
3. Configure:
   - Amount (full or partial)
   - Speed (normal/instant)
   - Receipt number
4. Click **"Process Refund"**

### Settlements

#### Fetching Settlements
1. Navigate to **Razorpay Settlement**
2. Click **"Fetch Settlements"** button
3. Configure date range and count
4. Click **"Fetch"**

#### Settlement Reconciliation
1. Open a settlement document
2. Click **"Reconcile"** button
3. Review and confirm reconciliation

## 🔌 API Endpoints

### Payment Link API
```python
# Create payment link
POST /api/method/razorpay_integration.api.payment.create_payment_link_api
{
    "quotation_name": "QTN-001",
    "amount": 1000,
    "accept_partial": true
}

# Regenerate payment link
POST /api/method/razorpay_integration.api.payment.regenerate_payment_link_api
{
    "quotation_name": "QTN-001"
}
```

### Virtual Account API
```python
# Create virtual account
POST /api/method/razorpay_integration.api.payment.create_virtual_account_api
{
    "customer_name": "Customer Name",
    "description": "Virtual Account Description",
    "amount": 1000
}
```

### Refund API
```python
# Process refund
POST /api/method/razorpay_integration.api.payment.process_refund_api
{
    "payment_name": "Payment Name",
    "amount": 500,
    "speed": "normal"
}
```

## 🧪 Testing

### Running Tests
```bash
bench --site [site-name] run-tests --module razorpay_integration
```

### Test Coverage
- Payment link creation and management
- Virtual account operations
- Refund processing
- Webhook handling
- Settings validation
- API endpoint testing

## 🔧 Troubleshooting

### Common Issues

#### 1. API Key Errors
- Ensure correct API keys are configured
- Check sandbox/production mode setting
- Verify API key permissions in Razorpay dashboard

#### 2. Webhook Failures
- Verify webhook URLs are correct
- Check webhook secret configuration
- Ensure webhook events are enabled in Razorpay dashboard

#### 3. Payment Link Issues
- Check quotation validity dates
- Verify payment link expiry settings
- Ensure customer has valid email/mobile

#### 4. Virtual Account Issues
- Verify customer has Razorpay customer ID
- Check virtual account prefix configuration
- Ensure receiver types are supported

### Debugging

#### Enable Debug Logging
```python
# In hooks.py
frappe.logger().setLevel(logging.DEBUG)
```

#### Check Error Logs
```bash
bench --site [site-name] tail-logs
```

## 🔒 Security

### Webhook Security
- All webhooks are verified using HMAC signatures
- Webhook secret is required for verification
- Invalid signatures are rejected

### API Security
- All API endpoints require authentication
- Input validation on all parameters
- Error messages don't expose sensitive information

### Data Protection
- Sensitive data is encrypted
- API secrets are stored securely
- Payment data is handled according to PCI standards

## 📚 Documentation

### API Documentation
- [Razorpay API Docs](https://razorpay.com/docs/)
- [Webhook Documentation](https://razorpay.com/docs/webhooks/)
- [Testing Guide](https://razorpay.com/docs/testing/)

### App Documentation
- [Installation Guide](docs/README.md)
- [Configuration Guide](docs/README.md#configuration)
- [API Reference](docs/README.md#api-endpoints)

## 🤝 Support

### Community Support
- [GitHub Issues](https://github.com/axelgear/razorpay_integration/issues)
- [ERPNext Forum](https://discuss.erpnext.com/)

### Commercial Support
- Contact: rejithr1995@gmail.com
- License: MIT

## 📋 Changelog

### v0.0.1
- Initial release
- Basic payment link functionality
- Virtual account support
- QR code generation
- Refund processing
- Settlement management
- Webhook handling
- ZohoCliq notifications
- Comprehensive testing
- Security improvements
- API endpoints
- Setup wizard
- Documentation

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Razorpay team for their excellent API
- ERPNext community for the framework
- Contributors and testers

---

**Note**: This app is designed to work with ERPNext v14+ and requires proper Razorpay account setup. Please ensure you have valid API credentials before installation.




