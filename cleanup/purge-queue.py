import sys

from config import CLOUDAMQP_URL
from logger import logger
from helpers.rabbitMQ import connect_to_rabbitmq


def purge_queue(queue: str) -> None:
    """
    Remove all messages from a RabbitMQ queue without deleting the queue.

    Args:
        queue: Name of the queue to purge.

    Raises:
        Exception: If the RabbitMQ connection or purge operation fails.
    """
    connection = None

    try:
        connection, channel = connect_to_rabbitmq(CLOUDAMQP_URL)

        if not connection or not channel:
            raise RuntimeError("Failed to connect to RabbitMQ")

        channel.queue_purge(queue=queue)

        logger.info(f"Purged queue: {queue}")

    except Exception:
        logger.exception(f"Failed to purge queue: {queue}")
        raise

    finally:
        if connection and not connection.is_closed:
            connection.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 purge_queue.py <queue>")
        sys.exit(1)

    purge_queue(sys.argv[1])