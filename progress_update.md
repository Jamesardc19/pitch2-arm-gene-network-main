# ARG Co-occurrence Network — Team Progress Update
**Date:** May 5, 2026  
**Prepared by:** James Angelo R. Dela Cruz (Technical Lead)  
**For:** Angeleen Claire M. Lominoque, Hazelle N. Millarpis

---

## Current Phase

> [!IMPORTANT]
> We have **completed Phases 1 through 5** of the project timetable. As of today, the full analytical pipeline has been executed end-to-end and all primary outputs (networks, community partitions, centrality metrics, and figures) are ready.

The status report submitted last time placed us at **Phase 2** (Dataset Sourcing and Preparation). We are now **fully through Phase 5 (Synthesis and Final Output)** on the technical side:

| Phase | Description | Status |
|---|---|---|
| Phase 1 | Project initiation, pitch, proposal | Done |
| Phase 2 | Dataset sourcing, Koppen-Geiger zone assignment | Done |
| Phase 3 | Network construction, topology metrics | Done |
| Phase 4 | Community detection, centrality analysis | Done |
| Phase 5 | Network visualization, cross-zone comparison | **Done** |

---

## What Was Accomplished (Technical Summary)

### Dataset

- **Source used:** Martiny et al. mARG dataset (Zenodo 6919377)
  - `ARG.tsv` — 4.2 million rows, one row per sample-ARG pair (~445 MB)
  - `metadata.tsv` — 214,022 rows with geographic coordinates and continent labels
- **Normalisation:** RPKM (Reads Per Kilobase per Million mapped reads) to account for gene length and sequencing depth.

### Step 1 — Data Loading (`01_load_data.py`)

- Parsed coordinates (`lat`, `lon`) from the metadata `location` field (e.g., "18.05 S 47.03 E").
- Pivoted the long-format ARG table to a wide format: **rows = samples, columns = ARGs**.
- Merged with metadata on `run_accession`.
- **Result:** 119,232 samples × 2,999 ARGs saved to `data/processed/arg_wide_with_meta.csv` (1.5 GB).

### Step 2 — Climate Zone Assignment & Filtering (`02_preprocess.py`)

- Used the **Beck et al. (2023) Koppen-Geiger 0.1° raster** (Figshare dataset 21789074) to assign each sample a climate zone based on exact GPS coordinates — more accurate than continent-level approximation.
- Mapped Koppen-Geiger numeric codes to three major zones:
  - Codes 1–3 → **Tropical**
  - Codes 4–7 → **Arid**
  - Codes 8–28 → **Temperate** (C and D classes merged)
  - Codes 29–30 (Polar) → Excluded
