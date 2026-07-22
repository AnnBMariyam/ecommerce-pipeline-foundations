import pandas as pd


def clean_orders(orders_df: pd.DataFrame) -> pd.DataFrame:
    """Clean order records and calculate revenue."""

    required_columns = {
        "order_id",
        "quantity",
        "unit_price",
    }

    missing_columns = required_columns - set(orders_df.columns)

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {sorted(missing_columns)}"
        )

    cleaned_df = orders_df.copy()

    cleaned_df = cleaned_df.drop_duplicates()

    cleaned_df = cleaned_df.dropna(subset=["order_id"])

    cleaned_df = cleaned_df[cleaned_df["quantity"] > 0]

    cleaned_df = cleaned_df[cleaned_df["unit_price"] >= 0]

    cleaned_df["revenue"] = (
        cleaned_df["quantity"] * cleaned_df["unit_price"]
    )

    return cleaned_df