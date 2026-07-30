import json
import logging
from pathlib import Path
from typing import Any

import pandas as pd


logger = logging.getLogger(__name__)


class DataValidationError(Exception):
    """Raised when raw product data does not match the expected structure."""


def load_raw_payload(
    raw_file_path: str | Path,
) -> dict[str, Any]:
    """Load a raw extraction JSON file."""

    path = Path(raw_file_path)

    if not path.is_file():
        raise DataValidationError(
            f"Raw data file does not exist: '{path}'"
        )

    try:
        with path.open(mode="r", encoding="utf-8") as input_file:
            payload = json.load(input_file)

    except json.JSONDecodeError as error:
        raise DataValidationError(
            f"Raw data file contains invalid JSON: '{path}'"
        ) from error

    except OSError as error:
        raise DataValidationError(
            f"Could not read raw data file '{path}': {error}"
        ) from error

    if not isinstance(payload, dict):
        raise DataValidationError(
            "The raw JSON must contain one outer object."
        )

    return payload


def validate_raw_payload(
    payload: dict[str, Any],
) -> tuple[list[dict[str, Any]], str]:
    """Validate the outer payload and individual product structures."""

    products = payload.get("products")
    declared_count = payload.get("record_count")
    extracted_at = payload.get("extracted_at_utc")

    if not isinstance(products, list):
        raise DataValidationError(
            "The raw payload must contain a 'products' list."
        )

    if not products:
        raise DataValidationError(
            "The raw payload contains no products."
        )

    if not isinstance(declared_count, int):
        raise DataValidationError(
            "The raw payload must contain an integer 'record_count'."
        )

    if declared_count != len(products):
        raise DataValidationError(
            "The declared record count does not match the number "
            f"of products: declared={declared_count}, "
            f"actual={len(products)}."
        )

    if not isinstance(extracted_at, str) or not extracted_at.strip():
        raise DataValidationError(
            "The raw payload must contain 'extracted_at_utc'."
        )

    for product_index, product in enumerate(products):
        if not isinstance(product, dict):
            raise DataValidationError(
                f"Product at index {product_index} must be an object."
            )

        for field_name in ("dimensions", "meta"):
            field_value = product.get(field_name)

            if field_value is not None and not isinstance(
                field_value,
                dict,
            ):
                raise DataValidationError(
                    f"Product at index {product_index} has an invalid "
                    f"'{field_name}' field. It must be an object."
                )

        for field_name in ("reviews", "tags", "images"):
            field_value = product.get(field_name)

            if field_value is not None and not isinstance(
                field_value,
                list,
            ):
                raise DataValidationError(
                    f"Product at index {product_index} has an invalid "
                    f"'{field_name}' field. It must be a list."
                )

    return products, extracted_at.strip()


def calculate_average_review_rating(
    reviews: list[Any],
    product_index: int,
) -> float | None:
    """Calculate an average from valid review-rating values."""

    ratings: list[float] = []

    for review_index, review in enumerate(reviews):
        if not isinstance(review, dict):
            raise DataValidationError(
                f"Review {review_index} for product {product_index} "
                "must be an object."
            )

        raw_rating = review.get("rating")

        if raw_rating is None:
            continue

        try:
            rating = float(raw_rating)
        except (TypeError, ValueError) as error:
            raise DataValidationError(
                f"Review {review_index} for product {product_index} "
                "contains a non-numeric rating."
            ) from error

        ratings.append(rating)

    if not ratings:
        return None

    return sum(ratings) / len(ratings)


def build_review_and_array_metrics(
    products: list[dict[str, Any]],
) -> dict[str, list[int | float | None]]:
    """Create scalar metrics from nested product arrays."""

    review_counts: list[int] = []
    average_review_ratings: list[float | None] = []
    tag_counts: list[int] = []
    image_counts: list[int] = []

    for product_index, product in enumerate(products):
        reviews = product.get("reviews") or []
        tags = product.get("tags") or []
        images = product.get("images") or []

        review_counts.append(len(reviews))
        average_review_ratings.append(
            calculate_average_review_rating(
                reviews,
                product_index,
            )
        )
        tag_counts.append(len(tags))
        image_counts.append(len(images))

    return {
        "review_count": review_counts,
        "average_review_rating": average_review_ratings,
        "tag_count": tag_counts,
        "image_count": image_counts,
    }


