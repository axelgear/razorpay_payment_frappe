import express from "express";
import fetch from "node-fetch";
import cors from "cors";

const app = express();

// ✅ CORS middleware must be placed before other routes
app.use((req, res, next) => {
  // Manually set CORS headers to be 100% sure even if the cors package fails
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "GET,POST,OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type, Authorization");
  // Quickly terminate OPTIONS pre-flight with 200 OK
  if (req.method === "OPTIONS") {
    return res.sendStatus(200);
  }
  next();
});

app.use(express.json());
app.use(express.static('.'));

app.get('/', (req, res) => {
  res.sendFile('zoho.html', { root: '.' });
});

const WEBHOOK_TOKEN = "1001.4b991a8eb8fe433eafff7f60e8d9aa6a.cd31f8ce031327c4cbfa5848369ddea2";
const CHANNEL_UNIQUE_NAME = "projectteamerp";
const BOT_UNIQUE_NAME = "elina";
const COMPANY_ID = "673651768";

// Correct API URLs with webhook token authentication
const CHANNEL_API = `https://cliq.zoho.com/api/v2/channelsbyname/${CHANNEL_UNIQUE_NAME}/message?bot_unique_name=${BOT_UNIQUE_NAME}&zapikey=${WEBHOOK_TOKEN}`;

app.post("/send-message", async (req, res) => {
  try {
    console.log("Sending message to Zoho Cliq...");
    console.log("Channel API:", CHANNEL_API);
    
    const response = await fetch(CHANNEL_API, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ text: req.body.text || "Default message" })
    });

    console.log("Response status:", response.status);
    console.log("Response headers:", Object.fromEntries(response.headers.entries()));
    
    const responseText = await response.text();
    console.log("Response text:", responseText);
    
    let data;
    try {
      data = JSON.parse(responseText);
    } catch (e) {
      data = { rawResponse: responseText };
    }
    
    res.json({
      status: response.status,
      statusText: response.statusText,
      data: data,
      headers: Object.fromEntries(response.headers.entries())
    });
  } catch (error) {
    console.error("Error:", error);
    res.status(500).json({ error: error.message });
  }
});

// Test endpoint to verify webhook token
app.get("/test-token", async (req, res) => {
  try {
    console.log("Testing webhook token...");
    // Use a valid webhook endpoint for testing
    const testUrl = `https://cliq.zoho.com/api/v2/channelsbyname/${CHANNEL_UNIQUE_NAME}/message?zapikey=${WEBHOOK_TOKEN}`;
    
    const response = await fetch(testUrl, {
      method: "GET",
      headers: {
        "Content-Type": "application/json"
      }
    });
    
    console.log("Test response status:", response.status);
    const responseText = await response.text();
    console.log("Test response text:", responseText);
    
    let data;
    try {
      data = JSON.parse(responseText);
    } catch (e) {
      data = { rawResponse: responseText };
    }
    
    res.json({
      status: response.status,
      statusText: response.statusText,
      data: data
    });
  } catch (error) {
    console.error("Test error:", error);
    res.status(500).json({ error: error.message });
  }
});

// Test incoming webhook endpoint (no token needed)
app.post("/test-webhook", async (req, res) => {
  try {
    console.log("Testing webhook...");
    const webhookUrl = "https://cliq.zoho.com/company/673651768/api/v2/bots/elina/incoming";
    
    const response = await fetch(webhookUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ 
        text: req.body.text || "Test message from webhook"
      })
    });
    
    console.log("Webhook response status:", response.status);
    console.log("Webhook response headers:", Object.fromEntries(response.headers.entries()));
    
    // Try to get response as text first
    const responseText = await response.text();
    console.log("Webhook response text:", responseText);
    
    let data;
    try {
      data = JSON.parse(responseText);
    } catch (e) {
      data = { rawResponse: responseText };
    }
    
    res.json({
      status: response.status,
      statusText: response.statusText,
      data: data,
      headers: Object.fromEntries(response.headers.entries())
    });
  } catch (error) {
    console.error("Webhook error:", error);
    res.status(500).json({ error: error.message });
  }
});

