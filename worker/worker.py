import signal
from typing import Any, Callable, Optional

from config import CLOUDAMQP_URL
from logger import logger
from helpers.rabbitMQ import (
    connect_to_rabbitmq,
    declare_queues,
    consume,
    publish,
)


class Worker:
    """
    Generic RabbitMQ worker.

    A worker consumes messages from an input queue, processes each message,
    and optionally publishes the result to an output queue.

    Args:
        name: Human-readable worker name.
        queue: Queue from which messages are consumed.
        process_fn: Function responsible for processing a message.
        output_queue: Optional queue where processed results are published.
    """

    def __init__(
        self,
        name: str,
        queue: str,
        process_fn: Callable[[Any], Any],
        output_queue: Optional[str] = None,
    ):
        self.name = name
        self.queue = queue
        self.process_fn = process_fn
        self.output_queue = output_queue

        self.connection = None
        self.channel = None
        self.running = True

    def connect(self) -> None:
        """
        Establish the RabbitMQ connection and declare required queues.
        """
        self.connection, self.channel = connect_to_rabbitmq(
            CLOUDAMQP_URL
        )

        if not self.connection or not self.channel:
            raise RuntimeError("Failed to connect to RabbitMQ")

        queues = [self.queue]

        if self.output_queue:
            queues.append(self.output_queue)

        declare_queues(
            self.channel,
            *queues,
        )

        logger.info(
            f"{self.name} connected to RabbitMQ"
        )

    def stop(self, *_args) -> None:
        """
        Stop the worker gracefully.
        """
        logger.info(f"Stopping {self.name} worker")
        self.running = False

        if self.channel and not self.channel.is_closed:
            self.channel.stop_consuming()

    def process(self, message: Any) -> None:
        """
        Process a single message.

        Args:
            message: Message received from RabbitMQ.
        """
        result = self.process_fn(message)

        if result is not None and self.output_queue:
            publish(
                self.channel,
                self.output_queue,
                result,
            )

    def handle_message(self, message: Any) -> None:
        """
        Handle an individual RabbitMQ message.

        Processing errors are logged and do not terminate the worker.
        """
        try:
            self.process(message)

            logger.info(
                f"{self.name} processed message"
            )

        except Exception:
            logger.exception(
                f"{self.name} failed to process message"
            )

    def start(self) -> None:
        """
        Start consuming messages from the configured queue.
        """
        self.connect()

        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)

        logger.info(
            f"Starting {self.name} worker"
        )

        try:
            consume(
                self.channel,
                self.queue,
                self.handle_message,
            )
        except KeyboardInterrupt:
            self.stop()
        finally:
            self.close()

    def close(self) -> None:
        """
        Close the RabbitMQ connection.
        """
        if self.connection and not self.connection.is_closed:
            self.connection.close()

            logger.info(
                f"{self.name} connection closed"
            )

    def run(self) -> None:
        """
        Run the worker and handle unexpected failures.
        """
        try:
            self.start()

        except Exception:
            logger.exception(
                f"{self.name} worker failed"
            )
            raise

        finally:
            self.close()