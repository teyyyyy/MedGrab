from flask import Flask, request, jsonify
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# URL of the notification service
NOTIFICATION_SERVICE_URL = "http://127.0.0.1:5000/send-email"  # Change if deployed elsewhere

def send_email_via_service(to_email, subject, message):
    """Calls the notification service to send an email"""
    email_data = {
        "to_email": to_email,
        "subject": subject,
        "message": message
    }
    
    try:
        response = requests.post(NOTIFICATION_SERVICE_URL, json=email_data)
        return response.json()  # Return the response from the notification service
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}, 500

@app.route('/check-credit-score', methods=['POST'])
def check_credit_score_and_notify():
    data = request.get_json()
    email = data.get("email")
    name = data.get("name")
    credit_score = data.get("credit_score")
    is_suspended = data.get("is_suspended")
    is_suspended= "NO"

    if email is None or name is None or credit_score is None:
        return jsonify({"error": "Missing required fields"}), 400

    if credit_score < 50:
        is_suspended = "YES"
        send_email_via_service(
            email,
            "Suspension",
            "You are suspended for a month due to frequent cancellations/bad conduct."
        )
        credit_score = 50  # Reset credit score after suspension

    elif credit_score < 70:
        send_email_via_service(
            email,
            "Warning",
            "Warning of bad conduct."
        )

    else:
        print(f"{name} has a good credit score. No action required.")

    updated_user = {
        "name": name,
        "email": email,
        "credit_score": credit_score,
        "is_suspended": is_suspended
    }

    return jsonify(updated_user)

if __name__ == '__main__':
    app.run(port=5001,debug=True)