// Simple test with different auth methods
app.post("/test-simple", async (req, res) => {
  try {
    console.log("Testing simple message...");
    
    // Try the channel API with a simpler payload
    const response = await fetch(CHANNEL_API_SIMPLE, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ 
        text: req.body.text || "Simple test message"
      })
    });
    
    console.log("Simple test status:", response.status);
    const responseText = await response.text();
    console.log("Simple test response:", responseText);
    
    let data;
    try {
      data = JSON.parse(responseText);
    } catch (e) {
      data = { rawResponse: responseText };
    }
    
    res.json({
      status: response.status,
      statusText: response.statusText,
      data: data
    });
  } catch (error) {
    console.error("Simple test error:", error);
    res.status(500).json({ error: error.message });
  }
});

// Test endpoint to show webhook URL
app.get("/webhook-url", (req, res) => {
  const webhookUrl = `https://cliq.zoho.com/api/v2/channelsbyname/${CHANNEL_UNIQUE_NAME}/message?zapikey=${WEBHOOK_TOKEN}`;
  res.json({
    webhookUrl: webhookUrl,
    channelName: CHANNEL_UNIQUE_NAME,
    token: WEBHOOK_TOKEN,
    instructions: "Use POST method with JSON body: {\"text\": \"your message\"}"
  });
});

// Test endpoint to send a test message
app.post("/send-test", async (req, res) => {
  try {
    console.log("Sending test message...");
    const testMessage = "🧪 Test message from server at " + new Date().toLocaleString();
    
    const response = await fetch(CHANNEL_API, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ text: testMessage })
    });
    
    console.log("Test message status:", response.status);
    console.log("Test message sent successfully!");
    
    res.json({
      success: true,
      status: response.status,
      message: "Test message sent to channel",
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error("Test message error:", error);
    res.status(500).json({ error: error.message });
  }
});

// Send rich text message with formatting
app.post("/send-rich-text", async (req, res) => {
  try {
    console.log("Sending rich text message...");
    
    const richTextMessage = {
      text: "**Bold Text**\n*Italic Text*\n`Code Text`\n[Link Text](https://example.com)\n> Quote Text\n- Bullet Point 1\n- Bullet Point 2\n\n**Summary:** This is a rich text message with formatting!"
    };
    
    const response = await fetch(CHANNEL_API, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(richTextMessage)
    });
    
    console.log("Rich text status:", response.status);
    
    res.json({
      success: true,
      status: response.status,
      message: "Rich text message sent",
      sample: richTextMessage
    });
  } catch (error) {
    console.error("Rich text error:", error);
    res.status(500).json({ error: error.message });
  }
});

// Send proper message card with buttons
app.post("/send-card", async (req, res) => {
  try {
    console.log("Sending message card...");
    
    // Proper message card format based on Zoho documentation
    const messageCard = {
      text: "📋 **Task Update** - Project Status Update",
      card: {
        title: "Project Status Update",
        theme: "modern-inline",
        thumbnail: "https://via.placeholder.com/150x100/007bff/ffffff?text=Project"
      },
      buttons: [
        {
          label: "View Details",
          type: "+",
          action: {
            type: "open.url",
            data: {
              web: "https://subtle-exactly-glider.ngrok-free.app/app/project/PROJ-0003"
            }
          }
        },
        {
          label: "Mark Complete",
          type: "+",
          action: {
            type: "invoke.function",
            data: {
              name: "mark_task_complete"
            }
          }
        }
      ]
    };
    
    const response = await fetch(CHANNEL_API, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(messageCard)
    });
    
    console.log("Card status:", response.status);
    const responseText = await response.text();
    console.log("Card response:", responseText);
    
    let data;
    try {
      data = JSON.parse(responseText);
    } catch (e) {
      data = { rawResponse: responseText };
    }
    
    res.json({
      success: true,
      status: response.status,
      message: "Message card sent",
      data: data
    });
  } catch (error) {
    console.error("Card error:", error);
    res.status(500).json({ error: error.message });
  }
});

