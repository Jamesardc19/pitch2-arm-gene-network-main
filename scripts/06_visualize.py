"""
06_visualize.py
Generates network graphs (colored by community, sized by betweenness),
centrality bar charts, and a cross-zone Kruskal-Wallis boxplot.
"""

import networkx as nx
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
import os

try:
    import seaborn as sns
except ImportError:
    sns = None

from scipy.stats import kruskal

try:
    import community as community_louvain
except ImportError:
    raise ImportError("Run: pip install python-louvain")

NETWORKS_DIR = "outputs/networks/"
FIGURES_DIR  = "outputs/figures/"
ZONES = ["tropical", "arid", "temperate"]

ZONE_PALETTE = {
    "tropical":  "#2ecc71",
    "arid":      "#e67e22",
    "temperate": "#3498db",
}

os.makedirs(FIGURES_DIR, exist_ok=True)


def draw_network(G: nx.Graph, zone: str, centrality_df: pd.DataFrame) -> None:
    if G.number_of_edges() == 0:
        print(f"  [!] No edges to draw for {zone}.")
        return

    partition   = community_louvain.best_partition(G, weight="weight")
    communities = sorted(set(partition.values()))
    cmap        = cm.get_cmap("tab20", max(len(communities), 2))
    node_colors = [cmap(partition[n]) for n in G.nodes()]

    betw_map   = dict(zip(centrality_df["node"], centrality_df["betweenness_centrality"]))
    max_betw   = max(betw_map.values()) if betw_map else 1.0
    node_sizes = [200 + 1800 * (betw_map.get(n, 0) / (max_betw + 1e-9)) for n in G.nodes()]

    pos = nx.spring_layout(G, weight="weight", seed=42, k=0.4)

    edge_data    = list(G.edges(data=True))
    edge_weights = [d.get("weight", 0.3) for _, _, d in edge_data]
    max_w        = max(edge_weights) if edge_weights else 1.0
    edge_widths  = [0.3 + 1.5 * (w / max_w) for w in edge_weights]

    fig, ax = plt.subplots(figsize=(16, 11))
    ax.set_facecolor("white")
    fig.patch.set_facecolor("white")

    nx.draw_networkx_edges(G, pos, ax=ax, alpha=0.35, width=edge_widths, edge_color="#888888")
    nx.draw_networkx_nodes(G, pos, ax=ax, node_color=node_colors, node_size=node_sizes,
                           alpha=0.88, linewidths=0.5, edgecolors="#333333")

    # Label only the top-12 hubs to keep the figure readable
    TOP_LABEL_N = 12
    top_nodes   = set(centrality_df.head(TOP_LABEL_N)["node"].tolist())
    nx.draw_networkx_labels(G, pos, labels={n: n for n in G.nodes() if n in top_nodes},
                            ax=ax, font_size=7, font_color="#111111", font_weight="bold")

    zone_colour = ZONE_PALETTE.get(zone, "#333333")
    ax.set_title(
        f"ARG Co-occurrence Network  |  {zone.capitalize()} Climate Zone\n"
        f"Nodes: {G.number_of_nodes()}  |  Edges: {G.number_of_edges()}  |  "
        f"Louvain communities: {len(communities)}",
        fontsize=13, fontweight="bold", color=zone_colour, pad=18
    )
    ax.axis("off")

    comm_patches = [
        Patch(facecolor=cmap(c), edgecolor="#555555", label=f"Community {c + 1}")
        for c in communities[:12]
    ]
    if len(communities) > 12:
        comm_patches.append(Patch(facecolor="none", edgecolor="none",
                                  label=f"... +{len(communities) - 12} more"))
    legend1 = ax.legend(handles=comm_patches, title="Louvain Community", title_fontsize=8,
                        fontsize=7, loc="upper left", framealpha=0.85,
                        ncol=2 if len(communities) > 8 else 1, borderpad=0.8)
    ax.add_artist(legend1)

    size_legend = [
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#888888",
               markersize=sz ** 0.5, label=lbl, markeredgecolor="#333333")
        for sz, lbl in [(200, "Low centrality"), (1000, "Medium"), (2000, "High (hub)")]
    ]
    ax.legend(handles=size_legend, title="Node size = Betweenness centrality",
              title_fontsize=8, fontsize=7, loc="lower left", framealpha=0.85)

    fig.text(
        0.5, 0.01,
        f"Only top {TOP_LABEL_N} hub ARGs (by betweenness centrality) are labelled. "
        "Node size is proportional to betweenness centrality. "
        "Node colour indicates Louvain community membership. "
        "Edge width is proportional to Spearman r (r >= 0.3, p < 0.05).",
        ha="center", fontsize=7.5, color="#555555", style="italic"
    )

    out_path = os.path.join(FIGURES_DIR, f"network_{zone}.png")
    plt.savefig(out_path, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"  Saved: {out_path}")