- Applied a **5% presence filter**: kept only ARGs found in ≥5% of samples (removes near-absent ARGs that can't form meaningful co-occurrence edges).

**Zone distribution after assignment:**

| Climate Zone | Samples |
|---|---|
| Tropical | 4,443 |
| Arid | 3,020 |
| Temperate | 44,601 |
| **Total retained** | **52,064** |

**ARGs retained after 5% filter: 156** (from 2,999 original ARGs)

> [!NOTE]
> Temperate is heavily overrepresented because the mARG dataset draws heavily from North American and European studies. Arid and tropical sample sizes (3,020 and 4,443) are both well above the minimum threshold of 20, so all three zones are viable for analysis.

### Step 3 — Co-occurrence Network Construction (`03_build_network.py`)

- For each climate zone, computed **pairwise Spearman correlations** between all 156 ARG pairs.
- Kept only edges where **r ≥ 0.3 AND p < 0.05** (significant positive co-occurrence only).
- Built a weighted, undirected `NetworkX` graph per zone.
- Exported as `.gexf` files (openable in Gephi for interactive exploration).

**Network topology summary:**

| Zone | Nodes | Edges | Density | Avg. Clustering |
|---|---|---|---|---|
| Tropical | 155 | 1,730 | 0.145 | 0.315 |
| Arid | 155 | 2,292 | 0.192 | 0.326 |
| Temperate | 155 | 1,960 | 0.164 | 0.323 |

All three networks are well-connected (non-trivial density). Arid has the highest density, suggesting the most integrated co-occurrence structure.

### Step 4 — Community Detection (`04_community_detection.py`)

Two algorithms were applied for comparison:

| Zone | Louvain Communities | Louvain Modularity (Q) | Girvan-Newman Communities |
|---|---|---|---|
| Tropical | 27 | **0.4135** | 25 |
| Arid | 20 | 0.2601 | 16 |
| Temperate | 24 | **0.3083** | 19 |

> [!NOTE]
> **Modularity Q > 0.3 is considered meaningful community structure.** Tropical (Q = 0.41) and Temperate (Q = 0.31) show clear modular ARG communities. Arid (Q = 0.26) is below this threshold — this is itself an interesting finding suggesting that arid-zone ARGs form a more integrated, less compartmentalised co-occurrence network. This should be discussed in context of the environmental pressure hypothesis.

### Step 5 — Centrality Analysis (`05_centrality_analysis.py`)

Computed three metrics per node per zone: degree centrality, betweenness centrality, and clustering coefficient. Hub ARGs (highest betweenness) are the most structurally important nodes — they act as bridges between communities.

**Top 5 hub ARGs by betweenness centrality:**

**Tropical zone:**
| ARG | Betweenness | Degree Centrality |
|---|---|---|
| tet(M)_13_AM990992 | 0.060 | 0.299 |
| tet(Q)_4_Z21523 | 0.045 | 0.325 |
| tet(M)_12_FR671418 | 0.044 | 0.247 |
| erm(B)_10_U86375 | 0.039 | 0.143 |
| tet(O)_3_Y07780 | 0.030 | 0.344 |

**Arid zone:**
| ARG | Betweenness | Degree Centrality |
|---|---|---|
| aadA2_1_NC_010870 | 0.081 | 0.182 |
| lsa(E)_1_JX560992 | 0.063 | 0.240 |
| tet(M)_13_AM990992 | 0.061 | 0.331 |
| lnu(A)_1_M14039 | 0.056 | 0.032 |
| aph(3'')-Ib_5_AF321551 | 0.040 | 0.182 |

**Temperate zone:**
| ARG | Betweenness | Degree Centrality |
|---|---|---|
| lnu(B)_2_JQ861959 | 0.094 | 0.273 |
| aph(6)-Id_1_M28829 | 0.079 | 0.149 |
| aph(3')-Ia_7_X62115 | 0.054 | 0.071 |
| mef(A)_2_U83667 | 0.050 | 0.214 |
| lsa(E)_1_JX560992 | 0.048 | 0.305 |

> [!TIP]
> `tet(M)` (tetracycline resistance) appears as a hub in both tropical and arid zones — this cross-zone recurrence is worth highlighting in the Discussion. `lsa(E)` appears as a hub in both arid and temperate zones.

### Step 6 — Cross-zone Statistical Comparison & Visualisation (`06_visualize.py`)

- Generated network figures for all three zones (white background, nodes coloured by Louvain community, sized by betweenness, with labels on top-12 hubs only).
- Generated centrality bar charts (top-15 hub ARGs per zone).
- **Kruskal-Wallis test** (non-parametric, compares betweenness distributions across zones):
  - H = 3.219, p = 0.200 — **not statistically significant**
  - Interpretation: The three zones do not have significantly different overall centrality distributions. However, the qualitative differences in **which ARGs** serve as hubs, and in **modularity**, are still biologically meaningful and should be discussed.

---

## Output Files Ready

All outputs are in the `outputs/` folder:

```
outputs/
  figures/
    network_tropical.png        <- network graph, Tropical zone
    network_arid.png            <- network graph, Arid zone
    network_temperate.png       <- network graph, Temperate zone
    centrality_barplot_*.png    <- hub ARG bar charts per zone
    centrality_by_zone.png      <- cross-zone boxplot + K-W test
  networks/
    network_tropical.gexf       <- open in Gephi for interactive view
    network_arid.gexf
    network_temperate.gexf
    communities_*.csv           <- node-level community assignments
    modularity_summary.csv      <- community counts & modularity per zone
    centrality_*.csv            <- full centrality table per zone
    top_hubs_summary.csv        <- top 10 hubs across all zones
    network_stats.csv           <- nodes, edges, density per zone
```

---

## What the Team Should Do Next

### James (Technical Lead)
- [x] Pipeline complete — all 6 scripts ran successfully
- [ ] Interpret hub ARG biology: look up what resistance mechanisms `tet(M)`, `lnu(B)`, `aadA2`, `lsa(E)` confer and why they might be structurally central
- [ ] Open `.gexf` files in **Gephi** for interactive visualisation (better for presentations)
- [ ] Consider running sensitivity analysis: re-run with r ≥ 0.2 or r ≥ 0.4 to check edge stability

### Angeleen (Data & Background)
- [ ] Draft the **Methods** section — you now have all the numbers:
  - Dataset: mARG (Zenodo 6919377), 119,232 samples
  - Koppen-Geiger raster (Beck et al. 2023, 0.1° resolution)
  - Spearman co-occurrence, r ≥ 0.3, p < 0.05
  - ARG presence filter: ≥5% of samples
- [ ] Draft the **Results** section using the tables above
- [ ] Note the zone sample imbalance (temperate >> arid/tropical) as a limitation

### Hazelle (Writing & RRL)
- [ ] Frame the Discussion around:
  1. Tropical has the most modular network (Q = 0.41) — what does that mean biologically?
  2. Arid has the highest edge density but lowest modularity — more integrated resistance gene network?
  3. The Kruskal-Wallis result (p = 0.20) — absence of significance is also a finding
  4. Recurrence of `tet(M)` and `lsa(E)` as hubs in multiple zones — mobile genetic elements?
- [ ] Update the Introduction/RRL to mention Martiny et al. mARG dataset as the primary source

---

## Key Numbers for the Paper

| Metric | Value |
|---|---|
| Dataset | Martiny et al. mARG (Zenodo 6919377) |
| Total samples processed | 119,232 |
| Samples assigned to climate zones | 52,064 |
| ARGs after 5% presence filter | 156 |
| Network nodes per zone | 155 |
| Edges: Tropical / Arid / Temperate | 1,730 / 2,292 / 1,960 |
| Modularity Q: Tropical / Arid / Temperate | 0.41 / 0.26 / 0.31 |
| Kruskal-Wallis (betweenness, cross-zone) | H = 3.22, p = 0.20 (ns) |
| Climate zone assignment method | Koppen-Geiger raster, Beck et al. 2023, 0.1° |
| Co-occurrence threshold | Spearman r >= 0.3, p < 0.05 |
