"""
01_load_data.py
---------------
Load the raw ARG abundance table and inspect its structure.

Expected input:
    data/raw/<your_dataset>.csv  (or .xlsx)
    - Rows: samples
    - Columns: ARG names + metadata columns (SampleID, Latitude, Longitude, etc.)

Output:
    Prints shape, column names, and a preview to confirm the table loaded correctly.
"""

import pandas as pd
import os

# ── Configuration ────────────────────────────────────────────────────────────
RAW_DATA_PATH = "data/raw/"   # Update filename after download


def load_arg_table(filepath: str) -> pd.DataFrame:
    """Load an ARG abundance table from CSV or Excel."""
    ext = os.path.splitext(filepath)[-1].lower()
    if ext in (".xlsx", ".xls"):
        df = pd.read_excel(filepath, index_col=0)
    elif ext == ".csv":
        df = pd.read_csv(filepath, index_col=0)
    else:
        raise ValueError(f"Unsupported file format: {ext}")
    return df


def inspect(df: pd.DataFrame) -> None:
    print(f"Shape: {df.shape}")
    print(f"\nColumns ({len(df.columns)}):\n{df.columns.tolist()}")
    print(f"\nFirst 5 rows:\n{df.head()}")
    print(f"\nMissing values per column:\n{df.isnull().sum()[df.isnull().sum() > 0]}")


if __name__ == "__main__":
    # List files in raw folder so you can confirm the filename
    files = os.listdir(RAW_DATA_PATH)
    print("Files in data/raw/:", files)

    if not files:
        print("\n[!] No files found in data/raw/. Download your dataset first.")
    else:
        # Change this to match your actual filename
        target = os.path.join(RAW_DATA_PATH, files[0])
        print(f"\nLoading: {target}")
        df = load_arg_table(target)
        inspect(df)
