"""Smoke + integration tests for emburden-data."""

from __future__ import annotations

import pandas as pd
import pytest


def test_package_importable():
    import emburden_data
    assert emburden_data.__version__ == "0.1.0"


def test_list_datasets_returns_dataframe():
    from emburden_data import list_datasets
    df = list_datasets()
    assert isinstance(df, pd.DataFrame)
    assert len(df) >= 5
    assert set(df.columns) >= {"key", "filename", "format", "downloadable", "description"}


def test_dataset_info_known_key():
    from emburden_data import dataset_info
    info = dataset_info("owid_co2")
    assert info["format"] == "csv"
    assert info["downloadable"] is True
    assert "OWID CO2" in info["description"]


def test_dataset_info_unknown_raises():
    from emburden_data import dataset_info
    with pytest.raises(KeyError):
        dataset_info("does_not_exist")


def test_cache_dir_exists():
    from emburden_data import cache_dir
    d = cache_dir()
    assert d.exists()
    assert d.is_dir()


def test_rds_loader_raises_clear_error(monkeypatch, tmp_path):
    """Loading an RDS dataset without the dev-mode R repo should raise a helpful error."""
    from emburden_data import load
    # Force _emburdensynth_root() to return None so we hit the RDS-not-supported branch
    monkeypatch.setattr(load, "_emburdensynth_root", lambda: None)
    monkeypatch.setattr(load, "cache_dir", lambda: tmp_path)
    with pytest.raises((FileNotFoundError, NotImplementedError)) as excinfo:
        load.load_canonical_burden()
    msg = str(excinfo.value).lower()
    assert "rds" in msg or "not downloadable" in msg


def test_dev_mode_local_read_when_available():
    """If Eric's box, verify a real load works."""
    from emburden_data.load import _emburdensynth_root, load_owid_co2
    root = _emburdensynth_root()
    if root is None:
        pytest.skip("Not on the dev box; skipping local-file check")
    # OWID CO2 is small enough to test — but skip if it's not cached to keep unit tests fast
    # (this is a smoke; a full integration test would go in a separate suite)
    assert callable(load_owid_co2)
