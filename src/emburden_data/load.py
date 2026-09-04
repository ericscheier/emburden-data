"""
Dataset loaders for the emburden-data package.

Design:
  * Every dataset is defined once in DATASETS
  * Files are resolved via three-tier fallback:
      1. Local dev path (if user is on Eric's box)
      2. Local cache (platformdirs user cache dir)
      3. Download from URL (Zenodo / GitHub Releases)
  * Parquet is native pyarrow; RDS is unsupported (use emburden[r] for
    RDS access); CSV/JSON/GeoJSON all handled
  * Every loader returns pandas.DataFrame; the ``geo`` extra unlocks
    GeoDataFrame returns for spatial datasets
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pandas as pd
from platformdirs import user_cache_dir

# ─── Dataset registry ─────────────────────────────────────────────────
#
# Each entry:
#   filename:  cache filename (final on disk)
#   url:       remote URL (or None if only local)
#   format:    parquet | csv | rds | json | geojson
#   local:     path relative to the user's Documents/apps/emburdensynth/
#              (used when developing on Eric's laptop; ignored otherwise)
#   description: short user-facing description

DATASETS: dict[str, dict[str, Any]] = {
    "canonical_burden": {
        "filename": "summary_enriched.rds",
        "url": None,  # RDS not supported natively; requires emburden[r]
        "format": "rds",
        "local": "docs/global_analysis_data/summary_enriched.rds",
        "description": "Country-level burden via 4-tier fallback chain, 215 countries",
    },
    "cell_grid": {
        "filename": "cell_grid_wide.rds",
        "url": None,
        "format": "rds",
        "local": "docs/global_analysis_data/cell_grid_wide.rds",
        "description": "17,028 1° cells across 129 countries with burden + physics + suppression",
    },
    "climate_justice_headline": {
        "filename": "climate_justice_headline_v2.rds",
        "url": None,
        "format": "rds",
        "local": "docs/global_analysis_data/climate_justice_headline_v2.rds",
        "description": "Computed 67× per-capita CO2 mismatch + country lists (framing A + B)",
    },
    "owid_energy": {
        "filename": "owid_energy_data.csv",
        "url": "https://raw.githubusercontent.com/owid/energy-data/master/owid-energy-data.csv",
        "format": "csv",
        "local": None,
        "description": "OWID Energy — 220 countries × 1900-2025 × 130 vars (mirror)",
    },
    "owid_co2": {
        "filename": "owid_co2_data.csv",
        "url": "https://raw.githubusercontent.com/owid/co2-data/master/owid-co2-data.csv",
        "format": "csv",
        "local": None,
        "description": "OWID CO2 — 218 countries × 1750-2024 × per-capita + cumulative + by-fuel",
    },
    "global_synthetic_cells": {
        "filename": "global_synthetic_population_cells.parquet",
        "url": None,  # planned Zenodo release
        "format": "parquet",
        "local": "output/global/release/global_synthetic_population_cells.parquet",
        "description": "Flagship parquet — 17,028 cells × 50+ fields (129 countries, 8.2bn people)",
    },
}


def _emburdensynth_root() -> Path | None:
    """Best-effort locator of the R repo — for dev use on Eric's box."""
    for candidate in (
        Path.home() / "Documents" / "apps" / "emburdensynth",
        Path(os.environ.get("EMBURDENSYNTH_ROOT", "")),
    ):
        if candidate and candidate.is_dir():
            return candidate
    return None


def cache_dir() -> Path:
    """Return the on-disk cache directory (platformdirs user cache)."""
    d = Path(user_cache_dir("emburden-data", "emburden"))
    d.mkdir(parents=True, exist_ok=True)
    return d


def _resolve_path(key: str) -> Path:
    """Return a local file for a dataset key, downloading if necessary."""
    if key not in DATASETS:
        raise KeyError(f"Unknown dataset {key!r}. See list_datasets().")
    spec = DATASETS[key]

    # Tier 1: dev-mode local
    root = _emburdensynth_root()
    if root is not None and spec["local"]:
        p = root / spec["local"]
        if p.exists():
            return p

    # Tier 2: cache
    cache = cache_dir() / spec["filename"]
    if cache.exists():
        return cache

    # Tier 3: download
    url = spec["url"]
    if url is None:
        raise FileNotFoundError(
            f"Dataset {key!r} is not downloadable (format {spec['format']}). "
            "It lives only in the R repo (docs/global_analysis_data/). "
            "For access, either (a) clone the R repo + set EMBURDENSYNTH_ROOT, "
            "or (b) install emburden with the R extras (`pip install emburden[r]`)."
        )
    _download(url, cache)
    return cache


