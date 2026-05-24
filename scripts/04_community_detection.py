"""
04_community_detection.py
Runs Louvain and Girvan-Newman community detection on each per-zone network
and saves partition tables with modularity scores.

Requirements: pip install python-louvain
"""

import networkx as nx
import pandas as pd
import os

try:
    import community as community_louvain
except ImportError:
    raise ImportError("python-louvain not found. Install with: pip install python-louvain")

from networkx.algorithms.community import girvan_newman

NETWORKS_DIR = "outputs/networks/"
ZONES = ["tropical", "arid", "temperate"]

os.makedirs(NETWORKS_DIR, exist_ok=True)


def run_louvain(G: nx.Graph) -> tuple[dict, float]:
    partition = community_louvain.best_partition(G, weight="weight")
    mod = community_louvain.modularity(partition, G, weight="weight")
    return partition, mod


def run_girvan_newman(G: nx.Graph) -> frozenset:
    return next(girvan_newman(G))


def partition_to_df(partition: dict, gn_communities: frozenset, zone: str) -> pd.DataFrame:
    louvain_col = {node: comm for node, comm in partition.items()}
    gn_col = {}
    for i, community in enumerate(gn_communities):
        for node in community:
            gn_col[node] = i

    nodes = list(partition.keys())
    return pd.DataFrame({
        "node": nodes,
        "zone": zone,
        "louvain_community": [louvain_col.get(n, -1) for n in nodes],
        "gn_community": [gn_col.get(n, -1) for n in nodes],
    })


if __name__ == "__main__":
    modularity_records = []

    for zone in ZONES:
        gexf_path = os.path.join(NETWORKS_DIR, f"network_{zone}.gexf")
        if not os.path.exists(gexf_path):
            print(f"[!] Skipping {zone} — GEXF not found. Run 03_build_network.py first.")
            continue

        print(f"\nCommunity detection: {zone.upper()}")
        G = nx.read_gexf(gexf_path)

        if G.number_of_edges() == 0:
            print(f"  [!] No edges in {zone} network — skipping.")
            continue

        print("  Running Louvain...")
        partition, mod = run_louvain(G)
        n_communities = len(set(partition.values()))
        print(f"  Louvain: {n_communities} communities, modularity = {mod:.4f}")

        print("  Running Girvan-Newman (may take a moment on large graphs)...")
        gn_communities = run_girvan_newman(G)
        print(f"  Girvan-Newman: {len(gn_communities)} communities")

        df_communities = partition_to_df(partition, gn_communities, zone)
        out_path = os.path.join(NETWORKS_DIR, f"communities_{zone}.csv")
        df_communities.to_csv(out_path, index=False)
        print(f"  Saved: {out_path}")

        modularity_records.append({
            "zone": zone,
            "louvain_communities": n_communities,
            "louvain_modularity": round(mod, 4),
            "gn_communities": len(gn_communities),
        })

    mod_df = pd.DataFrame(modularity_records)
    mod_path = os.path.join(NETWORKS_DIR, "modularity_summary.csv")
    mod_df.to_csv(mod_path, index=False)
    print(f"\nModularity summary saved to: {mod_path}")
    print(mod_df.to_string(index=False))
