import json
from pathlib import Path
from typing import Any

import pytest

from src.transform import (
    DataValidationError,
    transform_products,
)


def build_valid_payload() -> dict[str, Any]:
    """Return a small but valid raw product payload for testing."""

    return {
        "extracted_at_utc": "2026-07-30T12:00:00+00:00",
        "source_url": "https://example.com/products",
        "record_count": 1,
        "products": [
            {
                "id": 1,
                "title": "  Test Product  ",
                "description": "A product used in a test.",
                "category": "electronics",
                "brand": "Test Brand",
                "sku": "TEST-001",
                "price": "19.99",
                "discountPercentage": "5.5",
                "rating": "4.2",
                "stock": "10",
                "weight": "2.5",
                "dimensions": {
                    "width": "10.5",
                    "height": "5.0",
                    "depth": "2.0",
                },
                "reviews": [
                    {
                        "rating": 4,
                        "comment": "Good product",
                    },
                    {
                        "rating": 5,
                        "comment": "Excellent product",
                    },
                ],
                "tags": [
                    "electronics",
                    "test",
                ],
                "images": [
                    "https://example.com/product.jpg",
                ],
                "minimumOrderQuantity": 1,
                "meta": {
                    "createdAt": "2026-01-01T10:00:00Z",
                    "updatedAt": "2026-01-02T10:00:00Z",
                },
            }
        ],
    }


def write_payload(
    tmp_path: Path,
    payload: dict[str, Any],
) -> Path:
    """Write a test payload into a temporary JSON file."""

    raw_file_path = tmp_path / "products_test.json"

    raw_file_path.write_text(
        json.dumps(payload),
        encoding="utf-8",
    )

    return raw_file_path


def test_transform_products_returns_clean_dataframe(
    tmp_path: Path,
) -> None:
    """Valid raw data should become one clean product row."""

    # Arrange
    payload = build_valid_payload()
    raw_file_path = write_payload(tmp_path, payload)

    # Act
    dataframe = transform_products(raw_file_path)

    # Assert
    assert len(dataframe) == 1

    product = dataframe.iloc[0]

    assert int(product["source_product_id"]) == 1
    assert product["title"] == "Test Product"
    assert product["category"] == "electronics"
    assert float(product["price"]) == pytest.approx(19.99)
    assert float(product["width"]) == pytest.approx(10.5)
    assert int(product["review_count"]) == 2
    assert float(
        product["average_review_rating"]
    ) == pytest.approx(4.5)
    assert int(product["tag_count"]) == 2
    assert int(product["image_count"]) == 1


def test_transform_rejects_missing_products_list(
    tmp_path: Path,
) -> None:
    """A payload without a products list should be rejected."""

    # Arrange
    payload = build_valid_payload()
    del payload["products"]

    raw_file_path = write_payload(tmp_path, payload)

    # Act and assert
    with pytest.raises(
        DataValidationError,
        match="products.*list",
    ):
        transform_products(raw_file_path)


def test_transform_rejects_negative_price(
    tmp_path: Path,
) -> None:
    """A product with a negative price should be rejected."""

    # Arrange
    payload = build_valid_payload()
    payload["products"][0]["price"] = -10

    raw_file_path = write_payload(tmp_path, payload)

    # Act and assert
    with pytest.raises(
        DataValidationError,
        match="prices cannot be negative",
    ):
        transform_products(raw_file_path)