# E-commerce API to PostgreSQL ETL Pipeline

A production-style Python ETL pipeline that extracts paginated product data
from the DummyJSON REST API, validates and transforms nested JSON, and loads
the results into PostgreSQL using idempotent upserts.

The project includes automated testing, structured logging, environment-based
configuration, Docker containerization, Docker Compose orchestration, and
GitHub Actions CI.

## Tech Stack

- Python
- pandas
- Requests
- PostgreSQL
- Psycopg
- pytest
- Docker
- Docker Compose
- GitHub Actions

## Run with Docker

The recommended way to run this project is with Docker Compose.

You do not need Python or PostgreSQL installed locally. Docker runs both the
Python ETL pipeline and PostgreSQL in containers.

### Prerequisites

- Git
- Docker Desktop with Docker Compose

### 1. Clone the repository

```bash
git clone https://github.com/AnnBMariyam/ecommerce-pipeline-foundations.git
cd ecommerce-pipeline-foundations