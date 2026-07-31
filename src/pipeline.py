import logging
import sys

from src.config import LOG_FILE, LOG_LEVEL
from src.extract import extract_products
from src.load import load_products
from src.transform import transform_products


logger = logging.getLogger(__name__)


def configure_logging() -> None:
    """Configure logging to both the terminal and a log file."""

    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    numeric_log_level = getattr(logging, LOG_LEVEL, None)

    if not isinstance(numeric_log_level, int):
        raise ValueError(
            f"Invalid LOG_LEVEL configuration: '{LOG_LEVEL}'"
        )

    log_format = (
        "%(asctime)s | %(levelname)s | "
        "%(name)s | %(message)s"
    )

    console_handler = logging.StreamHandler(sys.stdout)

    file_handler = logging.FileHandler(
        LOG_FILE,
        mode="a",
        encoding="utf-8",
    )

    logging.basicConfig(
        level=numeric_log_level,
        format=log_format,
        handlers=[
            console_handler,
            file_handler,
        ],
        force=True,
    )


def run_pipeline() -> int:
    """Run extract, transform, and load in sequence."""

    logger.info("Pipeline started.")

    raw_file_path = extract_products()

    logger.info(
        "Extraction stage completed: raw_file=%s",
        raw_file_path,
    )

    dataframe = transform_products(raw_file_path)

    logger.info(
        "Transformation stage completed: row_count=%s",
        len(dataframe),
    )

    database_total = load_products(dataframe)

    logger.info(
        "Load stage completed: database_total=%s",
        database_total,
    )

    return database_total


def main() -> int:
    """Run the pipeline and return a process exit code."""

    try:
        configure_logging()

    except Exception as error:
        print(
            f"Failed to configure logging: {error}",
            file=sys.stderr,
        )
        return 1

    try:
        database_total = run_pipeline()

    except Exception:
        logger.exception("Pipeline failed.")
        return 1

    logger.info(
        "Pipeline completed successfully: database_total=%s",
        database_total,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())