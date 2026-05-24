"""
03_build_network.py
Builds a weighted ARG co-occurrence network per climate zone from pairwise
Spearman correlations, then exports each as a .gexf file.
"""

import pandas as pd
import numpy as np
import networkx as nx
from scipy.stats import spearmanr
import os

PROCESSED_DIR        = "data/processed/"
NETWORKS_DIR         = "outputs/networks/"
CORRELATION_THRESHOLD = 0.3
P_VALUE_THRESHOLD     = 0.05
ZONES                 = ["tropical", "arid", "temperate"]

# Columns that are metadata, not ARG abundances
META_COLS = ["Latitude", "Longitude", "KG_code", "Climate_Zone", "SampleID"]

os.makedirs(NETWORKS_DIR, exist_ok=True)


def get_arg_columns(df: pd.DataFrame) -> list:
    return [c for c in df.columns if c not in META_COLS]


def build_cooccurrence_matrix(df_zone: pd.DataFrame) -> pd.DataFrame:
    arg_cols = get_arg_columns(df_zone)
    df_args  = df_zone[arg_cols]
    n = len(arg_cols)
    corr_matrix = pd.DataFrame(np.zeros((n, n)), index=arg_cols, columns=arg_cols)

    for i in range(n):
        for j in range(i + 1, n):
            r, p = spearmanr(df_args.iloc[:, i], df_args.iloc[:, j])
            if p < P_VALUE_THRESHOLD and r > 0:
                corr_matrix.iloc[i, j] = r
                corr_matrix.iloc[j, i] = r

    return corr_matrix


def build_network(corr_matrix: pd.DataFrame, threshold: float = CORRELATION_THRESHOLD) -> nx.Graph:
    G = nx.Graph()
    args = corr_matrix.index.tolist()
    G.add_nodes_from(args)

    for i in range(len(args)):
        for j in range(i + 1, len(args)):
            weight = corr_matrix.iloc[i, j]
            if weight >= threshold:
                G.add_edge(args[i], args[j], weight=float(weight))

    return G


def summarize_graph(G: nx.Graph, zone: str) -> dict:
    return {
        "zone": zone,
        "nodes": G.number_of_nodes(),
        "edges": G.number_of_edges(),
        "density": round(nx.density(G), 4),
        "avg_clustering": round(nx.average_clustering(G, weight="weight"), 4)
        if G.number_of_edges() > 0 else 0,
        "components": nx.number_connected_components(G),
    }


if __name__ == "__main__":
    stats = []

    for zone in ZONES:
        filepath = os.path.join(PROCESSED_DIR, f"args_{zone}.csv")
        if not os.path.exists(filepath):
            print(f"[!] Skipping {zone} — file not found: {filepath}")
            continue

        print(f"\nBuilding network for: {zone.upper()}")
        df = pd.read_csv(filepath, index_col=0)
        print(f"  Samples: {len(df)}, ARG columns: {len(get_arg_columns(df))}")

        print("  Computing Spearman co-occurrence matrix...")
        corr = build_cooccurrence_matrix(df)

        print("  Building graph...")
        G = build_network(corr)

        gexf_path = os.path.join(NETWORKS_DIR, f"network_{zone}.gexf")
        nx.write_gexf(G, gexf_path)
        print(f"  Saved: {gexf_path}")

        summary = summarize_graph(G, zone)
        stats.append(summary)
        print(f"  Stats: {summary}")

    stats_df = pd.DataFrame(stats)
    stats_path = os.path.join(NETWORKS_DIR, "network_stats.csv")
    stats_df.to_csv(stats_path, index=False)
    print(f"\nNetwork stats saved to: {stats_path}")