// Send poll message card
app.post("/send-poll", async (req, res) => {
  try {
    console.log("Sending poll message...");
    
    const pollMessage = {
      text: "Would you be able to attend the team meeting tomorrow?",
      card: {
        title: "TEAM MEETING POLL",
        theme: "poll",
        thumbnail: "https://via.placeholder.com/150x100/28a745/ffffff?text=Poll"
      },
      buttons: [
        {
          label: "Yes",
          type: "+",
          action: {
            type: "invoke.function",
            data: {
              name: "poll_response"
            }
          }
        },
        {
          label: "No",
          type: "-",
          action: {
            type: "invoke.function",
            data: {
              name: "poll_response"
            }
          }
        },
        {
          label: "Maybe",
          type: "+",
          action: {
            type: "invoke.function",
            data: {
              name: "poll_response"
            }
          }
        }
      ]
    };
    
    const response = await fetch(CHANNEL_API, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(pollMessage)
    });
    
    console.log("Poll status:", response.status);
    const responseText = await response.text();
    console.log("Poll response:", responseText);
    
    let data;
    try {
      data = JSON.parse(responseText);
    } catch (e) {
      data = { rawResponse: responseText };
    }
    
    res.json({
      success: true,
      status: response.status,
      message: "Poll message sent",
      data: data
    });
  } catch (error) {
    console.error("Poll error:", error);
    res.status(500).json({ error: error.message });
  }
});

// Send message with emojis and formatting
app.post("/send-formatted", async (req, res) => {
  try {
    console.log("Sending formatted message...");
    
    const formattedMessage = {
      text: `🚀 **System Alert** 🚀

⚠️ *High Priority Notification*

**Details:**
• 🔴 Server Status: Critical
• 🟡 Response Time: 2.5s
• 🟢 Database: Healthy

**Actions Required:**
1. Check server logs
2. Monitor performance
3. Update status page

📞 Contact: @admin
🔗 [View Dashboard](https://dashboard.example.com)

---
*Sent via Bot API at ${new Date().toLocaleString()}*`
    };
    
    const response = await fetch(CHANNEL_API, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(formattedMessage)
    });
    
    console.log("Formatted status:", response.status);
    
    res.json({
      success: true,
      status: response.status,
      message: "Formatted message sent",
      sample: formattedMessage
    });
  } catch (error) {
    console.error("Formatted error:", error);
    res.status(500).json({ error: error.message });
  }
});

// Send simple card (alternative format)
app.post("/send-simple-card", async (req, res) => {
  try {
    console.log("Sending simple card...");
    
    // Fixed simple card format - removed 'description' key
    const simpleCard = {
      text: "📋 **Simple Card Test**",
      card: {
        title: "Simple Card"
      }
    };
    
    const response = await fetch(CHANNEL_API, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(simpleCard)
    });
    
    console.log("Simple card status:", response.status);
    const responseText = await response.text();
    console.log("Simple card response:", responseText);
    
    let data;
    try {
      data = JSON.parse(responseText);
    } catch (e) {
      data = { rawResponse: responseText };
    }
    
    res.json({
      success: true,
      status: response.status,
      message: "Simple card sent",
      data: data
    });
  } catch (error) {
    console.error("Simple card error:", error);
    res.status(500).json({ error: error.message });
  }
});

