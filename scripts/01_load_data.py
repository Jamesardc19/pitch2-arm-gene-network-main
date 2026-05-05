"""
01_load_data.py
---------------
Processes the mARG dataset (Martiny et al., Zenodo 6919377) from its native
long format into a wide ARG abundance table ready for co-occurrence analysis.

Steps:
1. Load metadata.tsv and parse lat/lon from the 'location' column
2. Load ARG.tsv (long format: one row per sample-ARG pair)
3. Compute RPKM-normalised abundance per sample
4. Pivot to wide format: rows = samples, columns = ARGs
5. Merge with metadata (lat/lon, continent)
6. Save to data/processed/arg_wide_with_meta.csv

Runtime note: ARG.tsv is 445 MB (~17 million rows). Loading takes ~3-5 min.
"""

import pandas as pd
import numpy as np
import re
import os

# ── Configuration ────────────────────────────────────────────────────────────
RAW_DIR        = "data/raw/"
PROCESSED_DIR  = "data/processed/"
ARG_FILE       = os.path.join(RAW_DIR, "ARG.tsv")
META_FILE      = os.path.join(RAW_DIR, "metadata.tsv")
OUT_FILE       = os.path.join(PROCESSED_DIR, "arg_wide_with_meta.csv")

# Minimum number of samples an ARG must appear in (presence filter applied later)
MIN_SAMPLE_PRESENCE_FRAC = 0.05   # keep ARGs present in ≥5% of samples

os.makedirs(PROCESSED_DIR, exist_ok=True)


# ── Step 1: Load and parse metadata ──────────────────────────────────────────

def parse_location(loc_str: str):
    """
    Parse strings like '18.05 S 47.03 E' or '38.15 N 141.00 E'
    into (lat, lon) as signed decimals.
    Returns (None, None) if parsing fails.
    """
    if not isinstance(loc_str, str):
        return None, None

    pattern = r"([\d.]+)\s*([NS])\s+([\d.]+)\s*([EW])"
    m = re.search(pattern, loc_str.strip(), re.IGNORECASE)
    if not m:
        return None, None

    lat = float(m.group(1)) * (-1 if m.group(2).upper() == "S" else 1)
    lon = float(m.group(3)) * (-1 if m.group(4).upper() == "W" else 1)
    return lat, lon


print("Loading metadata...")
meta = pd.read_csv(META_FILE, sep="\t", low_memory=False)
print(f"  Metadata rows: {len(meta):,}")

# Parse coordinates
coords = meta["location"].apply(parse_location)
meta["lat"] = coords.apply(lambda x: x[0])
meta["lon"] = coords.apply(lambda x: x[1])

coords_available = meta["lat"].notna().sum()
print(f"  Samples with parsed lat/lon: {coords_available:,}")
print(f"  Samples with continent:      {meta['continent'].notna().sum():,}")

# Keep only columns we need
meta_slim = meta[["run_accession", "lat", "lon", "continent", "country"]].copy()


# ── Step 2: Load ARG long table ───────────────────────────────────────────────

print("\nLoading ARG.tsv (this will take a few minutes)...")
arg = pd.read_csv(ARG_FILE, sep="\t", low_memory=False)
print(f"  ARG table rows: {len(arg):,}")
print(f"  Unique samples: {arg['run_accession'].nunique():,}")
print(f"  Unique ARGs:    {arg['refSequence'].nunique():,}")


# ── Step 3: Compute RPKM-normalised abundance ─────────────────────────────────
# RPKM = (fragmentCountAln * 1e6) / (refSequence_length/1000 * trimmed_fragments)
# This normalises for both gene length and sequencing depth.

print("\nComputing RPKM abundance...")
arg["rpkm"] = (
    (arg["fragmentCountAln"] * 1e6)
    / ((arg["refSequence_length"] / 1000) * arg["trimmed_fragments"])
).replace([np.inf, -np.inf], 0).fillna(0)


# ── Step 4: Pivot to wide format ──────────────────────────────────────────────
# For samples with duplicate runs (same run_accession x refSequence pair),
# sum the RPKM values.

print("Pivoting to wide format (samples × ARGs)...")
wide = arg.pivot_table(
    index="run_accession",
    columns="refSequence",
    values="rpkm",
    aggfunc="sum",
    fill_value=0
)
print(f"  Wide table shape: {wide.shape[0]:,} samples × {wide.shape[1]:,} ARGs")


# ── Step 5: Merge with metadata ───────────────────────────────────────────────

print("Merging with metadata...")
wide = wide.reset_index()
merged = wide.merge(meta_slim, on="run_accession", how="inner")

# Move metadata columns to front
meta_cols = ["run_accession", "lat", "lon", "continent", "country"]
arg_cols  = [c for c in merged.columns if c not in meta_cols]
merged    = merged[meta_cols + arg_cols]

print(f"  After merge: {len(merged):,} samples")
print(f"  Samples with lat/lon: {merged['lat'].notna().sum():,}")
print(f"  Samples with continent: {merged['continent'].notna().sum():,}")

# Show continent distribution
print("\nContinent distribution:")
print(merged["continent"].value_counts().to_string())


# ── Step 6: Save ──────────────────────────────────────────────────────────────

print(f"\nSaving to {OUT_FILE}...")
merged.to_csv(OUT_FILE, index=False)
print(f"Done. File size: {os.path.getsize(OUT_FILE) / 1e6:.1f} MB")
print("\nNext step: run 02_preprocess.py to assign climate zones and filter ARGs.")
