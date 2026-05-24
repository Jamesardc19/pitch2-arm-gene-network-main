"""
01_load_data.py
Loads the mARG dataset (Zenodo 6919377) from long format into a wide
RPKM-normalised abundance table merged with sample metadata.

Note: ARG.tsv is ~445 MB (~17M rows). Expect 3-5 min to load.
"""

import pandas as pd
import numpy as np
import re
import os

RAW_DIR        = "data/raw/"
PROCESSED_DIR  = "data/processed/"
ARG_FILE       = os.path.join(RAW_DIR, "ARG.tsv")
META_FILE      = os.path.join(RAW_DIR, "metadata.tsv")
OUT_FILE       = os.path.join(PROCESSED_DIR, "arg_wide_with_meta.csv")

MIN_SAMPLE_PRESENCE_FRAC = 0.05

os.makedirs(PROCESSED_DIR, exist_ok=True)


def parse_location(loc_str: str):
    """Parse '18.05 S 47.03 E' into signed decimal (lat, lon)."""
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

coords = meta["location"].apply(parse_location)
meta["lat"] = coords.apply(lambda x: x[0])
meta["lon"] = coords.apply(lambda x: x[1])

print(f"  Samples with parsed lat/lon: {meta['lat'].notna().sum():,}")
print(f"  Samples with continent:      {meta['continent'].notna().sum():,}")

meta_slim = meta[["run_accession", "lat", "lon", "continent", "country"]].copy()


print("\nLoading ARG.tsv (this will take a few minutes)...")
arg = pd.read_csv(ARG_FILE, sep="\t", low_memory=False)
print(f"  ARG table rows: {len(arg):,}")
print(f"  Unique samples: {arg['run_accession'].nunique():,}")
print(f"  Unique ARGs:    {arg['refSequence'].nunique():,}")


# RPKM = (fragmentCountAln * 1e6) / (refLength_kb * trimmed_fragments)
print("\nComputing RPKM abundance...")
arg["rpkm"] = (
    (arg["fragmentCountAln"] * 1e6)
    / ((arg["refSequence_length"] / 1000) * arg["trimmed_fragments"])
).replace([np.inf, -np.inf], 0).fillna(0)


print("Pivoting to wide format (samples x ARGs)...")
wide = arg.pivot_table(
    index="run_accession",
    columns="refSequence",
    values="rpkm",
    aggfunc="sum",
    fill_value=0
)
print(f"  Wide table shape: {wide.shape[0]:,} samples x {wide.shape[1]:,} ARGs")


print("Merging with metadata...")
wide = wide.reset_index()
merged = wide.merge(meta_slim, on="run_accession", how="inner")

meta_cols = ["run_accession", "lat", "lon", "continent", "country"]
arg_cols  = [c for c in merged.columns if c not in meta_cols]
merged    = merged[meta_cols + arg_cols]

print(f"  After merge: {len(merged):,} samples")
print(f"  Samples with lat/lon: {merged['lat'].notna().sum():,}")
print("\nContinent distribution:")
print(merged["continent"].value_counts().to_string())


print(f"\nSaving to {OUT_FILE}...")
merged.to_csv(OUT_FILE, index=False)
print(f"Done. File size: {os.path.getsize(OUT_FILE) / 1e6:.1f} MB")
print("\nNext: run 02_preprocess.py")
