import os
from pathlib import Path

from dotenv import load_dotenv


# Load values from a local .env file, if one exists
load_dotenv()


# Find the main project folder
BASE_DIR = Path(__file__).resolve().parent.parent


# Read file paths from environment variables
RAW_DATA_PATH = BASE_DIR / os.getenv(
    "RAW_DATA_PATH",
    "data/raw/orders.csv",
)

PROCESSED_DATA_PATH = BASE_DIR / os.getenv(
    "PROCESSED_DATA_PATH",
    "data/processed/cleaned_orders.csv",
)

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
