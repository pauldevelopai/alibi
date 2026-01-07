"""
Email Receiver - Webhook endpoint to receive forwarded emails

This creates a simple Flask server that can receive emails forwarded via:
1. Zapier (Email → Webhook)
2. Make.com (Email → HTTP Request)
3. Mailgun Inbound Routes
4. SendGrid Inbound Parse

Run this separately from the main Streamlit app.

Usage:
    python email_receiver.py

Then configure your email forwarding service to POST to:
    http://your-server:5050/inbox

The endpoint accepts JSON with:
    {
        "from": "sender@example.com",
        "subject": "Newsletter title",
        "body": "The email content (text or HTML)",
        "html": "Optional HTML version"
    }
"""

import os
import json
from flask import Flask, request, jsonify
from datetime import datetime
from pathlib import Path

# Import our content inbox
import sys
sys.path.insert(0, str(Path(__file__).parent))
from content_inbox import add_to_inbox, parse_forwarded_email

app = Flask(__name__)

# Simple API key for security (set in .env)
API_KEY = os.getenv("INBOX_API_KEY", "developai-inbox-2024")


@app.route('/inbox', methods=['POST'])
def receive_email():
    """
    Receive an email via webhook.
    
    Expected JSON format:
    {
        "from": "sender@example.com",
        "subject": "Email subject",
        "body": "Plain text body",
        "html": "Optional HTML body"
    }
    
    Or for raw forwarded emails:
    {
        "raw": "Full email content including headers"
    }
    """
    # Check API key
    provided_key = request.headers.get('X-API-Key') or request.args.get('api_key')
    if provided_key != API_KEY:
        return jsonify({'error': 'Invalid API key'}), 401
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Handle raw forwarded email
        if 'raw' in data:
            parsed = parse_forwarded_email(data['raw'])
            content = parsed['content']
            sender = parsed['sender']
            subject = parsed['subject']
        else:
            # Structured format
            content = data.get('html') or data.get('body') or ''
            sender = data.get('from', '')
            subject = data.get('subject', '')
        
        if not content:
            return jsonify({'error': 'No content provided'}), 400
        
        # Add to inbox
        result = add_to_inbox(
            content=content,
            source="email",
            title=subject,
            sender=sender,
            content_type="newsletter"
        )
        
        if result.get('error'):
            return jsonify({'status': 'duplicate', 'message': result['error'], 'id': result.get('id')}), 200
        
        return jsonify({
            'status': 'success',
            'id': result.get('id'),
            'title': result.get('title', '')[:50],
            'message': 'Email added to inbox'
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/inbox', methods=['GET'])
def get_inbox_status():
    """Get inbox status."""
    from content_inbox import get_inbox_stats
    
    # Check API key
    provided_key = request.headers.get('X-API-Key') or request.args.get('api_key')
    if provided_key != API_KEY:
        return jsonify({'error': 'Invalid API key'}), 401
    
    stats = get_inbox_stats()
    return jsonify({
        'status': 'ok',
        'stats': stats,
    })


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'service': 'email-receiver'})


# ============================================================================
# Instructions
# ============================================================================

SETUP_INSTRUCTIONS = """
================================================================================
EMAIL RECEIVER FOR CONTENT INBOX
================================================================================

This server receives emails forwarded to your Content Inbox.

ENDPOINTS:
  POST /inbox      - Receive an email (requires API key)
  GET  /inbox      - Get inbox stats (requires API key)
  GET  /health     - Health check

API KEY:
  Default: developai-inbox-2024
  Set custom: export INBOX_API_KEY=your-secret-key

OPTION 1: ZAPIER
----------------
1. Create a Zap: "Email → Webhooks by Zapier"
2. Set up email trigger (new email in Gmail/Outlook)
3. Add Webhooks action:
   - Method: POST
   - URL: http://your-server:5050/inbox?api_key=YOUR_KEY
   - Payload Type: JSON
   - Data:
     {
       "from": "{{from}}",
       "subject": "{{subject}}",
       "body": "{{body_plain}}"
     }

OPTION 2: MAKE.COM (Integromat)
-------------------------------
1. Create scenario: Email → HTTP
2. Watch emails in your inbox
3. Make HTTP request:
   - URL: http://your-server:5050/inbox
   - Method: POST
   - Headers: X-API-Key: YOUR_KEY
   - Body: JSON with from, subject, body

OPTION 3: GMAIL FILTER + GOOGLE APPS SCRIPT
-------------------------------------------
1. Create Gmail filter for newsletters
2. Create Apps Script:
   
   function forwardToInbox(e) {
     var message = e.message;
     var payload = {
       from: message.getFrom(),
       subject: message.getSubject(),
       body: message.getPlainBody()
     };
     UrlFetchApp.fetch('http://your-server:5050/inbox?api_key=YOUR_KEY', {
       method: 'post',
       contentType: 'application/json',
       payload: JSON.stringify(payload)
     });
   }

OPTION 4: MAILGUN INBOUND ROUTES
--------------------------------
1. Set up Mailgun inbound domain
2. Create route: forward to http://your-server:5050/inbox?api_key=YOUR_KEY
3. Forward emails to your Mailgun address

LOCAL TESTING:
  curl -X POST http://localhost:5050/inbox \\
    -H "Content-Type: application/json" \\
    -H "X-API-Key: developai-inbox-2024" \\
    -d '{"from":"test@example.com","subject":"Test Newsletter","body":"This is test content about AI..."}'

================================================================================
"""


if __name__ == "__main__":
    print(SETUP_INSTRUCTIONS)
    print(f"\nStarting email receiver on port 5050...")
    print(f"API Key: {API_KEY}")
    print(f"\nEndpoint: http://localhost:5050/inbox")
    print(f"Health:   http://localhost:5050/health\n")
    
    app.run(host='0.0.0.0', port=5050, debug=True)









