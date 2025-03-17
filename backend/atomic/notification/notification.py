from dotenv import load_dotenv, find_dotenv
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
load_dotenv()
def send_email_notification(to_email, subject, message):
    # Twilio SendGrid API key (you need to get this from your SendGrid account)
    sendgrid_api_key = os.getenv('SENDGRID_API_KEY')
    print(f"Loaded SendGrid API Key: {sendgrid_api_key}")

    # Create the email object
    from_email = 'medgrab0@gmail.com'  # This is your email address
    to_email = to_email  # The recipient's email
    subject = subject  # Subject of the email
    content = message  # The message content

    # Create the email message
    message = Mail(
        from_email=from_email,
        to_emails=to_email,
        subject=subject,
        html_content=content
    )

    try:
        # Send the email using SendGrid's API
        sg = SendGridAPIClient(sendgrid_api_key)
        response = sg.send(message)

        # Print the response status code and message
        print(f"Email sent successfully. Status Code: {response.status_code}")
        print(response.body)
        print(response.headers)
    except Exception as e:
        print(f"Error: {str(e)}")

# Usage example
#send_email_notification('email', 'Notification Subject', 'This is your notification message.')

