import aio_pika
import os
import asyncio
import json

# AMQP configurations
AMQP_HOST = os.getenv('AMQP_HOST', 'localhost')  # RabbitMQ host
AMQP_PORT = int(os.getenv('AMQP_PORT', '5672'))  # RabbitMQ port
EXCHANGE_NAME = os.getenv('AMQP_EXCHANGE', 'medgrab_exchange')  # Renamed exchange
EXCHANGE_TYPE = os.getenv('AMQP_EXCHANGE_TYPE', 'topic')  # Exchange type
NOTIFICATION_ROUTING_KEY = os.getenv('NOTIFICATION_ROUTING_KEY', 'notification.email')  # Updated routing key
NOTIFICATION_QUEUE = os.getenv('NOTIFICATION_QUEUE', 'email_notifications')  # Added queue name

# Global AMQP connection and channel
amqp_connection = None
amqp_channel = None
exchange = None


async def setup_amqp():
    """Initialize the AMQP connection and channel."""
    global amqp_connection, amqp_channel, exchange
    try:
        # Connect to RabbitMQ
        amqp_connection = await aio_pika.connect_robust(
            f"amqp://guest:guest@{AMQP_HOST}:{AMQP_PORT}/"
        )
        # Create a channel
        amqp_channel = await amqp_connection.channel()

        # Declare the exchange - this is critical
        exchange = await amqp_channel.declare_exchange(
            EXCHANGE_NAME,
            type=EXCHANGE_TYPE,
            durable=True
        )
        print(f"AMQP connection established to {AMQP_HOST}:{AMQP_PORT}")
        print(f"Exchange '{EXCHANGE_NAME}' of type '{EXCHANGE_TYPE}' declared")

        return amqp_connection, amqp_channel, exchange
    except Exception as e:
        print(f"Failed to establish AMQP connection: {e}")
        raise


async def close_amqp():
    """Close the AMQP connection and channel."""
    global amqp_connection, amqp_channel
    if amqp_channel is not None:
        await amqp_channel.close()
        print("AMQP channel closed")
    if amqp_connection is not None:
        await amqp_connection.close()
        print("AMQP connection closed")


async def send_notification_amqp(to_email, subject, message):
    """Send a notification via AMQP."""
    global amqp_connection, amqp_channel, exchange

    # If connection or channel is not initialized or closed, set it up
    if amqp_connection is None or amqp_channel is None or amqp_connection.is_closed or amqp_channel.is_closed:
        amqp_connection, amqp_channel, exchange = await setup_amqp()

    notification_data = {
        "to_email": to_email,
        "subject": subject,
        "message": message
    }

    # Convert the notification data to JSON string
    json_message = json.dumps(notification_data)

    try:
        # Send the message through the exchange with routing key
        await exchange.publish(
            aio_pika.Message(
                body=json_message.encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            ),
            routing_key=NOTIFICATION_ROUTING_KEY
        )
        print(f"Notification sent via AMQP: {json_message}")
        print(f"Routing key: {NOTIFICATION_ROUTING_KEY}")
        return {"success": True, "message": "Notification queued for delivery"}
    except Exception as e:
        print(f"Failed to send notification: {e}")
        return {"success": False, "message": f"Failed to send notification: {e}"}