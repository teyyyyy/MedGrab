from flask import Flask, Blueprint, request, jsonify
from dotenv import load_dotenv
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
import base64
import aio_pika
import asyncio
import json
import threading
from flask_cors import CORS

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)
notification_bp = Blueprint('notification', __name__)

AMQP_HOST = os.getenv('AMQP_HOST')
AMQP_PORT = int(os.getenv('AMQP_PORT'))
EXCHANGE_NAME = os.getenv('AMQP_EXCHANGE')
EXCHANGE_TYPE = os.getenv('AMQP_EXCHANGE_TYPE')
NOTIFICATION_ROUTING_KEY = os.getenv('NOTIFICATION_ROUTING_KEY')
NOTIFICATION_QUEUE = os.getenv('NOTIFICATION_QUEUE')

# Function to send email using SendGrid
def send_email_notification(to_email, subject, message, attachment=None, attachment_name="report.pdf"):
    sendgrid_api_key = os.getenv('SENDGRID_API_KEY')
    
    if not sendgrid_api_key:
        print("Missing SendGrid API Key!")
        return {"error": "Missing SendGrid API Key"}, 500
    
    from_email = 'medgrab0@gmail.com'  

    email_message = Mail(
        from_email=from_email,
        to_emails=to_email,
        subject=subject,
        html_content=message
    )

    # Add attachment if provided
    if attachment:
        if isinstance(attachment, str):
            # If attachment is a file path
            with open(attachment, 'rb') as f:
                data = f.read()
        else:
            # If attachment is bytes
            data = attachment
        
        encoded = base64.b64encode(data).decode()
        
        attached_file = Attachment(
            FileContent(encoded),
            FileName(attachment_name),
            FileType('application/pdf'),
            Disposition('attachment')
        )
        email_message.attachment = attached_file

    try:
        sg = SendGridAPIClient(sendgrid_api_key)
        response = sg.send(email_message)
        print(f"Email sent to {to_email}, status code: {response.status_code}")
        return {
            "message": "Email sent successfully",
            "status_code": response.status_code
        }
    except Exception as e:
        print(f"Email sending failed: {str(e)}")
        return {"error": str(e)}, 500

async def email_notification_callback(message):
    async with message.process():
        try:
            notification = json.loads(message.body.decode())
            
            # Required fields
            to_email = notification.get("to_email")
            subject = notification.get("subject")
            message_content = notification.get("message")
            
            if not all([to_email, subject, message_content]):
                print("Missing required email fields")
                return
            
            # Optional attachment
            attachment = None
            if "attachment" in notification:
                attachment = base64.b64decode(notification["attachment"])
            
            attachment_name = notification.get("attachment_name", "report.pdf")
            
            # Send email
            email_result = send_email_notification(
                to_email,
                subject,
                message_content,
                attachment=attachment,
                attachment_name=attachment_name
            )
            print(f"Email result: {email_result}")
            
        except Exception as e:
            print(f"Error processing message: {e}")
            
# AMQP consumer setup function
async def setup_consumer():
    """Set up the AMQP consumer"""
    try:
        # Connect to RabbitMQ
        connection = await aio_pika.connect_robust(
            f"amqp://guest:guest@{AMQP_HOST}:{AMQP_PORT}/"
        )
        channel = await connection.channel()
        
        # Declare the exchange
        exchange = await channel.declare_exchange(
            EXCHANGE_NAME,
            type=EXCHANGE_TYPE,
            durable=True
        )
        
        # Declare the queue
        queue = await channel.declare_queue(
            NOTIFICATION_QUEUE,
            durable=True
        )
        
        # Bind the queue to the exchange with routing key
        await queue.bind(exchange, routing_key=NOTIFICATION_ROUTING_KEY)
        
        # Start consuming messages
        await queue.consume(email_notification_callback)
        
        print(f"Consumer setup complete. Listening for messages on queue '{NOTIFICATION_QUEUE}'")
        print(f"Exchange: {EXCHANGE_NAME}, Routing key: {NOTIFICATION_ROUTING_KEY}")
        
        return connection
    except Exception as e:
        print(f"Failed to set up consumer: {e}")
        raise

# Function to start the consumer in a separate thread
def start_consumer():
    """Start the AMQP consumer in a separate event loop"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    async def run_consumer():
        connection = await setup_consumer()
        try:
            # Keep the consumer running
            while True:
                await asyncio.sleep(1)
        except Exception as e:
            print(f"Consumer error: {e}")
        finally:
            await connection.close()
    
    try:
        loop.run_until_complete(run_consumer())
    except KeyboardInterrupt:
        print("Consumer stopped")
    finally:
        loop.close()

# REST API endpoints for direct email sending
@notification_bp.route('/send-email', methods=['POST'])
def send_email_endpoint():
    """REST endpoint to send email directly"""
    data = request.json
    to_email = data.get('to_email')
    subject = data.get('subject')
    message = data.get('message')
    
    if not all([to_email, subject, message]):
        return jsonify({"error": "Missing required fields"}), 400
    
    result = send_email_notification(to_email, subject, message)
    return jsonify(result)

def init_app(app):
    """Initialize the notification blueprint and start consumer thread"""
    app.register_blueprint(notification_bp, url_prefix='/api/notifications')
    
    # Start the consumer in a separate thread
    consumer_thread = threading.Thread(target=start_consumer, daemon=True)
    consumer_thread.start()
    print("Notification consumer thread started")

# If running directly, start the Flask app and consumer
if __name__ == "__main__":
    init_app(app)
    app.run(host='0.0.0.0', port=5002, debug=True)