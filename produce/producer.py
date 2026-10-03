from config import CLOUDAMQP_URL
from logger import logger

from helpers.rabbitMQ import (
    connect_to_rabbitmq,
    declare_queues,
    publish,
)



class Producer:
    def __init__(self, name: str, queue: str, scraper_fn):
        self.name = name
        self.queue = queue
        self.scraper_fn = scraper_fn
        self.connection = None
        self.channel = None

    def connect(self):
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
                    f"Queued {self.name} item: {sd.get('name', 'Unknown')}"
                )

            except Exception as e:
                logger.error(
                    f"Failed to queue {self.name} item: {sd.get('name', 'Unknown')}. Error: {e}"
                )

        logger.info(
            f"Finished queueing {len(scraped_data)} {self.name} items"
        )

    def close(self):
        if self.connection and not self.connection.is_closed:
            self.connection.close()

            logger.info(
                "League producer connection closed"
            )

    def run(self):
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