def convert_column_types(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Convert columns into consistent nullable pandas data types."""

    dataframe = dataframe.copy()

    text_columns = [
        "title",
        "description",
        "category",
        "brand",
        "sku",
        "warranty_information",
        "shipping_information",
        "availability_status",
        "return_policy",
        "thumbnail",
    ]

    integer_columns = [
        "source_product_id",
        "stock",
        "minimum_order_quantity",
        "review_count",
        "tag_count",
        "image_count",
    ]

    decimal_columns = [
        "price",
        "discount_percentage",
        "rating",
        "weight",
        "width",
        "height",
        "depth",
        "average_review_rating",
    ]

    datetime_columns = [
        "source_created_at",
        "source_updated_at",
        "source_extracted_at",
    ]

    for column in text_columns:
        dataframe[column] = (
            dataframe[column]
            .astype("string")
            .str.strip()
            .replace("", pd.NA)
        )

    for column in integer_columns:
        numeric_values = pd.to_numeric(
            dataframe[column],
            errors="coerce",
        )

        fractional_values = numeric_values.dropna().mod(1).ne(0)

        if fractional_values.any():
            raise DataValidationError(
                f"Column '{column}' contains a non-integer value."
            )

        dataframe[column] = numeric_values.astype("Int64")

    for column in decimal_columns:
        dataframe[column] = pd.to_numeric(
            dataframe[column],
            errors="coerce",
        ).astype("Float64")

    for column in datetime_columns:
        dataframe[column] = pd.to_datetime(
            dataframe[column],
            errors="coerce",
            utc=True,
        )

    return dataframe


def validate_transformed_data(
    dataframe: pd.DataFrame,
) -> None:
    """Validate required values after type conversion."""

    required_columns = [
        "source_product_id",
        "title",
        "category",
        "price",
        "source_extracted_at",
    ]

    for column in required_columns:
        missing_count = int(dataframe[column].isna().sum())

        if missing_count > 0:
            raise DataValidationError(
                f"Required column '{column}' contains "
                f"{missing_count} missing value(s)."
            )

    invalid_ids = dataframe["source_product_id"] <= 0

    if invalid_ids.any():
        raise DataValidationError(
            "Product IDs must be greater than zero."
        )

    negative_prices = dataframe["price"] < 0

    if negative_prices.any():
        raise DataValidationError(
            "Product prices cannot be negative."
        )

    duplicate_ids = dataframe.loc[
        dataframe["source_product_id"].duplicated(keep=False),
        "source_product_id",
    ].tolist()

    if duplicate_ids:
        raise DataValidationError(
            "Duplicate product IDs were found: "
            f"{sorted(set(duplicate_ids))}"
        )


def transform_products(
    raw_file_path: str | Path,
) -> pd.DataFrame:
    """Load, flatten, clean, type, and validate raw products."""

    logger.info(
        "Starting product transformation: path=%s",
        raw_file_path,
    )

    payload = load_raw_payload(raw_file_path)
    products, extracted_at = validate_raw_payload(payload)

    normalized = pd.json_normalize(
        products,
        sep="_",
    )

    source_to_clean_columns = {
        "id": "source_product_id",
        "title": "title",
        "description": "description",
        "category": "category",
        "brand": "brand",
        "sku": "sku",
        "price": "price",
        "discountPercentage": "discount_percentage",
        "rating": "rating",
        "stock": "stock",
        "weight": "weight",
        "dimensions_width": "width",
        "dimensions_height": "height",
        "dimensions_depth": "depth",
        "warrantyInformation": "warranty_information",
        "shippingInformation": "shipping_information",
        "availabilityStatus": "availability_status",
        "returnPolicy": "return_policy",
        "minimumOrderQuantity": "minimum_order_quantity",
        "thumbnail": "thumbnail",
        "meta_createdAt": "source_created_at",
        "meta_updatedAt": "source_updated_at",
    }

    dataframe = (
        normalized
        .reindex(columns=source_to_clean_columns.keys())
        .rename(columns=source_to_clean_columns)
    )

    metrics = build_review_and_array_metrics(products)

    for column_name, values in metrics.items():
        dataframe[column_name] = values

    dataframe["source_extracted_at"] = extracted_at

    dataframe = convert_column_types(dataframe)
    validate_transformed_data(dataframe)

    logger.info(
        "Completed product transformation: rows=%s columns=%s",
        len(dataframe),
        len(dataframe.columns),
    )

    return dataframe