// Send payment update card
app.post("/send-payment-update", async (req, res) => {
  try {
    console.log("Sending payment update...");
    
    const paymentUpdate = {
      text: "💰 **Payment Update** - Invoice #INV-2024-001",
      card: {
        title: "PAYMENT STATUS UPDATE",
        theme: "modern-inline",
        thumbnail: "https://via.placeholder.com/150x100/28a745/ffffff?text=Payment"
      },
      slides: [
        {
          type: "table",
          title: "Payment Details",
          data: {
            headers: ["Field", "Value"],
            rows: [
              { "Field": "Invoice Number", "Value": "INV-2024-001" },
              { "Field": "Customer", "Value": "ABC Corporation" },
              { "Field": "Amount", "Value": "$2,500.00" },
              { "Field": "Due Date", "Value": "2024-01-15" },
              { "Field": "Status", "Value": "Overdue" }
            ]
          }
        }
      ],
      buttons: [
        {
          label: "View Invoice",
          type: "+",
          action: {
            type: "open.url",
            data: {
              web: "https://subtle-exactly-glider.ngrok-free.app/app/invoice/INV-2024-001"
            }
          }
        },
        {
          label: "Send Reminder",
          type: "+",
          action: {
            type: "invoke.function",
            data: {
              name: "send_payment_reminder"
            }
          }
        },
        {
          label: "Mark Paid",
          type: "+",
          action: {
            type: "invoke.function",
            data: {
              name: "mark_invoice_paid"
            }
          }
        }
      ]
    };
    
    const response = await fetch(CHANNEL_API, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(paymentUpdate)
    });
    
    console.log("Payment update status:", response.status);
    const responseText = await response.text();
    console.log("Payment update response:", responseText);
    
    let data;
    try {
      data = JSON.parse(responseText);
    } catch (e) {
      data = { rawResponse: responseText };
    }
    
    res.json({
      success: true,
      status: response.status,
      message: "Payment update sent",
      data: data
    });
  } catch (error) {
    console.error("Payment update error:", error);
    res.status(500).json({ error: error.message });
  }
});

// Send task update card
app.post("/send-task-update", async (req, res) => {
  try {
    console.log("Sending task update...");
    
    const taskUpdate = {
      text: "📋 **Task Update** - Project: Website Redesign",
      card: {
        title: "TASK STATUS UPDATE",
        theme: "modern-inline",
        thumbnail: "https://via.placeholder.com/150x100/007bff/ffffff?text=Task"
      },
      slides: [
        {
          type: "table",
          title: "Task Details",
          data: {
            headers: ["Field", "Value"],
            rows: [
              { "Field": "Task", "Value": "Homepage Design" },
              { "Field": "Assigned To", "Value": "John Smith" },
              { "Field": "Priority", "Value": "High" },
              { "Field": "Due Date", "Value": "2024-01-20" },
              { "Field": "Progress", "Value": "75%" },
              { "Field": "Status", "Value": "In Progress" }
            ]
          }
        }
      ],
      buttons: [
        {
          label: "View Task",
          type: "+",
          action: {
            type: "open.url",
            data: {
              web: "https://subtle-exactly-glider.ngrok-free.app/app/task/TASK-001"
            }
          }
        },
        {
          label: "Update Progress",
          type: "+",
          action: {
            type: "invoke.function",
            data: {
              name: "update_task_progress"
            }
          }
        },
        {
          label: "Mark Complete",
          type: "+",
          action: {
            type: "invoke.function",
            data: {
              name: "mark_task_complete"
            }
          }
        }
      ]
    };
    
    const response = await fetch(CHANNEL_API, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(taskUpdate)
    });
    
    console.log("Task update status:", response.status);
    const responseText = await response.text();
    console.log("Task update response:", responseText);
    
    let data;
    try {
      data = JSON.parse(responseText);
    } catch (e) {
      data = { rawResponse: responseText };
    }
    
    res.json({
      success: true,
      status: response.status,
      message: "Task update sent",
      data: data
    });
  } catch (error) {
    console.error("Task update error:", error);
    res.status(500).json({ error: error.message });
  }
});

