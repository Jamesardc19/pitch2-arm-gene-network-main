"""
run_all.py
----------
Master pipeline runner for the ARG Co-occurrence Network project.
Executes all steps in sequence:

  Step 1: 01_load_data.py        — parse ARG.tsv + metadata.tsv → wide table
  Step 2: 02_preprocess.py       — assign Koppen zones, filter sparse ARGs
  Step 3: 03_build_network.py    — Spearman co-occurrence → NetworkX .gexf
  Step 4: 04_community_detection.py  — Louvain + Girvan-Newman communities
  Step 5: 05_centrality_analysis.py  — degree / betweenness / clustering
  Step 6: 06_visualize.py            — network figures + centrality barplots

Usage:
    cd pitch2-arm-gene-network-main
    python scripts/run_all.py

Options:
    --from STEP   Start from step N (default: 1)
    --to   STEP   Stop after step N  (default: 6)
    --dry-run     Print what would run without executing

Example (skip step 1 if data already processed):
    python scripts/run_all.py --from 2
"""

import subprocess
import sys
import time
import argparse
from pathlib import Path

# ── Pipeline definition ───────────────────────────────────────────────────────
STEPS = [
    (1, "01_load_data.py",             "Parse ARG.tsv + metadata -> wide table"),
    (2, "02_preprocess.py",            "Assign Koppen zones, filter sparse ARGs"),
    (3, "03_build_network.py",         "Build co-occurrence networks (.gexf)"),
    (4, "04_community_detection.py",   "Louvain + Girvan-Newman communities"),
    (5, "05_centrality_analysis.py",   "Degree / betweenness / clustering metrics"),
    (6, "06_visualize.py",             "Network figures + centrality bar charts"),
]

SCRIPTS_DIR = Path(__file__).parent
ROOT_DIR    = SCRIPTS_DIR.parent


def fmt_seconds(s: float) -> str:
    if s < 60:
        return f"{s:.1f}s"
    m = int(s // 60)
    return f"{m}m {s % 60:.0f}s"


def run_step(step_num: int, script_name: str, description: str, dry_run: bool) -> bool:
    print(f"\n{'='*60}")
    print(f"  Step {step_num}: {script_name}")
    print(f"  {description}")
    print(f"{'='*60}")

    if dry_run:
        print("  [DRY RUN] Would execute: python", SCRIPTS_DIR / script_name)
        return True

    t0 = time.time()
    result = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / script_name)],
        cwd=str(ROOT_DIR),
    )
    elapsed = time.time() - t0

    if result.returncode != 0:
        print(f"\n  [FAILED] Step {step_num} FAILED (exit code {result.returncode}) after {fmt_seconds(elapsed)}")
        return False

    print(f"\n  [DONE] Step {step_num} completed in {fmt_seconds(elapsed)}")
    return True


def main():
    parser = argparse.ArgumentParser(description="ARG network pipeline runner")
    parser.add_argument("--from", dest="from_step", type=int, default=1,
                        help="Start from step N (default: 1)")
    parser.add_argument("--to",   dest="to_step",   type=int, default=6,
                        help="Stop after step N (default: 6)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print steps without executing")
    args = parser.parse_args()

    steps_to_run = [
        (n, s, d) for n, s, d in STEPS
        if args.from_step <= n <= args.to_step
    ]

    if not steps_to_run:
        print("No steps selected. Check --from / --to arguments.")
        sys.exit(1)

    print(f"\n{'#'*60}")
    print(f"  ARG Co-occurrence Network Pipeline")
    print(f"  Running steps {args.from_step} -> {args.to_step}")
    if args.dry_run:
        print("  MODE: DRY RUN")
    print(f"{'#'*60}")

    t_pipeline = time.time()
    failed_at = None

    for step_num, script, desc in steps_to_run:
        ok = run_step(step_num, script, desc, dry_run=args.dry_run)
        if not ok:
            failed_at = step_num
            break

    total = time.time() - t_pipeline
    print(f"\n{'#'*60}")
    if failed_at:
        print(f"  Pipeline stopped at step {failed_at}. Total time: {fmt_seconds(total)}")
        sys.exit(1)
    else:
        print(f"  [DONE] All steps completed. Total time: {fmt_seconds(total)}")
        print(f"  Outputs in: {ROOT_DIR / 'outputs'}")
    print(f"{'#'*60}\n")


if __name__ == "__main__":
    main()
