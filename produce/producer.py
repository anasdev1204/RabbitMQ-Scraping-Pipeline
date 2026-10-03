from config import CLOUDAMQP_URL
from logger import logger

from helpers.rabbitMQ import (
    connect_to_rabbitmq,
    declare_queues,
    publish,
)


class Producer:
    """
    Generic RabbitMQ producer that executes a scraper and publishes
    the resulting items to a queue.
    """

    def __init__(self, name: str, queue: str, scraper_fn):
        """
        Initialize a RabbitMQ producer.

        Args:
            name: Human-readable name used for logging.
            queue: Name of the RabbitMQ queue to publish to.
            scraper_fn: Function responsible for scraping the data.
        """
        self.name = name
        self.queue = queue
        self.scraper_fn = scraper_fn
        self.connection = None
        self.channel = None

    def connect(self):
        """
        Establish a connection to RabbitMQ and declare the target queue.

        Raises:
            Exception: If the RabbitMQ connection, channel, or queue
                configuration fails.
        """
        self.connection, self.channel = connect_to_rabbitmq(
            CLOUDAMQP_URL
        )

        if not self.connection or not self.channel or self.queue is None:
            logger.error(
                "Failed to connect to RabbitMQ or declare queue"
            )
            raise Exception(
                "Failed to connect to RabbitMQ or declare queue"
            )

        declare_queues(
            self.channel,
            self.queue
        )

    def produce(self):
        """
        Run the scraper and publish the resulting items to RabbitMQ.

        Each scraped item is published individually to the configured
        queue. A failure to publish one item is logged without stopping the remaining items from being processed.
        """
        logger.info(f"Starting {self.name} producer")

        scraped_data = self.scraper_fn()

        if not scraped_data:
            logger.warning(f"No data found in {self.name} scraper")
            return

        logger.info(
            f"Found {len(scraped_data)} items in {self.name} scraper"
        )

        for sd in scraped_data:
            try:
                publish(
                    self.channel,
                    self.queue,
                    sd
                )

                logger.info(
                    f"Queued {self.name} item: "
                    f"{sd.get('name', 'Unknown')}"
                )

            except Exception as e:
                logger.error(
                    f"Failed to queue {self.name} item: "
                    f"{sd.get('name', 'Unknown')}. Error: {e}"
                )

        logger.info(
            f"Finished queueing {len(scraped_data)} "
            f"{self.name} items"
        )

    def close(self):
        """
        Close the RabbitMQ connection if it is currently open.
        """
        if self.connection and not self.connection.is_closed:
            self.connection.close()

            logger.info(
                "League producer connection closed"
            )

    def run(self):
        """
        Execute the complete producer lifecycle.

        The lifecycle consists of connecting to RabbitMQ, producing
        messages, and closing the connection regardless of whether
        an error occurs.

        Raises:
            Exception: Re-raises any exception encountered during
                connection or production.
        """
        try:
            self.connect()
            self.produce()

        except Exception as e:
            logger.exception(
                f"League producer failed: {e}"
            )
            raise

        finally:
            self.close()