// Send payment received notification
app.post("/send-payment-received", async (req, res) => {
  try {
    console.log("Sending payment received notification...");
    
    const paymentReceived = {
      text: "✅ **Payment Received** - Thank you!",
      card: {
        title: "PAYMENT CONFIRMATION",
        theme: "prompt",
        thumbnail: "https://via.placeholder.com/150x100/28a745/ffffff?text=Success"
      },
      slides: [
        {
          type: "table",
          title: "Payment Details",
          data: {
            headers: ["Field", "Value"],
            rows: [
              { "Field": "Invoice Number", "Value": "INV-2024-001" },
              { "Field": "Customer", "Value": "ABC Corporation" },
              { "Field": "Amount Paid", "Value": "$2,500.00" },
              { "Field": "Payment Method", "Value": "Bank Transfer" },
              { "Field": "Transaction ID", "Value": "TXN-123456789" },
              { "Field": "Date Received", "Value": "2024-01-10 14:30" }
            ]
          }
        }
      ],
      buttons: [
        {
          label: "View Receipt",
          type: "+",
          action: {
            type: "open.url",
            data: {
              web: "https://subtle-exactly-glider.ngrok-free.app/app/receipt/REC-001"
            }
          }
        },
        {
          label: "Send Thank You",
          type: "+",
          action: {
            type: "invoke.function",
            data: {
              name: "send_thank_you_email"
            }
          }
        }
      ]
    };
    
    const response = await fetch(CHANNEL_API, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(paymentReceived)
    });
    
    console.log("Payment received status:", response.status);
    const responseText = await response.text();
    console.log("Payment received response:", responseText);
    
    let data;
    try {
      data = JSON.parse(responseText);
    } catch (e) {
      data = { rawResponse: responseText };
    }
    
    res.json({
      success: true,
      status: response.status,
      message: "Payment received notification sent",
      data: data
    });
  } catch (error) {
    console.error("Payment received error:", error);
    res.status(500).json({ error: error.message });
  }
});

// Send quote items list
app.post("/send-quote-items", async (req, res) => {
  try {
    console.log("Sending quote items...");
    
    const quoteItems = {
      text: "📄 **Quote Items** - Quote #QT-2024-001",
      card: {
        title: "QUOTE DETAILS",
        theme: "modern-inline",
        thumbnail: "https://via.placeholder.com/150x100/ffc107/ffffff?text=Quote"
      },
      slides: [
        {
          type: "table",
          title: "Quote Items",
          data: {
            headers: ["Item", "Description", "Qty", "Rate", "Amount"],
            rows: [
              { "Item": "Web Design", "Description": "Homepage Redesign", "Qty": "1", "Rate": "$1,500.00", "Amount": "$1,500.00" },
              { "Item": "Logo Design", "Description": "Company Logo", "Qty": "1", "Rate": "$500.00", "Amount": "$500.00" },
              { "Item": "SEO Setup", "Description": "Search Engine Optimization", "Qty": "1", "Rate": "$800.00", "Amount": "$800.00" },
              { "Item": "Hosting", "Description": "Annual Hosting", "Qty": "1", "Rate": "$200.00", "Amount": "$200.00" }
            ]
          }
        },
        {
          type: "table",
          title: "Summary",
          data: {
            headers: ["Field", "Value"],
            rows: [
              { "Field": "Subtotal", "Value": "$3,000.00" },
              { "Field": "Tax (10%)", "Value": "$300.00" },
              { "Field": "Total", "Value": "$3,300.00" },
              { "Field": "Valid Until", "Value": "2024-02-10" }
            ]
          }
        }
      ],
      buttons: [
        {
          label: "View Quote",
          type: "+",
          action: {
            type: "open.url",
            data: {
              web: "https://subtle-exactly-glider.ngrok-free.app/app/quote/QT-2024-001"
            }
          }
        },
        {
          label: "Convert to Invoice",
          type: "+",
          action: {
            type: "invoke.function",
            data: {
              name: "convert_quote_to_invoice"
            }
          }
        },
        {
          label: "Send to Customer",
          type: "+",
          action: {
            type: "invoke.function",
            data: {
              name: "send_quote_email"
            }
          }
        }
      ]
    };
    
    const response = await fetch(CHANNEL_API, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(quoteItems)
    });
    
    console.log("Quote items status:", response.status);
    const responseText = await response.text();
    console.log("Quote items response:", responseText);
    
    let data;
    try {
      data = JSON.parse(responseText);
    } catch (e) {
      data = { rawResponse: responseText };
    }
    
    res.json({
      success: true,
      status: response.status,
      message: "Quote items sent",
      data: data
    });
  } catch (error) {
    console.error("Quote items error:", error);
    res.status(500).json({ error: error.message });
  }
});

