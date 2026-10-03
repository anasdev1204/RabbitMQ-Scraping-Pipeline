import json
import pika


def connect_to_rabbitmq(url):
    try:
        connection = pika.BlockingConnection(pika.URLParameters(url))
        channel = connection.channel()
        return connection, channel
    except pika.exceptions.AMQPConnectionError as e:
        print(f"Failed to connect to RabbitMQ: {e}")
        exit(1)

def declare_queues(channel, queues):
    for queue in queues:
        channel.queue_declare(queue=queue, durable=True)

def publish(channel, queue, message):
    channel.basic_publish(
        exchange="",
        routing_key=queue,
        body=json.dumps(message),
        properties=pika.BasicProperties(
            delivery_mode=2
        )
    )

def consume(channel, queue, callback):
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=queue, on_message_callback=callback)
    channel.start_consuming()
