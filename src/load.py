import logging
from typing import Any

import pandas as pd
import psycopg

from src.config import DATABASE_DSN


logger = logging.getLogger(__name__)


class LoadError(Exception):
    """Raised when transformed product data cannot be loaded."""


LOAD_COLUMNS = (
    "source_product_id",
    "title",
    "description",
    "category",
    "brand",
    "sku",
    "price",
    "discount_percentage",
    "rating",
    "stock",
    "weight",
    "width",
    "height",
    "depth",
    "warranty_information",
    "shipping_information",
    "availability_status",
    "return_policy",
    "minimum_order_quantity",
    "thumbnail",
    "source_created_at",
    "source_updated_at",
    "review_count",
    "average_review_rating",
    "tag_count",
    "image_count",
    "source_extracted_at",
)


CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS api_products (
    source_product_id BIGINT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    category TEXT NOT NULL,
    brand TEXT,
    sku TEXT,
    price NUMERIC(12, 2) NOT NULL CHECK (price >= 0),
    discount_percentage NUMERIC(7, 2),
    rating NUMERIC(4, 2),
    stock INTEGER,
    weight DOUBLE PRECISION,
    width DOUBLE PRECISION,
    height DOUBLE PRECISION,
    depth DOUBLE PRECISION,
    warranty_information TEXT,
    shipping_information TEXT,
    availability_status TEXT,
    return_policy TEXT,
    minimum_order_quantity INTEGER,
    thumbnail TEXT,
    source_created_at TIMESTAMPTZ,
    source_updated_at TIMESTAMPTZ,
    review_count INTEGER,
    average_review_rating NUMERIC(4, 2),
    tag_count INTEGER,
    image_count INTEGER,
    source_extracted_at TIMESTAMPTZ NOT NULL,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    database_updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


UPSERT_PRODUCTS_SQL = """
INSERT INTO api_products (
    source_product_id,
    title,
    description,
    category,
    brand,
    sku,
    price,
    discount_percentage,
    rating,
    stock,
    weight,
    width,
    height,
    depth,
    warranty_information,
    shipping_information,
    availability_status,
    return_policy,
    minimum_order_quantity,
    thumbnail,
    source_created_at,
    source_updated_at,
    review_count,
    average_review_rating,
    tag_count,
    image_count,
    source_extracted_at
)
VALUES (
    %(source_product_id)s,
    %(title)s,
    %(description)s,
    %(category)s,
    %(brand)s,
    %(sku)s,
    %(price)s,
    %(discount_percentage)s,
    %(rating)s,
    %(stock)s,
    %(weight)s,
    %(width)s,
    %(height)s,
    %(depth)s,
    %(warranty_information)s,
    %(shipping_information)s,
    %(availability_status)s,
    %(return_policy)s,
    %(minimum_order_quantity)s,
    %(thumbnail)s,
    %(source_created_at)s,
    %(source_updated_at)s,
    %(review_count)s,
    %(average_review_rating)s,
    %(tag_count)s,
    %(image_count)s,
    %(source_extracted_at)s
)
ON CONFLICT (source_product_id)
DO UPDATE SET
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    category = EXCLUDED.category,
    brand = EXCLUDED.brand,
    sku = EXCLUDED.sku,
    price = EXCLUDED.price,
    discount_percentage = EXCLUDED.discount_percentage,
    rating = EXCLUDED.rating,
    stock = EXCLUDED.stock,
    weight = EXCLUDED.weight,
    width = EXCLUDED.width,
    height = EXCLUDED.height,
    depth = EXCLUDED.depth,
    warranty_information = EXCLUDED.warranty_information,
    shipping_information = EXCLUDED.shipping_information,
    availability_status = EXCLUDED.availability_status,
    return_policy = EXCLUDED.return_policy,
    minimum_order_quantity = EXCLUDED.minimum_order_quantity,
    thumbnail = EXCLUDED.thumbnail,
    source_created_at = EXCLUDED.source_created_at,
    source_updated_at = EXCLUDED.source_updated_at,
    review_count = EXCLUDED.review_count,
    average_review_rating = EXCLUDED.average_review_rating,
    tag_count = EXCLUDED.tag_count,
    image_count = EXCLUDED.image_count,
    source_extracted_at = EXCLUDED.source_extracted_at,
    database_updated_at = CURRENT_TIMESTAMP;
"""


def convert_database_value(value: Any) -> Any:
    """Convert pandas and NumPy values into database-friendly values."""

    if pd.isna(value):
        return None

    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime()

    if hasattr(value, "item"):
        return value.item()

    return value


def prepare_product_records(
    dataframe: pd.DataFrame,
) -> list[dict[str, Any]]:
    """Convert a validated DataFrame into PostgreSQL-ready records."""

    if not isinstance(dataframe, pd.DataFrame):
        raise LoadError(
            "The load stage requires a pandas DataFrame."
        )

    if dataframe.empty:
        raise LoadError(
            "The transformed DataFrame contains no products."
        )

    missing_columns = [
        column
        for column in LOAD_COLUMNS
        if column not in dataframe.columns
    ]

    if missing_columns:
        raise LoadError(
            "The transformed DataFrame is missing required columns: "
            f"{missing_columns}"
        )

    selected_data = dataframe.loc[:, LOAD_COLUMNS]
    raw_records = selected_data.to_dict(orient="records")

    prepared_records: list[dict[str, Any]] = []

    for raw_record in raw_records:
        prepared_record = {
            column: convert_database_value(value)
            for column, value in raw_record.items()
        }

        prepared_records.append(prepared_record)

    return prepared_records


def load_products(dataframe: pd.DataFrame) -> int:
    """Create the product table and upsert transformed products."""

    logger.info(
        "Starting product load: dataframe_rows=%s",
        len(dataframe),
    )

    records = prepare_product_records(dataframe)

    try:
        with psycopg.connect(DATABASE_DSN) as connection:
            with connection.cursor() as cursor:
                cursor.execute(CREATE_TABLE_SQL)

                cursor.execute(
                    "SELECT COUNT(*) FROM api_products;"
                )
                before_count = cursor.fetchone()[0]

                cursor.executemany(
                    UPSERT_PRODUCTS_SQL,
                    records,
                )

                cursor.execute(
                    "SELECT COUNT(*) FROM api_products;"
                )
                after_count = cursor.fetchone()[0]

    except psycopg.Error as error:
        raise LoadError(
            f"PostgreSQL load failed: {error}"
        ) from error

    new_row_count = after_count - before_count

    logger.info(
        "Completed product load: attempted_rows=%s "
        "new_rows=%s table_total=%s",
        len(records),
        new_row_count,
        after_count,
    )

    return after_count