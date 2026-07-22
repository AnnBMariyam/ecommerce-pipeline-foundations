from pathlib import Path

import pandas as pd


def read_orders(file_path: str | Path) -> pd.DataFrame:
    """Read order data from a CSV file."""

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Input file was not found: {path}")

    orders_df = pd.read_csv(path)

    return orders_df