// Send team notification with @participants mention
app.post("/send-team-notification", async (req, res) => {
  try {
    console.log("Sending team notification...");
    
    const teamNotification = {
      text: "🚨 **URGENT TEAM ALERT** {@participants}\n\nSystem maintenance scheduled for tonight at 2:00 AM. Please save your work and expect 2 hours of downtime.",
      card: {
        title: "SYSTEM MAINTENANCE ALERT",
        theme: "modern-inline",
        thumbnail: "https://via.placeholder.com/150x100/dc3545/ffffff?text=Alert"
      },
      slides: [
        {
          type: "table",
          title: "Maintenance Details",
          data: {
            headers: ["Field", "Value"],
            rows: [
              { "Field": "Type", "Value": "System Maintenance" },
              { "Field": "Date", "Value": "Tonight" },
              { "Field": "Time", "Value": "2:00 AM - 4:00 AM" },
              { "Field": "Duration", "Value": "2 hours" },
              { "Field": "Impact", "Value": "All systems offline" }
            ]
          }
        }
      ],
      buttons: [
        {
          label: "Acknowledge",
          type: "+",
          action: {
            type: "invoke.function",
            data: {
              name: "acknowledge_maintenance"
            }
          }
        },
        {
          label: "View Status",
          type: "+",
          action: {
            type: "open.url",
            data: {
              web: "https://subtle-exactly-glider.ngrok-free.app/app/status/maintenance"
            }
          }
        }
      ]
    };
    
    const response = await fetch(CHANNEL_API, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(teamNotification)
    });
    
    console.log("Team notification status:", response.status);
    const responseText = await response.text();
    console.log("Team notification response:", responseText);
    
    let data;
    try {
      data = JSON.parse(responseText);
    } catch (e) {
      data = { rawResponse: responseText };
    }
    
    res.json({
      success: true,
      status: response.status,
      message: "Team notification sent",
      data: data
    });
  } catch (error) {
    console.error("Team notification error:", error);
    res.status(500).json({ error: error.message });
  }
});

// Send simple mention message
app.post("/send-mention", async (req, res) => {
  try {
    console.log("Sending mention message...");
    
    const mentionMessage = {
      text: "👋 **Good Morning Team!** {@participants}\n\nHope everyone has a productive day ahead! 🌅"
    };
    
    const response = await fetch(CHANNEL_API, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(mentionMessage)
    });
    
    console.log("Mention status:", response.status);
    const responseText = await response.text();
    console.log("Mention response:", responseText);
    
    let data;
    try {
      data = JSON.parse(responseText);
    } catch (e) {
      data = { rawResponse: responseText };
    }
    
    res.json({
      success: true,
      status: response.status,
      message: "Mention message sent",
      data: data
    });
  } catch (error) {
    console.error("Mention error:", error);
    res.status(500).json({ error: error.message });
  }
});

