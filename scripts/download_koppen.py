"""
download_koppen.py
------------------
Helper script to download the Beck et al. (2023) Koppen-Geiger GeoTIFF
from Figshare (dataset 21789074) and extract the file needed for this project.

Usage:
    python scripts/download_koppen.py

What it does:
    1. Downloads koppen_geiger_tif.zip (~125 MB) from Figshare
    2. Extracts only the 1991-2020, 0.1° resolution GeoTIFF
    3. Saves it to: data/raw/koppen_geiger_1991_2020_0p1.tif

Figshare dataset: https://figshare.com/articles/dataset/21789074
Citation: Beck, H.E. et al. (2023). High-resolution (1 km) Koppen-Geiger
          maps for 1901-2099. Scientific Data.
"""

import os
import sys
import zipfile
from pathlib import Path

try:
    import requests
except ImportError:
    print("Installing 'requests'...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "-q"])
    import requests

# ── Configuration ─────────────────────────────────────────────────────────────
RAW_DIR    = Path("data/raw")
ZIP_PATH   = RAW_DIR / "koppen_geiger_tif.zip"
TARGET_TIF = RAW_DIR / "koppen_geiger_1991_2020_0p1.tif"

# The file inside the zip we want (0.1° resolution, 1991-2020)
PERIOD     = "1991_2020"
RESOLUTION = "0p1"

# Direct download URL from Figshare (koppen_geiger_tif.zip, file ID 61012822)
# Retrieved from: https://api.figshare.com/v2/articles/21789074/files
FIGSHARE_URL = "https://ndownloader.figshare.com/files/61012822"

os.makedirs(RAW_DIR, exist_ok=True)


def download_zip():
    print(f"Downloading koppen_geiger_tif.zip (~125 MB)...")
    print(f"Source: {FIGSHARE_URL}")

    with requests.get(FIGSHARE_URL, stream=True, timeout=120) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        downloaded = 0
        chunk_size = 1 << 16  # 64 KB chunks

        with open(ZIP_PATH, "wb") as f:
            for chunk in r.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total > 0:
                        pct = min(int(downloaded * 100 / total), 100)
                        bar = "#" * (pct // 2) + "-" * (50 - pct // 2)
                        sys.stdout.write(
                            f"\r  [{bar}] {pct}% ({downloaded/1e6:.1f}/{total/1e6:.1f} MB)"
                        )
                    else:
                        sys.stdout.write(f"\r  Downloaded {downloaded/1e6:.1f} MB...")
                    sys.stdout.flush()

    print()  # newline after progress
    size_mb = ZIP_PATH.stat().st_size / 1e6
    print(f"Downloaded: {ZIP_PATH} ({size_mb:.1f} MB)")


def extract_tif():
    print(f"\nExtracting target TIF from zip...")
    with zipfile.ZipFile(ZIP_PATH, "r") as z:
        all_files = z.namelist()
        print(f"  Files in archive: {len(all_files)}")

        # Find the tif matching our period and resolution
        candidates = [
            f for f in all_files
            if f.endswith(".tif")
            and PERIOD in f
            and RESOLUTION in f
        ]

        if not candidates:
            print("  [!] Could not find a matching TIF in the archive.")
            print(f"      Looking for: *{PERIOD}*{RESOLUTION}*.tif")
            print("  Available .tif files:")
            for f in all_files:
                if f.endswith(".tif"):
                    print(f"    {f}")
            sys.exit(1)

        chosen = candidates[0]
        print(f"  Extracting: {chosen}")
        data = z.read(chosen)

    TARGET_TIF.write_bytes(data)
    size_mb = TARGET_TIF.stat().st_size / 1e6
    print(f"  Saved: {TARGET_TIF} ({size_mb:.1f} MB)")


def main():
    if TARGET_TIF.exists():
        size_mb = TARGET_TIF.stat().st_size / 1e6
        print(f"✅ Koppen-Geiger raster already exists: {TARGET_TIF} ({size_mb:.1f} MB)")
        print("   Delete it and re-run this script to re-download.")
        return

    # Download if needed
    if not ZIP_PATH.exists():
        download_zip()
    else:
        print(f"  Zip already downloaded: {ZIP_PATH}")

    extract_tif()

    # Clean up zip to save space
    print(f"\nRemoving zip archive to free disk space...")
    ZIP_PATH.unlink()

    print(f"\n✅ Done! Koppen-Geiger raster ready at: {TARGET_TIF}")
    print("   You can now run: python scripts/run_all.py --from 2")


if __name__ == "__main__":
    main()
