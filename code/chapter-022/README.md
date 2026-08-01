# Chapter 022 — FAISS

FAISS-backed indexes (Flat IP/L2, IVF, HNSW), IDMap + metadata sidecar, persistence, optimization sweeps, and a **PDF search** mini project.

## Dependencies

```bash
pip install numpy faiss-cpu pytest
```

## Run

```bash
cd code/chapter-022
pytest -q
python3 main.py search "money back refund" --kind flat_ip
python3 main.py compare
python3 main.py nprobe
python3 main.py persist --path /tmp/faisskit-index
python3 main.py fixtures --dir ./fixtures/pdfs
python3 main.py pdf-search "How do I get a refund?"
```

## Index kinds

| Kind | Notes |
|------|--------|
| `flat_ip` | Exact inner product (cosine if vectors unit-normalized) |
| `flat_l2` | Exact L2 |
| `ivf_flat` | Approximate; tune `nprobe` |
| `hnsw` | Graph ANN; tune `efSearch` |

## Layout

| Module | Role |
|--------|------|
| `service.py` | FaissIndexService |
| `indexes.py` | Factory + train/nprobe |
| `store.py` | String ids + metadata |
| `persist.py` | `index.faiss` + `meta.json` |
| `optimize.py` | Compare kinds / nprobe sweep |
| `pdf_io.py` | Minimal PDF write/extract |
| `pdf_search.py` | PDF → chunks → FAISS |