def _download(url: str, dest: Path) -> None:
    """Stream-download a URL to a destination path."""
    import requests
    with requests.get(url, stream=True, timeout=300) as r:
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 15):
                if chunk:
                    f.write(chunk)


def _read(path: Path, fmt: str) -> pd.DataFrame:
    """Read a file into a DataFrame."""
    if fmt == "parquet":
        return pd.read_parquet(path)
    if fmt == "csv":
        return pd.read_csv(path, low_memory=False)
    if fmt == "json":
        return pd.read_json(path)
    if fmt == "geojson":
        try:
            import geopandas as gpd
            return gpd.read_file(path)  # type: ignore[return-value]
        except ImportError as e:  # pragma: no cover
            raise ImportError(
                "GeoJSON loading requires geopandas. Install with `pip install emburden-data[geo]`."
            ) from e
    if fmt == "rds":
        raise NotImplementedError(
            "RDS files are R-native and can't be read from pure Python. "
            "Install the R extras: `pip install emburden[r]` and use "
            "`emburden.pipeline.*` functions, or export the dataset to Parquet first."
        )
    raise ValueError(f"Unknown format {fmt!r}")


# ─── Public API ───────────────────────────────────────────────────────

def list_datasets() -> pd.DataFrame:
    """Table of all available datasets with description + format."""
    rows = []
    for key, spec in DATASETS.items():
        rows.append({
            "key": key,
            "filename": spec["filename"],
            "format": spec["format"],
            "downloadable": spec["url"] is not None,
            "description": spec["description"],
        })
    return pd.DataFrame(rows)


def dataset_info(key: str) -> dict:
    """Return metadata for one dataset."""
    if key not in DATASETS:
        raise KeyError(f"Unknown dataset {key!r}")
    return dict(DATASETS[key], key=key)


def load_canonical_burden() -> pd.DataFrame:
    """
    215-country canonical burden (via 4-tier fallback chain).

    Note: this dataset lives as RDS in the R repo. Requires either the
    dev-mode R-repo path or the emburden[r] extras. See dataset_info().
    """
    path = _resolve_path("canonical_burden")
    return _read(path, DATASETS["canonical_burden"]["format"])


def load_cell_grid() -> pd.DataFrame:
    """
    17,028 1° cells × 129 countries × burden + physics + suppression.

    Note: RDS-only in this release. Zenodo Parquet mirror on the roadmap.
    """
    path = _resolve_path("cell_grid")
    return _read(path, DATASETS["cell_grid"]["format"])


def load_climate_justice_headline() -> dict:
    """
    Return the computed 67× per-capita CO2 mismatch summary.

    Structure (dict):
      * ``ratio_a``: 5× disparity (top-30 burden vs top-30 per-cap emitters)
      * ``ratio_b``: 67× disparity (20 lowest-access vs 20 largest emitters)
      * ``low_acc``: DataFrame of the 20 lowest-electricity-access countries
      * ``top20_emit``: DataFrame of the 20 largest historical emitters
      * ``top30_burden``, ``top30_co2pc``: subsidiary framings
      * ``world_cum_co2_mt``, ``world_pop``: denominators
    """
    path = _resolve_path("climate_justice_headline")
    return _read(path, DATASETS["climate_justice_headline"]["format"])


def load_owid_energy() -> pd.DataFrame:
    """OWID Energy dataset — 220 countries × 1900-2025 × 130 variables."""
    path = _resolve_path("owid_energy")
    return _read(path, DATASETS["owid_energy"]["format"])


def load_owid_co2() -> pd.DataFrame:
    """OWID CO2 dataset — 218 countries × 1750-2024 × per-capita + cumulative + by-fuel."""
    path = _resolve_path("owid_co2")
    return _read(path, DATASETS["owid_co2"]["format"])
