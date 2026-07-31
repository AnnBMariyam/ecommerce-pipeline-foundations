import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

from src.config import (
    API_PAGE_SIZE,
    API_TIMEOUT_SECONDS,
    PRODUCTS_API_URL,
    RAW_DATA_DIR,
)


logger = logging.getLogger(__name__)


class ExtractionError(Exception):
    """Raised when product data cannot be extracted from the API."""


def fetch_product_page(skip: int) -> dict[str, Any]:
    """Fetch and validate one page of products from the API."""

    if skip < 0:
        raise ValueError("skip must be zero or greater.")

    params = {
        "limit": API_PAGE_SIZE,
        "skip": skip,
    }

    logger.info(
        "Requesting product page: url=%s limit=%s skip=%s",
        PRODUCTS_API_URL,
        API_PAGE_SIZE,
        skip,
    )

    try:
        response = requests.get(
            PRODUCTS_API_URL,
            params=params,
            timeout=API_TIMEOUT_SECONDS,
        )

        logger.info(
            "Received API response: url=%s status=%s",
            response.url,
            response.status_code,
        )

        response.raise_for_status()

    except requests.exceptions.RequestException as error:
        raise ExtractionError(
            f"Failed to retrieve product page at skip={skip}: {error}"
        ) from error

    try:
        payload = response.json()

    except requests.exceptions.JSONDecodeError as error:
        raise ExtractionError(
            f"The API returned invalid JSON for skip={skip}."
        ) from error

    if not isinstance(payload, dict):
        raise ExtractionError(
            "The API response must be a JSON object."
        )

    products = payload.get("products")

    if not isinstance(products, list):
        raise ExtractionError(
            "The API response must contain a 'products' list."
        )

    logger.info(
        "Fetched product page: skip=%s record_count=%s",
        skip,
        len(products),
    )

    return payload

def fetch_all_products() -> list[dict[str, Any]]:
    """Fetch every product by requesting one API page at a time."""

    all_products: list[dict[str, Any]] = []
    skip = 0
    expected_total: int | None = None

    while True:
        payload = fetch_product_page(skip)

        products = payload["products"]
        total = payload.get("total")

        if not isinstance(total, int) or total < 0:
            raise ExtractionError(
                "The API response must contain a valid non-negative 'total'."
            )

        if expected_total is None:
            expected_total = total

            logger.info(
                "Beginning paginated extraction: expected_total=%s",
                expected_total,
            )

        all_products.extend(products)

        logger.info(
            "Pagination progress: collected=%s expected_total=%s",
            len(all_products),
            expected_total,
        )

        if len(all_products) >= expected_total:
            break

        if not products:
            raise ExtractionError(
                "The API returned an empty page before all products "
                "were collected."
            )

        skip += len(products)

    logger.info(
        "Completed paginated extraction: record_count=%s",
        len(all_products),
    )

    return all_products


def save_raw_products(
    products: list[dict[str, Any]],
) -> Path:
    """Save extracted products to a timestamped raw JSON file."""

    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    extracted_at = datetime.now(timezone.utc)
    timestamp = extracted_at.strftime("%Y%m%dT%H%M%SZ")

    output_path = RAW_DATA_DIR / f"products_{timestamp}.json"

    raw_payload = {
        "extracted_at_utc": extracted_at.isoformat(),
        "source_url": PRODUCTS_API_URL,
        "record_count": len(products),
        "products": products,
    }

    try:
        with output_path.open(
            mode="w",
            encoding="utf-8",
        ) as output_file:
            json.dump(
                raw_payload,
                output_file,
                indent=2,
                ensure_ascii=False,
            )

    except OSError as error:
        raise ExtractionError(
            f"Failed to save raw product data to '{output_path}': "
            f"{error}"
        ) from error

    logger.info(
        "Saved raw product data: path=%s record_count=%s",
        output_path,
        len(products),
    )

    return output_path


def extract_products() -> Path:
    """Run the complete extraction process and return the raw file path."""

    logger.info("Starting product extraction.")

    products = fetch_all_products()
    output_path = save_raw_products(products)

    logger.info(
        "Product extraction finished successfully: path=%s",
        output_path,
    )

    return output_path