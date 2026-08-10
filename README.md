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

## Pipeline Architecture

```text
DummyJSON Products API
        |
        v
   Extract
   - REST API requests
   - offset pagination
   - timestamped raw JSON
        |
        v
   Transform
   - schema validation
   - nested JSON flattening
   - type conversion
   - derived review metrics
        |
        v
   Load
   - PostgreSQL
   - primary-key validation
   - ON CONFLICT upsert
        |
        v
   api_products
```

Docker Compose runs two services:

```text
pipeline container  --->  db container
Python ETL               PostgreSQL
```

The pipeline connects to the PostgreSQL container using the Compose service
hostname `db` rather than `localhost`.

## How the Pipeline Works

### 1. Extract

The extraction stage calls the DummyJSON Products API using offset-based
pagination with `limit` and `skip`.

Each API page is validated, logged, and combined into a complete product
dataset. The unmodified source data is then saved as a timestamped JSON file
in `data/raw/` for traceability.

### 2. Transform

The transformation stage loads the raw JSON and validates the expected
structure before processing it.

Nested product fields such as dimensions and metadata are flattened into
tabular columns. Reviews, tags, and images are summarized into useful metrics,
and pandas nullable data types are used to preserve missing values safely.

Invalid required fields raise a custom `DataValidationError` instead of
silently entering the database.

### 3. Load

The cleaned DataFrame is loaded into PostgreSQL using Psycopg.

Products are identified by their source product ID. PostgreSQL
`ON CONFLICT ... DO UPDATE` logic inserts new products and updates existing
ones, making pipeline reruns idempotent.

### 4. Orchestrate

A single command runs the stages in order:

```bash
python -m src.pipeline
```

The orchestrator logs each stage, returns exit code `0` on success, and returns
a non-zero exit code when the pipeline fails.

## Key Features

- Paginated REST API extraction using `limit` and `skip`
- Timestamped raw JSON preservation
- Structured logging to the terminal and `logs/pipeline.log`
- Custom extraction, validation, configuration, and load errors
- Nested JSON normalization with pandas
- Nullable and validated data types
- PostgreSQL upsert using `ON CONFLICT`
- Idempotent pipeline reruns without duplicate product IDs
- Environment-based configuration with `python-dotenv`
- Pytest coverage for transformation and configuration logic
- Dockerized Python application
- PostgreSQL and pipeline orchestration with Docker Compose
- Database health checking before pipeline startup
- Persistent PostgreSQL storage using a Docker volume
- GitHub Actions CI

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
```

### 2. Create the environment file

Copy the example configuration.

**Windows PowerShell**

```powershell
Copy-Item .env.example .env
```

**macOS/Linux**

```bash
cp .env.example .env
```

Open `.env` and replace the placeholder database credentials with your own
local development values.

Do not commit `.env` because it contains private configuration.

### 3. Run the complete pipeline

```bash
docker compose up --build
```

Docker Compose will:

1. Build the Python pipeline image.
2. Start PostgreSQL.
3. Wait for PostgreSQL to become healthy.
4. Run the API extraction.
5. Transform and validate the product data.
6. Load the data into PostgreSQL using an upsert.
7. Save pipeline logs and timestamped raw JSON files.

A successful run ends with a message similar to:

```text
Pipeline completed successfully: database_total=194
```

The product count may change if the source API dataset changes.

### 4. Verify the loaded data

In another terminal:

```bash
docker compose exec db psql -U pipeline_user -d ecommerce_analytics -c "SELECT COUNT(*) AS total_rows, COUNT(DISTINCT source_product_id) AS distinct_product_ids FROM api_products;"
```

The two counts should be equal, confirming that product IDs were not
duplicated.

### 5. Stop the services

Press `Ctrl+C` in the terminal running Docker Compose, then run:

```bash
docker compose down
```

This removes the containers and network but preserves the PostgreSQL volume.

To intentionally delete the database and start completely from scratch:

```bash
docker compose down --volumes
docker compose up --build
```

## Run Locally

Docker Compose is the recommended way to run the complete project, but the
pipeline can also be run directly with Python and a local PostgreSQL instance.

### Prerequisites

- Python 3.12
- PostgreSQL
- Git

### 1. Clone the repository

```bash
git clone https://github.com/AnnBMariyam/ecommerce-pipeline-foundations.git
cd ecommerce-pipeline-foundations
```

### 2. Create a virtual environment

**Windows PowerShell**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS/Linux**

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Configure environment variables

Copy the example configuration.

**Windows PowerShell**

```powershell
Copy-Item .env.example .env
```

**macOS/Linux**

```bash
cp .env.example .env
```

Update `DATABASE_DSN` in `.env` with the credentials for your local
PostgreSQL instance.

The application validates required configuration at startup and rejects
missing, invalid, or obvious placeholder values.

### 5. Create the database

Create a PostgreSQL database named:

```text
ecommerce_analytics
```

Make sure the database name, username, password, host, and port in
`DATABASE_DSN` match your PostgreSQL installation.

The pipeline creates its `api_products` table automatically if the table does
not already exist.

### 6. Run the pipeline

```bash
python -m src.pipeline
```

A successful run returns exit code `0` and writes progress to both the terminal
and `logs/pipeline.log`.


## Testing

The project uses `pytest` for automated testing, with a focus on transformation
and configuration logic that can be tested independently from the API and
database.

Run the full test suite with:

```bash
python -m pytest -v
```

The current suite contains 15 test cases covering:

- successful raw JSON transformation
- nested field flattening
- derived review, tag, and image metrics
- missing product data
- invalid product structures
- negative price validation
- required environment variables
- positive integer configuration values
- invalid configuration values
- placeholder database credential rejection

## Continuous Integration

GitHub Actions automatically runs the pytest suite whenever code is pushed to
the repository.

The CI workflow is defined in:

```text
.github/workflows/ci.yml
```

The workflow performs the following steps:

```text
Push to GitHub
      |
      v
GitHub Actions starts
      |
      v
Ubuntu runner is created
      |
      v
Repository is checked out
      |
      v
Python 3.12 is installed
      |
      v
Dependencies are installed
      |
      v
pytest runs
      |
      v
Pass ✓ / Fail ✗
```

This provides an independent check that the tested parts of the project work
outside the local development environment.