# Chapter 021 — Vector Databases

Mini in-process vector DB: collections, flat + IVF indexes, metadata filters, JSON persistence, index comparison.

## Run

```bash
cd code/chapter-021
pip install pytest
pytest -q
python3 main.py demo
python3 main.py query "money back" --where '{"topic":"billing"}'
python3 main.py compare
python3 main.py persist --path /tmp/vdb.json
python3 main.py stats --db /tmp/vdb.json
```

## Index types

| Type | Behavior |
|------|----------|
| `flat` | Exact scan — full recall |
| `ivf` | Coarse clusters + `nprobe` lists — fewer scans, approximate |

## Layout

| Module | Role |
|--------|------|
| `database.py` | Multi-collection VectorDB |
| `collection.py` | Upsert / query / stats |
| `index_flat.py` | Exact search |
| `index_ivf.py` | Teaching IVF |
| `filter.py` | Metadata `$and/$or/$in/$gte`… |
| `persist.py` | Save/load JSON |
| `compare.py` | Flat vs IVF report |