// Send project enquiry with specific user mentions
app.post("/send-project-enquiry", async (req, res) => {
  try {
    console.log("Sending project enquiry...");
    
    const projectEnquiry = {
      text: "🎯 **NEW PROJECT ENQUIRY** {@aswathy@elina.so}\n\nA new project enquiry has been received. Please review and create the project.",
      card: {
        title: "PROJECT ENQUIRY",
        theme: "modern-inline",
        thumbnail: "https://via.placeholder.com/150x100/17a2b8/ffffff?text=Enquiry"
      },
      slides: [
        {
          type: "table",
          title: "Enquiry Details",
          data: {
            headers: ["Field", "Value"],
            rows: [
              { "Field": "Company", "Value": "BGC Technologies" },
              { "Field": "Contact Person", "Value": "Sunit Kumar" },
              { "Field": "Email", "Value": "sunit@bgc.in" },
              { "Field": "Phone", "Value": "+91-9876543210" },
              { "Field": "Project Type", "Value": "E-commerce Website" },
              { "Field": "Budget Range", "Value": "$10,000 - $15,000" },
              { "Field": "Timeline", "Value": "3-4 months" },
              { "Field": "Priority", "Value": "High" }
            ]
          }
        },
        {
          type: "text",
          title: "Project Requirements",
          data: "The client needs a complete e-commerce solution with:\n• User authentication and profiles\n• Product catalog with search\n• Shopping cart and checkout\n• Payment gateway integration\n• Admin dashboard\n• Mobile responsive design"
        }
      ],
      buttons: [
        {
          label: "Create Project",
          type: "+",
          action: {
            type: "invoke.function",
            data: {
              name: "create_new_project"
            }
          }
        },
        {
          label: "Send Quote",
          type: "+",
          action: {
            type: "invoke.function",
            data: {
              name: "generate_quote"
            }
          }
        },
        {
          label: "Contact Customer",
          type: "+",
          action: {
            type: "open.url",
            data: {
              web: "https://subtle-exactly-glider.ngrok-free.app/app/contact/sunit@bgc.in"
            }
          }
        }
      ]
    };
    
    const response = await fetch(CHANNEL_API, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(projectEnquiry)
    });
    
    console.log("Project enquiry status:", response.status);
    const responseText = await response.text();
    console.log("Project enquiry response:", responseText);
    
    let data;
    try {
      data = JSON.parse(responseText);
    } catch (e) {
      data = { rawResponse: responseText };
    }
    
    res.json({
      success: true,
      status: response.status,
      message: "Project enquiry sent",
      data: data
    });
  } catch (error) {
    console.error("Project enquiry error:", error);
    res.status(500).json({ error: error.message });
  }
});

// Send quote assignment with user mention
app.post("/send-quote-assignment", async (req, res) => {
  try {
    console.log("Sending quote assignment...");
    
    const quoteAssignment = {
      text: "📄 **QUOTE ASSIGNMENT** {@rakshitha@elina.so}\n\nPlease prepare and send the quote to the customer. Point of contact details provided.",
      card: {
        title: "QUOTE ASSIGNMENT",
        theme: "prompt",
        thumbnail: "https://via.placeholder.com/150x100/ffc107/ffffff?text=Quote"
      },
      slides: [
        {
          type: "table",
          title: "Customer Details",
          data: {
            headers: ["Field", "Value"],
            rows: [
              { "Field": "Company", "Value": "BGC Technologies" },
              { "Field": "Contact Person", "Value": "Sunit Kumar" },
              { "Field": "Email", "Value": "sunit@bgc.in" },
              { "Field": "Phone", "Value": "+91-9876543210" },
              { "Field": "Project", "Value": "E-commerce Website" },
              { "Field": "Assigned To", "Value": "Rakshitha" }
            ]
          }
        },
        {
          type: "text",
          title: "Quote Requirements",
          data: "Please include:\n• Detailed project scope\n• Timeline breakdown\n• Cost breakdown\n• Payment terms\n• Warranty information\n• Support details"
        }
      ],
      buttons: [
        {
          label: "Generate Quote",
          type: "+",
          action: {
            type: "invoke.function",
            data: {
              name: "generate_customer_quote"
            }
          }
        },
        {
          label: "Send Email",
          type: "+",
          action: {
            type: "invoke.function",
            data: {
              name: "send_quote_email"
            }
          }
        },
        {
          label: "Contact Customer",
          type: "+",
          action: {
            type: "open.url",
            data: {
              web: "https://subtle-exactly-glider.ngrok-free.app/app/contact/sunit@bgc.in"
            }
          }
        }
      ]
    };
    
    const response = await fetch(CHANNEL_API, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(quoteAssignment)
    });
    
    console.log("Quote assignment status:", response.status);
    const responseText = await response.text();
    console.log("Quote assignment response:", responseText);
    
    let data;
    try {
      data = JSON.parse(responseText);
    } catch (e) {
      data = { rawResponse: responseText };
    }
    
    res.json({
      success: true,
      status: response.status,
      message: "Quote assignment sent",
      data: data
    });
  } catch (error) {
    console.error("Quote assignment error:", error);
    res.status(500).json({ error: error.message });
  }
});

