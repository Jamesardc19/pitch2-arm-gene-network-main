"""
05_centrality_analysis.py
Computes degree centrality, betweenness centrality, and clustering coefficient
for each node per zone network, then reports the top hub ARGs.
"""

import networkx as nx
import pandas as pd
import os

NETWORKS_DIR = "outputs/networks/"
ZONES = ["tropical", "arid", "temperate"]
TOP_N = 10

os.makedirs(NETWORKS_DIR, exist_ok=True)


def compute_centrality(G: nx.Graph) -> pd.DataFrame:
    degree      = nx.degree_centrality(G)
    betweenness = nx.betweenness_centrality(G, weight="weight", normalized=True)
    clustering  = nx.clustering(G, weight="weight")

    return pd.DataFrame({
        "node": list(degree.keys()),
        "degree_centrality":      list(degree.values()),
        "betweenness_centrality": [betweenness[n] for n in degree.keys()],
        "clustering_coefficient": [clustering[n] for n in degree.keys()],
    }).sort_values("betweenness_centrality", ascending=False)


if __name__ == "__main__":
    all_top_hubs = []

    for zone in ZONES:
        gexf_path = os.path.join(NETWORKS_DIR, f"network_{zone}.gexf")
        if not os.path.exists(gexf_path):
            print(f"[!] Skipping {zone} — GEXF not found. Run 03_build_network.py first.")
            continue

        print(f"\nCentrality analysis: {zone.upper()}")
        G = nx.read_gexf(gexf_path)

        if G.number_of_edges() == 0:
            print(f"  [!] No edges — skipping.")
            continue

        df_centrality = compute_centrality(G)
        out_path = os.path.join(NETWORKS_DIR, f"centrality_{zone}.csv")
        df_centrality.to_csv(out_path, index=False)
        print(f"  Saved: {out_path}")

        top = df_centrality.head(TOP_N).copy()
        top["zone"] = zone
        all_top_hubs.append(top)

        print(f"  Top {TOP_N} hub ARGs by betweenness:")
        print(top[["node", "betweenness_centrality", "degree_centrality"]].to_string(index=False))

    if all_top_hubs:
        hub_df = pd.concat(all_top_hubs, ignore_index=True)
        hub_path = os.path.join(NETWORKS_DIR, "top_hubs_summary.csv")
        hub_df.to_csv(hub_path, index=False)
        print(f"\nTop hubs summary saved to: {hub_path}")
