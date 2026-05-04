"""
02_preprocess.py
----------------
1. Load the ARG abundance table from data/raw/
2. Assign Koppen-Geiger climate zone to each sample using lat/lon
3. Simplify zones into three groups: Tropical (A), Arid (B), Temperate (C/D)
4. Save per-zone filtered tables to data/processed/

Requirements:
    pip install rasterio rasterstats

Koppen-Geiger raster:
    Download "Beck_KG_V1_present_0p0083.tif" from:
    https://figshare.com/articles/dataset/Present_and_future_K_ppen-Geiger_climate_classification_maps_at_1-km_resolution/6396959
    Save to: data/raw/koppen_geiger.tif
"""

import pandas as pd
import numpy as np
import rasterio
from rasterio.transform import rowcol
import os

# ── Configuration ────────────────────────────────────────────────────────────
RAW_DIR = "data/raw/"
PROCESSED_DIR = "data/processed/"
KOPPEN_RASTER = os.path.join(RAW_DIR, "koppen_geiger.tif")

# Update to your actual filename
ARG_TABLE_FILE = os.path.join(RAW_DIR, "arg_abundance.csv")

LAT_COL = "Latitude"
LON_COL = "Longitude"

ZONE_MAP = {
    "A": "Tropical",
    "B": "Arid",
    "C": "Temperate",
    "D": "Temperate",
}

os.makedirs(PROCESSED_DIR, exist_ok=True)


def get_koppen_code(lat: float, lon: float, src: rasterio.DatasetReader) -> str:
    """Query raster to get the Koppen-Geiger zone code integer, map to letter."""
    # Beck 2018 encodes zones as integers (1=Af, 2=Am, 3=As, 4=Aw, 5=BWh, ...)
    row, col = rowcol(src.transform, lon, lat)
    try:
        value = src.read(1)[row, col]
    except IndexError:
        return "Unknown"

    # Integer → letter mapping (simplified — first letter only)
    zone_codes = {
        range(1, 5): "A",    # Tropical
        range(5, 9): "B",    # Arid
        range(9, 17): "C",   # Temperate (warm)
        range(17, 29): "D",  # Continental
        range(29, 31): "E",  # Polar
    }
    for code_range, letter in zone_codes.items():
        if value in code_range:
            return letter
    return "Unknown"


def assign_zones(df: pd.DataFrame) -> pd.DataFrame:
    """Add KG_code and Climate_Zone columns to the dataframe."""
    if not os.path.exists(KOPPEN_RASTER):
        raise FileNotFoundError(
            f"Koppen-Geiger raster not found at {KOPPEN_RASTER}.\n"
            "Download Beck 2018 raster from Figshare and save as data/raw/koppen_geiger.tif"
        )

    with rasterio.open(KOPPEN_RASTER) as src:
        df["KG_code"] = df.apply(
            lambda row: get_koppen_code(row[LAT_COL], row[LON_COL], src), axis=1
        )

    df["Climate_Zone"] = df["KG_code"].map(ZONE_MAP).fillna("Other")
    return df


def split_by_zone(df: pd.DataFrame) -> dict:
    """Return a dict of {zone_name: DataFrame} for each climate zone."""
    zones = {}
    for zone in ["Tropical", "Arid", "Temperate"]:
        subset = df[df["Climate_Zone"] == zone].copy()
        print(f"  {zone}: {len(subset)} samples")
        zones[zone] = subset
    return zones


if __name__ == "__main__":
    print("Loading ARG table...")
    df = pd.read_csv(ARG_TABLE_FILE, index_col=0)

    print("Assigning Koppen-Geiger zones...")
    df = assign_zones(df)

    print("\nSample counts by zone:")
    zones = split_by_zone(df)

    for zone_name, zone_df in zones.items():
        out_path = os.path.join(PROCESSED_DIR, f"args_{zone_name.lower()}.csv")
        zone_df.to_csv(out_path)
        print(f"  Saved: {out_path}")

    # Also save the full labeled table
    df.to_csv(os.path.join(PROCESSED_DIR, "args_all_zones.csv"))
    print("\nDone. Check data/processed/ for output files.")
