# RabbitMQ Scraping Pipeline

A reusable Python template for building scalable hierarchical web scrapers using **RabbitMQ**, producers, workers, and nested task queues.

The template is designed for scraping websites where data is structured hierarchically, for example:

```text
League
 └── Team
      └── Player
           └── Statistics
```

Each level can be handled independently by a worker, allowing the scraping pipeline to scale horizontally.

## Features

* RabbitMQ-based task queues
* Producer/worker architecture
* HTML scraping with BeautifulSoup
* JSON API scraping
* Configurable data transformations
* Concurrent workers
* Built-in logging
* Queue management utilities
* Simple local scraper testing
* No database required by the template

## Architecture

The general pipeline looks like this:

```text
                 ┌─────────────┐
                 │   Producer  │
                 └──────┬──────┘
                        │
                        ▼
                 ┌─────────────┐
                 │  RabbitMQ   │
                 │    Queue    │
                 └──────┬──────┘
                        │
                        ▼
                 ┌─────────────┐
                 │   Worker A  │
                 └──────┬──────┘
                        │
                        ▼
                 ┌─────────────┐
                 │  RabbitMQ   │
                 │    Queue    │
                 └──────┬──────┘
                        │
                        ▼
                 ┌─────────────┐
                 │   Worker B  │
                 └─────────────┘
```

For hierarchical scraping:

```text
Root
 │
 ├── Child A
 │    ├── Item A1
 │    ├── Item A2
 │    └── Item A3
 │
 └── Child B
      ├── Item B1
      └── Item B2
```

Each worker can consume one queue and publish the resulting tasks to another queue.

## Project Structure

```text
.
├── RabbitMQ/
│   └── helpers.py
│
├── produce/
│   └── ...
│
├── scrape/
│   ├── helpers.py
│   └── ...
│
├── workers/
│   ├── base.py
│   ├── manager.py
│   └── ...
│
├── config.py
├── logger.py
├── purge_queue.py
├── remove_queue.py
└── README.md
```

### `RabbitMQ/`

Contains the RabbitMQ connection, queue, consumer, and publisher utilities.

### `produce/`

Contains producers that populate the first-level queues.

### `scrape/`

Contains the website-specific scraping and transformation logic.

Scrapers can work with either:

* HTML pages using BeautifulSoup
* JSON APIs

### `workers/`

Contains the generic worker infrastructure and individual workers.

### `config.py`

Contains application configuration such as the RabbitMQ connection URL and queue names.

### `logger.py`

Provides console logging and optional persistent file logging.

---

# Installation

Clone the repository:

```bash
git clone <repository-url>
cd <repository-name>
```

Create a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

# Configuration

Create a `.env` file:

```env
CLOUDAMQP_URL=amqps://username:password@host/vhost
WRITE_LOGS=false
```

Your configuration module can then load the environment variables:

```python
import os

CLOUDAMQP_URL = os.getenv("CLOUDAMQP_URL")
WRITE_LOGS = os.getenv("WRITE_LOGS", "false").lower() == "true"
```

RabbitMQ can be hosted locally or through a managed provider such as CloudAMQP.

---

# Creating a Scraper

The generic scraper supports both HTML and JSON responses.

For an HTML page:

```python
from bs4 import BeautifulSoup
from scrape.base import Scraper


class ProductScraper(Scraper):

    def extract(self, data: BeautifulSoup):
        return [
            {
                "name": product.select_one(".name").get_text(strip=True),
                "url": product.select_one("a")["href"],
            }
            for product in data.select(".product")
        ]
```

For an API:

```python
from scrape.base import Scraper


class PlayerScraper(Scraper):

    def extract(self, data: dict):
        return [
            {
                "id": player["id"],
                "name": player["name"],
            }
            for player in data["players"]
        ]
```

The scraper automatically determines whether the response is HTML or JSON.

---

# Transforming Data

Transformations can be applied after extraction.

```python
def normalize_name(data):
    for item in data:
        item["name"] = item["name"].strip().lower()

    return data
```

Pass transformations to the scraper:

```python
scraper = ProductScraper(
    url="https://example.com/products",
    transforms=[
        normalize_name,
    ],
)
```

Multiple transformations can be chained:

```text
Fetch
  ↓
Extract
  ↓
Transform 1
  ↓
Transform 2
  ↓
Transform 3
  ↓
Result
```

---

# Testing a Scraper

Scrapers can be tested independently from RabbitMQ.

For example:

```bash
python3 -m scrape.products
```

This is useful when developing selectors or API transformations without starting any workers.

A scraper should ideally be tested independently before connecting it to the pipeline.

---

# Creating a Producer

