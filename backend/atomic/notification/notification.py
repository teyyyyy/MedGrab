from flask import Flask, Blueprint, request, jsonify
from dotenv import load_dotenv
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from atomic.firestore import db
import datetime

# Load environment variables
load_dotenv()

# Initialize Flask and Firestore DB
app = Flask(__name__)
notification_bp = Blueprint('notification', __name__)

# Function to send email using SendGrid
def send_email_notification(to_email, subject, message):
    sendgrid_api_key = os.getenv('SENDGRID_API_KEY')
    
    if not sendgrid_api_key:
        return {"error": "Missing SendGrid API Key"}, 500
    
    from_email = 'medgrab0@gmail.com'  # Change to your email address

    email_message = Mail(
        from_email=from_email,
        to_emails=to_email,
        subject=subject,
        html_content=message
    )

    try:
        sg = SendGridAPIClient(sendgrid_api_key)
        response = sg.send(email_message)
        return {
            "message": "Email sent successfully",
            "status_code": response.status_code
        }
    except Exception as e:
        return {"error": str(e)}, 500


# API endpoint to send email
@app.route('/api/notifications/send-email', methods=['POST'])
def send_email():
    data = request.get_json()
    to_email = data.get("to_email")
    subject = data.get("subject")
    message = data.get("message")

    if not to_email or not subject or not message:
        return jsonify({"error": "Missing required fields"}), 400

    # Send email
    email_result = send_email_notification(to_email, subject, message)
    
    if email_result.get('status_code') != 202:
        return jsonify(email_result), 500  # SendGrid email not sent


    return jsonify({"message": "Email sent!"}), 200

# Register the blueprint for notifications
app.register_blueprint(notification_bp)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002)