def draw_centrality_barplot(centrality_df: pd.DataFrame, zone: str, top_n: int = 15) -> None:
    top   = centrality_df.head(top_n)
    color = ZONE_PALETTE.get(zone, "#888888")

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.barh(top["node"][::-1], top["betweenness_centrality"][::-1], color=color)
    ax.set_xlabel("Betweenness Centrality")
    ax.set_title(f"Top {top_n} Hub ARGs -- {zone.capitalize()} Zone")
    ax.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()

    out_path = os.path.join(FIGURES_DIR, f"centrality_barplot_{zone}.png")
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {out_path}")


def draw_cross_zone_comparison(centrality_dfs: dict) -> None:
    frames = []
    for zone, df in centrality_dfs.items():
        tmp = df[["betweenness_centrality"]].copy()
        tmp["zone"] = zone
        frames.append(tmp)
    all_df = pd.concat(frames, ignore_index=True)

    groups = [g["betweenness_centrality"].values for _, g in all_df.groupby("zone")]
    if len(groups) >= 2 and all(len(g) > 1 for g in groups):
        stat, p = kruskal(*groups)
        kw_label = f"Kruskal-Wallis: H = {stat:.3f}, p = {p:.4f}"
        sig = " (significant, p < 0.05)" if p < 0.05 else " (not significant)"
        print(f"\n  Cross-zone Kruskal-Wallis: H = {stat:.3f}, p = {p:.4f}{sig}")
    else:
        kw_label = "Kruskal-Wallis: insufficient data"
        print("  [!] Not enough zones/samples for Kruskal-Wallis test.")

    fig, ax = plt.subplots(figsize=(9, 5))
    zone_order = [z for z in ZONES if z in centrality_dfs]
    palette    = {z: ZONE_PALETTE.get(z, "#888888") for z in zone_order}

    if sns is not None:
        sns.boxplot(data=all_df, x="zone", y="betweenness_centrality",
                    order=zone_order, hue="zone", palette=palette, ax=ax, legend=False)
    else:
        data_ordered = [centrality_dfs[z]["betweenness_centrality"].values for z in zone_order]
        ax.boxplot(data_ordered, patch_artist=True)
        ax.set_xticks(range(1, len(zone_order) + 1))
        ax.set_xticklabels(zone_order)

    ax.set_title(f"Betweenness Centrality of ARGs by Climate Zone\n{kw_label}", fontsize=12)
    ax.set_xlabel("Climate Zone")
    ax.set_ylabel("Betweenness Centrality")
    ax.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()

    out_path = os.path.join(FIGURES_DIR, "centrality_by_zone.png")
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {out_path}")


if __name__ == "__main__":
    centrality_dfs = {}

    for zone in ZONES:
        gexf_path      = os.path.join(NETWORKS_DIR, f"network_{zone}.gexf")
        centrality_path = os.path.join(NETWORKS_DIR, f"centrality_{zone}.csv")

        if not os.path.exists(gexf_path):
            print(f"[!] Skipping {zone} -- GEXF not found. Run 03_build_network.py first.")
            continue
        if not os.path.exists(centrality_path):
            print(f"[!] Skipping {zone} -- centrality CSV not found. Run 05_centrality_analysis.py first.")
            continue

        print(f"\nVisualizing: {zone.upper()}")
        G = nx.read_gexf(gexf_path)
        centrality_df = pd.read_csv(centrality_path)

        draw_network(G, zone, centrality_df)
        draw_centrality_barplot(centrality_df, zone)
        centrality_dfs[zone] = centrality_df

    if len(centrality_dfs) >= 2:
        print("\nGenerating cross-zone comparison...")
        draw_cross_zone_comparison(centrality_dfs)

    print("\nAll figures saved to outputs/figures/")
