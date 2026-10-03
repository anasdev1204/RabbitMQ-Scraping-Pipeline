import multiprocessing
from typing import Callable, List

from logger import logger
from worker.worker import Worker


class WorkerManager:
    """
    Manage multiple RabbitMQ workers running concurrently.
    """

    def __init__(
        self,
        workers: List[Callable[[], Worker]],
    ):
        self.workers = workers

    def run(self) -> None:
        """
        Start each worker in its own process.
        """
        processes = []

        for worker_factory in self.workers:
            process = multiprocessing.Process(
                target=self._run_worker,
                args=(worker_factory,),
            )

            processes.append(process)
            process.start()

        logger.info(
            f"Started {len(processes)} worker processes"
        )

        try:
            for process in processes:
                process.join()

        except KeyboardInterrupt:
            logger.info("Stopping worker processes")

            for process in processes:
                process.terminate()

            for process in processes:
                process.join()

    @staticmethod
    def _run_worker(
        worker_factory: Callable[[], Worker],
    ) -> None:
        worker = worker_factory()
        worker.run()