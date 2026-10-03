from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional

import requests
from bs4 import BeautifulSoup

from config import BASE_HEADERS


class Scraper(ABC):
    """
    Generic scraper supporting both HTML pages and JSON APIs.

    A scraper can:
    - Fetch and parse an HTML page using BeautifulSoup.
    - Fetch JSON data from an API.
    - Apply one or more transformation functions to the fetched data.

    Subclasses only need to implement the extraction/transformation logic.
    """

    def __init__(
        self,
        url: str,
        method: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        timeout: int = 30,
        transforms: Optional[List[Callable[[Any], Any]]] = None,
    ):
        self.url = url
        self.method = method.upper()
        self.headers = headers or BASE_HEADERS
        self.params = params or {}
        self.timeout = timeout
        self.transforms = transforms or []

    def fetch(self) -> Any:
        """
        Fetch data from the configured URL.

        Returns:
            BeautifulSoup object for HTML responses or a Python object
            decoded from JSON responses.

        Raises:
            requests.HTTPError: If the HTTP request fails.
            ValueError: If an API response cannot be decoded as JSON.
        """
        response = requests.request(
            method=self.method,
            url=self.url,
            headers=self.headers,
            params=self.params,
            timeout=self.timeout,
        )

        response.raise_for_status()

        content_type = response.headers.get("Content-Type", "").lower()

        if "application/json" in content_type:
            return response.json()

        return BeautifulSoup(response.text, "html.parser")

    def transform(self, data: Any) -> Any:
        """
        Apply all configured transformations sequentially.

        Args:
            data: Data returned by fetch().

        Returns:
            Transformed data.
        """
        for transform_fn in self.transforms:
            data = transform_fn(data)

        return data

    def scrape(self) -> Any:
        """
        Fetch and transform the remote data.

        Returns:
            Final transformed scraping result.
        """
        data = self.fetch()
        return self.transform(data)

    @abstractmethod
    def extract(self, data: Any) -> Any:
        """
        Extract the desired data from the fetched response.

        Implement this method when the scraper requires custom extraction
        logic before transformation.

        Args:
            data: BeautifulSoup object or decoded JSON data.

        Returns:
            Extracted data.
        """
        pass

    def run(self) -> Any:
        """
        Execute the complete scraping pipeline.

        The pipeline is:

            fetch → extract → transform → result

        Returns:
            Final scraping result.
        """
        data = self.fetch()
        data = self.extract(data)
        return self.transform(data)