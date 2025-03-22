import aio_pika
import os
import asyncio
import json


# AMQP configurations
AMQP_HOST = os.getenv('AMQP_HOST', 'localhost')  # Updated default host
AMQP_PORT = int(os.getenv('AMQP_PORT', '5672'))
EXCHANGE_NAME = os.getenv('AMQP_EXCHANGE', 'report_exchange')
EXCHANGE_TYPE = os.getenv('AMQP_EXCHANGE_TYPE', 'topic')
NOTIFICATION_ROUTING_KEY = os.getenv('NOTIFICATION_ROUTING_KEY', 'report.notification')

# Global AMQP connection and channel
amqp_connection = None
amqp_channel = None

async def setup_amqp():
    """Initialize the AMQP connection and channel."""
    global amqp_connection, amqp_channel
    try:
        # Connect to RabbitMQ
        amqp_connection = await aio_pika.connect_robust(
            f"amqp://{AMQP_HOST}:{AMQP_PORT}/"
        )
        # Create a channel
        amqp_channel = await amqp_connection.channel()
        print("AMQP connection and channel established")
        return amqp_connection, amqp_channel
    except Exception as e:
        print(f"Failed to establish AMQP connection: {e}")
        raise

async def close_amqp():
    """Close the AMQP connection and channel."""
    global amqp_connection, amqp_channel
    if amqp_connection is not None:
        await amqp_connection.close()
        print("AMQP connection closed")
    if amqp_channel is not None:
        await amqp_channel.close()
        print("AMQP channel closed")

async def send_notification_amqp(to_email, subject, message):
    """Send a notification via AMQP."""
    global amqp_connection, amqp_channel
    
    # If connection or channel is not initialized or closed, set it up
    if amqp_connection is None or amqp_channel is None or amqp_connection.is_closed or amqp_channel.is_closed:
        amqp_connection, amqp_channel = await setup_amqp()
    
    notification_data = {
        "to_email": to_email,
        "subject": subject,
        "message": message
    }
    
    # Convert the notification data to JSON string
    json_message = json.dumps(notification_data)
    
    try:
        # Send the message to RabbitMQ
        await amqp_channel.default_exchange.publish(
            aio_pika.Message(body=json_message.encode()),
            routing_key=NOTIFICATION_ROUTING_KEY
        )
        print("Notification sent via AMQP")
        return {"success": True, "message": "Notification queued for delivery"}
    except Exception as e:
        print(f"Failed to send notification: {e}")
        return {"success": False, "message": f"Failed to send notification: {e}"}