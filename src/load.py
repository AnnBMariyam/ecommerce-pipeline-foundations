from pathlib import Path

import pandas as pd


def save_orders(
    orders_df: pd.DataFrame,
    output_path: str | Path,
) -> None:
    """Save processed order data to a CSV file."""

    path = Path(output_path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    orders_df.to_csv(
        path,
        index=False,
    )