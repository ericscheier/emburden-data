"""
emburden-data — pure-Python access to the emburden global dataset.

No R install required. Datasets are downloaded on-demand from Zenodo /
GitHub Releases and cached locally via platformdirs. Every loader
returns a pandas DataFrame; geo-datasets optionally return GeoDataFrames
if geopandas is installed.

Quick start:

    import emburden_data as ed
    print(ed.list_datasets())            # what's available
    df = ed.load_canonical_burden()      # 215 country burdens
    grid = ed.load_cell_grid()           # 17,028 cells × 129 countries
    hdr = ed.load_climate_justice_headline()  # 67× mismatch computation
"""

from __future__ import annotations

__version__ = "0.1.0"
__author__ = "Eric Scheier"
__email__ = "hello@emrgi.com"
__license__ = "MIT"

from emburden_data.load import (
    list_datasets,
    load_canonical_burden,
    load_cell_grid,
    load_climate_justice_headline,
    load_owid_energy,
    load_owid_co2,
    dataset_info,
    cache_dir,
)

__all__ = [
    "__version__",
    "list_datasets",
    "load_canonical_burden",
    "load_cell_grid",
    "load_climate_justice_headline",
    "load_owid_energy",
    "load_owid_co2",
    "dataset_info",
    "cache_dir",
]
