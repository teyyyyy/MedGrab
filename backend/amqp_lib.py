import asyncio
import aio_pika
import json

async def connect(hostname, port, exchange_name, exchange_type):
    """Connect to RabbitMQ asynchronously and declare exchange"""
    connection = await aio_pika.connect_robust(f"amqp://{hostname}:{port}")
    channel = await connection.channel()  # creating a channel
    
    # Declare an exchange (it will create if it does not exist)
    await channel.declare_exchange(exchange_name, exchange_type, durable=True)
    return connection, channel


async def close(connection, channel):
    """Close connection and channel gracefully"""
    await channel.close()
    await connection.close()


async def send_message(channel, exchange_name, routing_key, message):
    """Publish a message to the specified exchange with routing key"""
    await channel.default_exchange.publish(
        aio_pika.Message(body=message.encode()),
        routing_key=routing_key
    )


async def create_queue(channel, exchange_name, queue_name, routing_key):
    """Declare a queue and bind it to an exchange with a routing key"""
    queue = await channel.declare_queue(queue_name, durable=True)
    await queue.bind(exchange_name, routing_key=routing_key)
    return queue


async def consume_messages(channel, queue_name, callback):
    """Consume messages from a RabbitMQ queue"""
    queue = await channel.declare_queue(queue_name, durable=True)

    # Define what happens when a message is received
    async def on_message(message: aio_pika.abc.AbstractIncomingMessage):
        async with message.process():
            await callback(message)

    # Start consuming messages
    await queue.consume(on_message)

    print(f"Consuming from {queue_name}. Press Ctrl+C to exit.")
    try:
        # Keeps the consumer running
        await asyncio.Future()  # Run forever
    except KeyboardInterrupt:
        pass


async def email_notification_callback(message):
    """Callback function for processing email notifications"""
    # Assume the message body contains a JSON string with the email content
    body = message.body.decode()
    notification = json.loads(body)

    # Process the notification (e.g., send an email)
    print(f"Received notification: {notification}")
    
    # You can implement email-sending logic here
    # Example: send_email(notification["to_email"], notification["subject"], notification["message"])


# Example of usage in your main script
async def main():
    hostname = "localhost"
    port = 5672
    exchange_name = "report_exchange"
    routing_key = "report.notification"
    queue_name = "report_notifications"

    connection, channel = await connect(hostname, port, exchange_name, "topic")

    # Send a test message to RabbitMQ
    test_message = json.dumps({
        "to_email": "nurse@example.com",
        "subject": "Monthly Report",
        "message": "Here is your monthly report."
    })
    await send_message(channel, exchange_name, routing_key, test_message)

    # Start consuming messages from the queue
    await consume_messages(channel, queue_name, email_notification_callback)

    # Close connection and channel after done
    await close(connection, channel)

if __name__ == "__main__":
    asyncio.run(main())
