"""
02_preprocess.py
Assigns Koppen-Geiger climate zones to each sample (raster if available,
country/continent fallback otherwise), filters sparse ARGs, and saves
per-zone tables.

Raster (optional, more accurate):
    Download Beck 2018 from: https://figshare.com/articles/dataset/21789074
    Save as: data/raw/koppen_geiger_tif/1991_2020/koppen_geiger_0p1.tif
"""

import pandas as pd
import numpy as np
import os

PROCESSED_DIR  = "data/processed/"
RAW_DIR        = "data/raw/"
IN_FILE        = os.path.join(PROCESSED_DIR, "arg_wide_with_meta.csv")
KOPPEN_RASTER  = os.path.join(RAW_DIR, "koppen_geiger_tif", "1991_2020", "koppen_geiger_0p1.tif")

META_COLS = ["run_accession", "lat", "lon", "continent", "country",
             "koppen_code", "climate_zone"]

MIN_PRESENCE_FRAC = 0.05

os.makedirs(PROCESSED_DIR, exist_ok=True)


def assign_zone_from_raster(df: pd.DataFrame) -> pd.DataFrame:
    """Use the Beck 2018 GeoTIFF for precise per-coordinate zone assignment."""
    import rasterio

    def code_to_letter(value):
        if value is None or value == 0:
            return None
        if 1  <= value <= 3:  return "A"
        if 4  <= value <= 7:  return "B"
        if 8  <= value <= 16: return "C"
        if 17 <= value <= 28: return "D"
        if 29 <= value <= 30: return "E"
        return None

    def letter_to_zone(letter):
        return {"A": "tropical", "B": "arid",
                "C": "temperate", "D": "temperate"}.get(letter, None)

    print("  Using Koppen-Geiger raster for zone assignment...")
    with rasterio.open(KOPPEN_RASTER) as src:
        def query(lat, lon):
            if pd.isna(lat) or pd.isna(lon):
                return None, None
            try:
                row, col = src.index(lon, lat)
                value = int(src.read(1)[row, col])
                letter = code_to_letter(value)
                return value, letter
            except Exception:
                return None, None

        results = df.apply(lambda r: query(r["lat"], r["lon"]), axis=1)

    df["koppen_code"] = results.apply(lambda x: x[0])
    df["kg_letter"]   = results.apply(lambda x: x[1])
    df["climate_zone"] = df["kg_letter"].apply(letter_to_zone)
    return df


# Country/continent fallback when no raster is available
COUNTRY_ZONE = {
    "Brazil": "tropical", "Colombia": "tropical", "Peru": "tropical",
    "Venezuela": "tropical", "Ecuador": "tropical", "Bolivia": "tropical",
    "Indonesia": "tropical", "Malaysia": "tropical", "Thailand": "tropical",
    "Philippines": "tropical", "Vietnam": "tropical", "Cambodia": "tropical",
    "Laos": "tropical", "Myanmar": "tropical", "Papua New Guinea": "tropical",
    "India": "tropical", "Bangladesh": "tropical", "Sri Lanka": "tropical",
    "Nigeria": "tropical", "Ghana": "tropical", "Cameroon": "tropical",
    "Democratic Republic of the Congo": "tropical", "Uganda": "tropical",
    "Kenya": "tropical", "Tanzania": "tropical", "Ethiopia": "tropical",
    "Madagascar": "tropical", "Panama": "tropical", "Costa Rica": "tropical",
    "Guatemala": "tropical", "Honduras": "tropical", "Nicaragua": "tropical",
    "Singapore": "tropical",
    "Australia": "arid", "Namibia": "arid", "Botswana": "arid",
    "Saudi Arabia": "arid", "Iran": "arid", "Iraq": "arid",
    "Egypt": "arid", "Libya": "arid", "Algeria": "arid",
    "Morocco": "arid", "Sudan": "arid", "Mongolia": "arid",
    "Chile": "arid", "Argentina": "arid", "Pakistan": "arid",
    "Afghanistan": "arid", "Kazakhstan": "arid", "Uzbekistan": "arid",
    "United States": "temperate", "Canada": "temperate",
    "United Kingdom": "temperate", "Germany": "temperate",
    "France": "temperate", "Spain": "temperate", "Italy": "temperate",
    "Netherlands": "temperate", "Sweden": "temperate", "Norway": "temperate",
    "Denmark": "temperate", "Finland": "temperate", "Switzerland": "temperate",
    "Austria": "temperate", "Belgium": "temperate", "Poland": "temperate",
    "Czech Republic": "temperate", "Hungary": "temperate",
    "Romania": "temperate", "Ukraine": "temperate", "Russia": "temperate",
    "Japan": "temperate", "South Korea": "temperate", "China": "temperate",
    "New Zealand": "temperate", "South Africa": "temperate",
    "Turkey": "temperate", "Greece": "temperate", "Portugal": "temperate",
    "Mexico": "temperate",
}

