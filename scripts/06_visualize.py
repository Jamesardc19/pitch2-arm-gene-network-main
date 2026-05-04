"""
06_visualize.py
---------------
Generate publication-ready network visualizations using NetworkX + Matplotlib.
Nodes are:
  - Colored by Louvain community
  - Sized by betweenness centrality
  - Laid out with spring layout (Fruchterman-Reingold, approximates ForceAtlas2)

Output:
    outputs/figures/network_<zone>.png   ← one figure per climate zone
    outputs/figures/centrality_barplot_<zone>.png
"""

import networkx as nx
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # non-interactive backend for script use
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import os

try:
    import community as community_louvain
except ImportError:
    raise ImportError("Run: pip install python-louvain")

# ── Configuration ────────────────────────────────────────────────────────────
NETWORKS_DIR = "outputs/networks/"
FIGURES_DIR = "outputs/figures/"
ZONES = ["tropical", "arid", "temperate"]

ZONE_PALETTE = {
    "tropical":  "#2ecc71",
    "arid":      "#e67e22",
    "temperate": "#3498db",
}

os.makedirs(FIGURES_DIR, exist_ok=True)


def draw_network(G: nx.Graph, zone: str, centrality_df: pd.DataFrame) -> None:
    """Draw the network with community colors and betweenness-based node sizes."""
    if G.number_of_edges() == 0:
        print(f"  [!] No edges to draw for {zone}.")
        return

    # Community partition for coloring
    partition = community_louvain.best_partition(G, weight="weight")
    communities = sorted(set(partition.values()))
    cmap = cm.get_cmap("tab20", len(communities))
    node_colors = [cmap(partition[n]) for n in G.nodes()]

    # Node sizes from betweenness
    betw_map = dict(zip(centrality_df["node"], centrality_df["betweenness_centrality"]))
    max_betw = max(betw_map.values()) if betw_map else 1.0
    node_sizes = [
        300 + 2000 * (betw_map.get(n, 0) / (max_betw + 1e-9))
        for n in G.nodes()
    ]

    # Layout
    pos = nx.spring_layout(G, weight="weight", seed=42)

    # Edge widths from weight
    edges = G.edges(data=True)
    edge_weights = [d.get("weight", 0.3) for _, _, d in edges]
    max_w = max(edge_weights) if edge_weights else 1.0
    edge_widths = [0.5 + 2.5 * (w / max_w) for w in edge_weights]

    fig, ax = plt.subplots(figsize=(14, 10))
    ax.set_facecolor("#1a1a2e")
    fig.patch.set_facecolor("#1a1a2e")

    nx.draw_networkx_edges(
        G, pos, ax=ax, alpha=0.4,
        width=edge_widths, edge_color="#aaaaaa"
    )
    nx.draw_networkx_nodes(
        G, pos, ax=ax,
        node_color=node_colors, node_size=node_sizes, alpha=0.9
    )
    nx.draw_networkx_labels(
        G, pos, ax=ax,
        font_size=6, font_color="white"
    )

    ax.set_title(
        f"ARG Co-occurrence Network — {zone.capitalize()} Zone\n"
        f"Nodes: {G.number_of_nodes()} | Edges: {G.number_of_edges()} | "
        f"Communities: {len(communities)}",
        color="white", fontsize=13, pad=15
    )
    ax.axis("off")

    out_path = os.path.join(FIGURES_DIR, f"network_{zone}.png")
    plt.savefig(out_path, dpi=200, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()
    print(f"  Saved: {out_path}")


def draw_centrality_barplot(centrality_df: pd.DataFrame, zone: str, top_n: int = 15) -> None:
    """Bar chart of top N nodes by betweenness centrality."""
    top = centrality_df.head(top_n)
    color = ZONE_PALETTE.get(zone, "#888888")

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.barh(top["node"][::-1], top["betweenness_centrality"][::-1], color=color)
    ax.set_xlabel("Betweenness Centrality")
    ax.set_title(f"Top {top_n} Hub ARGs — {zone.capitalize()} Zone")
    ax.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()

    out_path = os.path.join(FIGURES_DIR, f"centrality_barplot_{zone}.png")
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {out_path}")


if __name__ == "__main__":
    for zone in ZONES:
        gexf_path = os.path.join(NETWORKS_DIR, f"network_{zone}.gexf")
        centrality_path = os.path.join(NETWORKS_DIR, f"centrality_{zone}.csv")

        if not os.path.exists(gexf_path):
            print(f"[!] Skipping {zone} — GEXF not found. Run 03_build_network.py first.")
            continue
        if not os.path.exists(centrality_path):
            print(f"[!] Skipping {zone} — centrality CSV not found. Run 05_centrality_analysis.py first.")
            continue

        print(f"\nVisualizing: {zone.upper()}")
        G = nx.read_gexf(gexf_path)
        centrality_df = pd.read_csv(centrality_path)

        draw_network(G, zone, centrality_df)
        draw_centrality_barplot(centrality_df, zone)

    print("\nAll figures saved to outputs/figures/")