A producer executes a scraper and publishes the resulting items to a RabbitMQ queue.

```python
from produce.base import Producer
from scrape.products import scrape_products


producer = Producer(
    name="products",
    queue="products",
    scraper_fn=scrape_products,
)

producer.run()
```

Run it with:

```bash
python3 -m produce.products
```

The flow is:

```text
Scraper
   ↓
Producer
   ↓
RabbitMQ Queue
```

---

# Creating a Worker

A worker consumes messages from a queue and processes them.

```python
from workers.base import Worker


def process_products(message):
    # Scrape/process the product
    return result


worker = Worker(
    name="products",
    queue="products",
    process_fn=process_products,
    output_queue="reviews",
)

worker.run()
```

The worker can optionally publish its result to another queue.

```text
products queue
      ↓
Products Worker
      ↓
reviews queue
```

---

# Nested Workers

The main purpose of this template is to support nested scraping.

For example:

```text
Categories
    ↓
Products
    ↓
Reviews
```

The workers can be configured as:

```python
Worker(
    name="categories",
    queue="categories",
    process_fn=process_categories,
    output_queue="products",
)

Worker(
    name="products",
    queue="products",
    process_fn=process_products,
    output_queue="reviews",
)

Worker(
    name="reviews",
    queue="reviews",
    process_fn=process_reviews,
)
```

This creates:

```text
categories
    │
    ▼
products
    │
    ▼
reviews
```

Each stage is independent and can have its own number of workers.

---

# Running Multiple Workers

The worker manager can run multiple workers concurrently.

```python
from workers.manager import WorkerManager
from workers.base import Worker


manager = WorkerManager([
    lambda: Worker(
        name="products",
        queue="products",
        process_fn=process_products,
        output_queue="reviews",
    ),

    lambda: Worker(
        name="reviews",
        queue="reviews",
        process_fn=process_reviews,
    ),
])


if __name__ == "__main__":
    manager.run()
```

This allows the pipeline to scale independently:

```text
              RabbitMQ
                  │
        ┌─────────┴─────────┐
        ▼                   ▼
 Product Worker         Review Worker
        │
        │
   Multiple processes
```

You can run multiple instances of the same worker when a particular scraping stage requires more throughput.

---

# Queue Management

### Purge a queue

Remove all messages while keeping the queue:

```bash
python3 purge_queue.py products
```

### Delete a queue

Delete the queue and all messages inside it:

```bash
python3 remove_queue.py products
```

Be careful when using `remove_queue.py`, as the queue itself will need to be declared again before it can be used.

---

# Logging

Console logging is enabled by default:

```text
12:43:21 | INFO     | scraper | Starting products producer
12:43:22 | INFO     | scraper | Found 120 products
12:43:23 | WARNING  | scraper | No reviews found
```

File logging is optional.

Set:

```env
WRITE_LOGS=true
```

Logs will then be written to:

```text
logs/
└── scraper.log
```

File logging uses rotation to prevent the log file from growing indefinitely.

---

# Recommended Workflow

When building a new scraper, develop each stage independently.

### 1. Implement the scraper

```text
scrape/
└── products.py
```

Test it:

```bash
python3 -m scrape.products
```

### 2. Create the producer

```text
produce/
└── products.py
```

Run it:

```bash
python3 -m produce.products
```

### 3. Verify the queue

Check that messages are being published correctly.

### 4. Create the worker

```text
workers/
└── products.py
```

Run it:

```bash
python3 -m workers.products
```

### 5. Add the next scraping stage

For example:

```text
Products Worker
      ↓
Reviews Queue
      ↓
Reviews Worker
```

### 6. Scale workers

Once the pipeline works correctly, run multiple instances of workers that require more processing capacity.

---

# Design Philosophy

This template intentionally separates:

```text
Scraping
   │
   ├── Fetching
   ├── Extraction
   └── Transformation

Messaging
   │
   ├── Queues
   ├── Producers
   └── Consumers

Processing
   │
   └── Workers
```

This makes the scraping logic independent from RabbitMQ and allows the same infrastructure to be reused for different websites and data hierarchies.

---

# Example Use Cases

The architecture can be adapted to many hierarchical scraping problems:

```text
E-commerce

Categories
    ↓
Products
    ↓
Reviews
```

```text
Football

Leagues
    ↓
Teams
    ↓
Players
    ↓
Statistics
```

```text
Travel

Countries
    ↓
Cities
    ↓
Hotels
    ↓
Reviews
```

```text
Education

Universities
    ↓
Departments
    ↓
Courses
    ↓
Students
```

---

# License

This project is licensed under the MIT License.

See [`LICENSE`](LICENSE) for details.
