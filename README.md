# Pitch 2 — ARG Co-occurrence Network Under Climate Gradients

**Research Question:** Do ARGs that co-occur in environmental samples form different network communities depending on climate zone?

## Team
- James Angelo R. Dela Cruz (NetSci Lead)
- Angeleen Claire M. Lominoque (Data / Genomics)
- Hazelle N. Millarpis (Writing / Genomics)

## Pipeline Phases
1. Dataset sourcing (Figshare, Zenodo, NCBI supplementary)
2. Preprocessing and Koppen-Geiger zone labeling
3. Co-occurrence matrix construction (Spearman correlation)
4. Network construction (weighted ARG co-occurrence graph)
5. Community detection (Louvain, Girvan-Newman)
6. Centrality analysis (degree, betweenness, modularity)
7. Visualization (NetworkX / Gephi)

## Folder Structure
```
pitch2-amr-gene-network-main/
├── data/
│   ├── raw/           ← original downloaded datasets (not committed to git)
│   └── processed/     ← cleaned, labeled tables
├── docs/              ← reports and LaTeX source
├── outputs/
│   ├── figures/       ← plots and charts
│   └── networks/      ← .gexf files for Gephi
├── scripts/           ← numbered pipeline scripts
├── .gitignore
├── README.md
└── requirements.txt
```

## Data Sources
- https://figshare.com
- https://zenodo.org
- https://www.ncbi.nlm.nih.gov/sra
- https://www.climond.org (Koppen-Geiger raster by Beck 2018)

## Setup
```bash
pip install -r requirements.txt
```

Run scripts in order:
```bash
python scripts/01_load_data.py
python scripts/02_preprocess.py
python scripts/03_build_network.py
python scripts/04_community_detection.py
python scripts/05_centrality_analysis.py
python scripts/06_visualize.py
```
