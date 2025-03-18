from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# Load environment variables
load_dotenv()

app = Flask(__name__)

def send_email_notification(to_email, subject, message):
    sendgrid_api_key = os.getenv('SENDGRID_API_KEY')
    
    if not sendgrid_api_key:
        return {"error": "Missing SendGrid API Key"}, 500
    
    from_email = 'medgrab0@gmail.com'  

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

@app.route('/send-email', methods=['POST'])
def send_email():
    data = request.get_json()
    to_email = data.get("to_email")
    subject = data.get("subject")
    message = data.get("message")

    if not to_email or not subject or not message:
        return jsonify({"error": "Missing required fields"}), 400

    result = send_email_notification(to_email, subject, message)
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)


#http://127.0.0.1:5000/send-email 
# {
#   "to_email": "recipient@example.com",
#   "subject": "Hello from Flask",
#   "message": "<h1>This is an HTML email</h1>"
# }