import sys

from config import CLOUDAMQP_URL
from logger import logger
from helpers.rabbitMQ import connect_to_rabbitmq


def remove_queue(queue: str) -> None:
    """
    Delete a RabbitMQ queue and all messages contained in it.

    Args:
        queue: Name of the queue to delete.

    Raises:
        Exception: If the RabbitMQ connection or deletion fails.
    """
    connection = None

    try:
        connection, channel = connect_to_rabbitmq(CLOUDAMQP_URL)

        if not connection or not channel:
            raise RuntimeError("Failed to connect to RabbitMQ")

        channel.queue_delete(queue=queue)

        logger.info(f"Deleted queue: {queue}")

    except Exception:
        logger.exception(f"Failed to delete queue: {queue}")
        raise

    finally:
        if connection and not connection.is_closed:
            connection.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 remove_queue.py <queue>")
        sys.exit(1)

    remove_queue(sys.argv[1])