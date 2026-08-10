import os
from pathlib import Path

from dotenv import load_dotenv


class ConfigurationError(Exception):
    """Raised when required project configuration is missing or invalid."""


# The main ecommerce-pipeline-foundations folder
BASE_DIR = Path(__file__).resolve().parent.parent

# Load variables from the .env file in the project root
load_dotenv(BASE_DIR / ".env")


def get_required_setting(name: str) -> str:
    """Return a required environment setting or raise a clear error."""

    value = os.getenv(name)

    if value is None or not value.strip():
        raise ConfigurationError(
            f"Required configuration setting '{name}' is missing."
        )

    return value.strip()


def get_positive_integer_setting(name: str) -> int:
    """Read a required setting and validate that it is a positive integer."""

    raw_value = get_required_setting(name)

    try:
        value = int(raw_value)
    except ValueError as error:
        raise ConfigurationError(
            f"Configuration setting '{name}' must be an integer."
        ) from error

    if value <= 0:
        raise ConfigurationError(
            f"Configuration setting '{name}' must be greater than zero."
        )

    return value




def get_database_dsn() -> str:
    """Return the database DSN and reject obvious placeholder values."""

    dsn = get_required_setting("DATABASE_DSN")

    placeholder_markers = (
        "CHANGE_ME",
        "REPLACE_ME",
        "YOUR_PASSWORD",
        "PASSWORD_HERE",
    )

    normalized_dsn = dsn.upper()

    for marker in placeholder_markers:
        if marker in normalized_dsn:
            raise ConfigurationError(
                "DATABASE_DSN appears to contain a placeholder "
                "password. Replace it with a real credential."
            )

    return dsn



# API settings
PRODUCTS_API_URL = get_required_setting("PRODUCTS_API_URL")
API_PAGE_SIZE = get_positive_integer_setting("API_PAGE_SIZE")
API_TIMEOUT_SECONDS = get_positive_integer_setting(
    "API_TIMEOUT_SECONDS"
)

# File and logging settings
RAW_DATA_DIR = BASE_DIR / get_required_setting("RAW_DATA_DIR")
LOG_FILE = BASE_DIR / get_required_setting("LOG_FILE")
LOG_LEVEL = get_required_setting("LOG_LEVEL").upper()

# PostgreSQL settings
DATABASE_DSN = get_database_dsn()