CONTINENT_ZONE = {
    "Africa":        "tropical",
    "South America": "tropical",
    "Asia":          "temperate",
    "Europe":        "temperate",
    "North America": "temperate",
    "Oceania":       "arid",
}


def assign_zone_fallback(df: pd.DataFrame) -> pd.DataFrame:
    """Country lookup first, then continent fallback. Less precise than raster."""
    print("  No raster found — using country/continent fallback zones.")

    def zone_for_row(row):
        if isinstance(row["country"], str) and row["country"] in COUNTRY_ZONE:
            return COUNTRY_ZONE[row["country"]]
        if isinstance(row["continent"], str) and row["continent"] in CONTINENT_ZONE:
            return CONTINENT_ZONE[row["continent"]]
        return None

    df["koppen_code"]  = None
    df["climate_zone"] = df.apply(zone_for_row, axis=1)
    return df


if __name__ == "__main__":
    print(f"Loading {IN_FILE}...")
    df = pd.read_csv(IN_FILE, low_memory=False)
    print(f"  Shape: {df.shape[0]:,} samples x {df.shape[1]:,} columns")

    existing_meta = [c for c in META_COLS if c in df.columns]
    arg_cols = [c for c in df.columns if c not in existing_meta]
    print(f"  ARG columns: {len(arg_cols):,}")

    print("\nAssigning climate zones...")
    if os.path.exists(KOPPEN_RASTER):
        df = assign_zone_from_raster(df)
    else:
        df = assign_zone_fallback(df)

    print("\nSamples per zone:")
    print(df["climate_zone"].value_counts().to_string())

    df = df.dropna(subset=["climate_zone"])
    print(f"\nSamples retained after zone assignment: {len(df):,}")

    print(f"\nFiltering ARGs present in <{MIN_PRESENCE_FRAC*100:.0f}% of samples...")
    presence = (df[arg_cols] > 0).sum() / len(df)
    arg_cols_kept = presence[presence >= MIN_PRESENCE_FRAC].index.tolist()
    print(f"  ARGs before: {len(arg_cols):,}  →  after: {len(arg_cols_kept):,}")

    print("\nSaving per-zone tables...")
    for zone in ["tropical", "arid", "temperate"]:
        subset = df[df["climate_zone"] == zone][arg_cols_kept].copy()
        out_path = os.path.join(PROCESSED_DIR, f"args_{zone}.csv")
        subset.to_csv(out_path, index=False)
        print(f"  {zone:10s}: {len(subset):>5} samples, {len(arg_cols_kept):>4} ARGs -> {out_path}")

    full_out = os.path.join(PROCESSED_DIR, "args_all_zones.csv")
    df[["run_accession", "lat", "lon", "continent", "country", "climate_zone"] + arg_cols_kept].to_csv(
        full_out, index=False
    )
    print(f"\nFull labeled table saved to: {full_out}")
    print("\nNext: run 03_build_network.py")
