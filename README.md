# emburden-data — pure-Python data access to the emburden global dataset

**pandas + pyarrow loaders for the emburden global household
energy-burden dataset. No R install required.**

[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](https://opensource.org/license/mit)
[![Python: 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://pypi.org/project/emburden-data/)
[![emburden.org](https://img.shields.io/badge/site-emburden.org-228b22.svg)](https://emburden.org)

---

## What this is

The [emburden R ecosystem](https://github.com/ericscheier) produces
a suite of open datasets: a canonical burden panel for 215 countries,
a 17,028-cell global microdata grid, a climate-justice mismatch
computation, harmonized mirrors of OWID Energy + OWID CO₂, and more.

This Python package gives you `pandas.DataFrame` access to those
datasets **without needing R installed**. Files are downloaded
on-demand from Zenodo / GitHub Releases and cached locally.

For the full R computational pipeline, see
[emburden](https://github.com/ericscheier/emburden) and
[emburdensynth](https://github.com/ericscheier/emburdensynth). For
the Python meta-package that bridges to R, see
[emburden](https://pypi.org/project/emburden/).

## Install

```bash
pip install emburden-data

# For spatial datasets (GeoJSON):
pip install "emburden-data[geo]"
```

## Quickstart

```python
import emburden_data as ed

# What's available?
print(ed.list_datasets())

# The 67× climate-justice mismatch computation:
hdr = ed.load_climate_justice_headline()
print(f"67× disparity ratio: {hdr['ratio_b']}")
print(f"20 least-electrified countries: {hdr['low_acc']['iso3'].tolist()}")

# OWID Energy — 1900-2025 per-country per-year:
energy = ed.load_owid_energy()
print(energy.query("iso_code == 'USA'").tail())

# OWID CO2 — 1750-2024 with per-capita + cumulative + by-fuel:
co2 = ed.load_owid_co2()
print(co2.filter(regex="cumulative|iso").head())

# Country-level canonical burden (currently RDS; needs emburden[r]):
burden = ed.load_canonical_burden()   # 215 countries
```

## Available datasets

| Key | Format | Rows | Description |
|---|---|---|---|
| `canonical_burden` | RDS | 249 | 215-country burden via 4-tier fallback chain |
| `cell_grid` | RDS | 17,028 | 1° cells × 129 countries × burden + physics + suppression |
| `climate_justice_headline` | RDS | — | The 67× mismatch computation + country lists |
| `global_synthetic_cells` | Parquet | ~17k | Flagship 50+-field microdata parquet (planned Zenodo release) |
| `owid_energy` | CSV | ~17k | OWID Energy — 220 countries × 1900-2025 × 130 vars |
| `owid_co2` | CSV | ~42k | OWID CO2 — 218 countries × 1750-2024 |

## Design principles

- **pandas-native**: every function returns a `pandas.DataFrame` (or a
  `GeoDataFrame` with the `geo` extra, or a Python dict for the
  climate-justice computation).
- **On-demand caching**: data lives in the user cache directory
  (`platformdirs.user_cache_dir("emburden-data")`), downloaded once,
  reused thereafter.
- **Three-tier resolution**: (1) dev-mode R-repo path, (2) local
  cache, (3) remote download.
- **Graceful degradation**: RDS-only datasets raise a clear error
  pointing you at either the R extras or the R repo, rather than
  crashing.

## Relationship to the R ecosystem

- **Canonical implementation**: R, at
  [github.com/ericscheier](https://github.com/ericscheier)
- **Data snapshots**: this package (`pip install emburden-data`) —
  read-only access to the outputs
- **Bridge for running the pipeline from Python**:
  [`emburden`](https://pypi.org/project/emburden/) via `rpy2`

## Development

```bash
git clone https://github.com/ericscheier/emburden-data
cd emburden-data
pip install -e ".[dev]"
pytest
```

## License

MIT © [Eric Scheier](mailto:hello@emrgi.com) / Emrgi
