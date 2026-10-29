import pandas as pd


def display_value(value, suffix="", decimals=2):
    """
    Format a value for display, returning "N/A" for None/NaN values
    instead of showing "nan" or "None" in the UI.
    """
    if value is None or pd.isna(value):
        return "N/A"

    if isinstance(value, (int, float)):
        return f"{value:.{decimals}f}{suffix}"

    return str(value)