// Send new project added card and create a discussion thread
app.post("/send-new-project", async (req, res) => {
  try {
    // Extract project details from request body or use defaults for demo
    const {
      project_id = "PROJ-0004",
      assigned_to = "aswathy@elina.so",
      customer_name = "BGC",
      erp_link = `https://subtle-exactly-glider.ngrok-free.app/app/project/${project_id}`
    } = req.body || {};

    console.log("Creating new project card...");

    // 1️⃣ Post the main message (sync_message=true to retrieve message_id)
    const newProjectCard = {
      card: {
        title: "NEW PROJECT ADDED",
        theme: "modern-inline",
      },
      text: `**NEW PROJECT ADDED** {@${assigned_to}}`,   
      slides: [
        {
          type: "table",
          title: "Project Summary",
          data: {
            headers: ["Field", "Value"],
            rows: [
              { "Field": "Project ID", "Value": project_id },
              { "Field": "Assigned To", "Value": assigned_to },
              { "Field": "Customer", "Value": customer_name },
            ]
          }
        }
      ],
      buttons: [
        {
          label: "More Details",
          type: "+",
          action: {
            type: "open.url",
            data: {
              web: erp_link
            }
          }
        }
      ],
      sync_message: true
    };

    // First API call
    const mainRes = await fetch(CHANNEL_API, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(newProjectCard)
    });

    const mainText = await mainRes.text();
    let mainJson;
    try { mainJson = JSON.parse(mainText); } catch { mainJson = {}; }
    
    console.log("Main response text:", mainText);
    console.log("Main response JSON:", mainJson);
    
    const message_id = mainJson.message_id || (mainJson.data && mainJson.data.message_id);

    console.log("Main message status:", mainRes.status, "message_id:", message_id);

    if (!message_id) {
      return res.status(500).json({ 
        error: "Failed to obtain message_id", 
        response: mainJson,
        responseText: mainText 
      });
    }

    // 2️⃣ Create thread and post initial thread message
    const threadPayload = {
      text: `Thread for project **${project_id}** discussions.\nPlease use this thread to collaborate on tasks, updates, and clarifications.`,
      thread_message_id: message_id,
      thread_title: `Discussion – ${project_id}`,
      sync_message: true
    };

    console.log("Thread payload:", JSON.stringify(threadPayload, null, 2));

    // Try with bot_unique_name parameter
    const threadUrl = `${CHANNEL_API}&bot_unique_name=${BOT_UNIQUE_NAME}`;
    console.log("Thread URL:", threadUrl);

    const threadRes = await fetch(threadUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(threadPayload)
    });

    const threadText = await threadRes.text();
    let threadJson;
    try { threadJson = JSON.parse(threadText); } catch { threadJson = {}; }

    console.log("Thread response text:", threadText);
    console.log("Thread message status:", threadRes.status, threadJson);

    // If first attempt didn't work, try alternative approach
    if (threadRes.status !== 200 || !threadJson.message_id) {
      console.log("Trying alternative thread creation approach...");
      
      // Try without bot_unique_name
      const altThreadRes = await fetch(CHANNEL_API, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(threadPayload)
      });

      const altThreadText = await altThreadRes.text();
      let altThreadJson;
      try { altThreadJson = JSON.parse(altThreadText); } catch { altThreadJson = {}; }

      console.log("Alternative thread response:", altThreadText);
      console.log("Alternative thread status:", altThreadRes.status, altThreadJson);
      
      threadJson = altThreadJson;
    }

    res.json({
      success: true,
      main_message: mainJson,
      thread_message: threadJson,
      message_id: message_id
    });
  } catch (error) {
    console.error("New project error:", error);
    res.status(500).json({ error: error.message });
  }
});

app.listen(3050, () => {
  console.log("✅ Server running on http://localhost:3050");
});
